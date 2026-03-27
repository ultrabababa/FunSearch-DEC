# Stage 1 Case 优化实验指南

## 1. 环境准备

### 1.1 启动本地 LM Studio

确保 LM Studio 已启动并加载模型：

- 地址：`127.0.0.1:1234`
- 模型：`qwen3-coder-30b-a3b-instruct`

验证模型是否可用：

```bash
curl -s http://127.0.0.1:1234/v1/models | head -5
```

预期输出：

```json
{
  "data": [
    {
      "id": "qwen3-coder-30b-a3b-instruct",
      "object": "model",
```

### 1.2 激活虚拟环境

```bash
source .venv/bin/activate
```

### 1.3 安装依赖

```bash
pip install absl-py scipy numba tensorboard torch openai
```

### 1.3 进入项目目录

```bash
cd /mnt/d/study/cityu/cs5491-ai/project/funsearch
```

### 1.4 设置环境变量

#### 本地模型（LM Studio）

```bash
export FUNSEARCH_LLM_HOST="127.0.0.1:1234"
export FUNSEARCH_LLM_PATH="/v1/chat/completions"
export FUNSEARCH_LLM_MODEL="qwen3-coder-30b-a3b-instruct"
export FUNSEARCH_LLM_USE_HTTPS="0"
export FUNSEARCH_DISABLE_THINKING="auto"
export FUNSEARCH_THINKING_PARAM_MODE="both"
export FUNSEARCH_MAX_NON_CODE_RETRIES="2"
export FUNSEARCH_VERBOSE_SAMPLES="${FUNSEARCH_VERBOSE_SAMPLES:-1}"  # 1=详细输出, 0=静默
```

#### 云端 API（可选）

```bash
export FUNSEARCH_CLOUD_API_KEY="<YOUR_API_KEY>"
export FUNSEARCH_CLOUD_BASE_URL="https://api.bltcy.ai"
export FUNSEARCH_CLOUD_MODEL="gpt-5-nano"
```

#### 去重相关

```bash
export FUNSEARCH_DEDUP_ENABLE="1"           # 1=开启去重, 0=关闭
export FUNSEARCH_STAGE1_CASE_COUNT="15"     # Stage 1 case 数量
export FUNSEARCH_STAGE2_RANDOM_CASES="128"  # Stage 2 随机 case 数量
export FUNSEARCH_REASONING_EFFORT="none"    # 关闭思考 (Responses API)
```

#### 数据集选择

```bash
export FUNSEARCH_DATASET_KEY="OR3"          # 可选: OR3, OR_u1000, OR_t501, Weibull 5k 等
export FUNSEARCH_MAX_SAMPLES="10"           # 最大样本数
```

> **注意：** `run_stage1_optimization.sh` 脚本已内置上述环境变量，直接运行脚本即可，无需手动设置。

---

## 2. 实验说明

实验脚本：`run_stage1_optimization.sh`

查看所有可用实验：

```bash
bash run_stage1_optimization.sh list
```

输出：

```
可用实验：
  1 - 基线无去重 (OR3, 10 samples, 3 repeats)
  2 - 新15 cases有去重 (OR3, 10 samples, 3 repeats)
  3 - 基线无去重 (OR_u1000, 5 samples, 3 repeats)
  4 - 新15 cases有去重 (OR_u1000, 5 samples, 3 repeats)
  5 - Stage2=64 (OR3)
  6 - Stage2=128 (OR3)
  7 - Stage2=256 (OR3)
  8 - Stage1=10 cases (OR3)
  9 - Stage1=15 cases (OR3)
  all - 跑全部实验
```

运行指定实验：

```bash
bash run_stage1_optimization.sh <实验编号>
```

---

## 3. 推荐实验顺序

### 第一轮：验证去重效果

| 顺序 | 命令 | 目的 |
|------|------|------|
| 1 | `bash run_stage1_optimization.sh 1` | OR3 基线（无去重） |
| 2 | `bash run_stage1_optimization.sh 2` | OR3 新15 cases（有去重） |

对比实验 1 和 2 的结果，观察去重是否有效。

### 第二轮：验证大数据集效果

| 顺序 | 命令 | 目的 |
|------|------|------|
| 3 | `bash run_stage1_optimization.sh 3` | OR_u1000 基线（无去重） |
| 4 | `bash run_stage1_optimization.sh 4` | OR_u1000 新15 cases（有去重） |

对比实验 3 和 4，观察大数据集上去重效果是否更显著。

### 第三轮：优化 Stage 2 参数

| 顺序 | 命令 | 目的 |
|------|------|------|
| 5 | `bash run_stage1_optimization.sh 5` | Stage2=64 |
| 6 | `bash run_stage1_optimization.sh 6` | Stage2=128 |
| 7 | `bash run_stage1_optimization.sh 7` | Stage2=256 |

对比 5、6、7，找到最优 Stage 2 随机 case 数量。

### 第四轮：优化 Stage 1 参数

| 顺序 | 命令 | 目的 |
|------|------|------|
| 8 | `bash run_stage1_optimization.sh 8` | Stage1=10 cases |
| 9 | `bash run_stage1_optimization.sh 9` | Stage1=15 cases |

对比 8 和 9，验证 15 个 cases 是否比 10 个更好。

---

## 4. 结果观察方法

### 4.1 查看实验汇总

每次实验完成后会自动生成汇总文件：

```bash
# OR3 数据集结果
cat logs/experiments/summary_OR3.csv

# OR_u1000 数据集结果
cat logs/experiments/summary_OR_u1000.csv
```

CSV 文件包含以下关键列：

| 列名 | 含义 |
|------|------|
| `baseline_best_score` | 基线最佳分数 |
| `dedup_best_score` | 去重后最佳分数 |
| `best_score_diff_dedup_minus_baseline` | 去重减基线的分数差 |
| `time_saved_ratio` | 时间节省比例 |
| `pipeline_time_saved_ratio` | 流水线时间节省比例 |
| `dedup_hit` | 去重命中次数 |
| `dedup_miss` | 去重未命中次数 |

### 4.2 查看去重统计

每次实验后查看去重引擎的详细统计：

```bash
cat logs/funsearch_llm_api/dedup_stats.json
```

输出示例：

```json
{
  "dedup_enable": true,
  "dedup_hit": 5,
  "dedup_miss": 15,
  "seen_hash_count": 12,
  "stage2_recheck": 8,
  "stage2_reject": 3,
  "stage2_pass": 5
}
```

关键指标：

| 指标 | 含义 |
|------|------|
| `dedup_hit` | Stage 1 hash 碰撞 + Stage 2 确认为重复的次数 |
| `dedup_miss` | Stage 1 hash 未碰撞，放行评估的次数 |
| `stage2_recheck` | 进入 Stage 2 复查的次数 |
| `stage2_pass` | Stage 2 确认为重复的次数 |
| `stage2_reject` | Stage 2 判定为新算法的次数 |

### 4.3 对比分析

实验 1 vs 实验 2 对比：

```bash
# 查看基线结果
head -5 logs/experiments/summary_OR3.csv

# 查看去重结果（实验 2 跑完后会覆盖同一个文件）
head -5 logs/experiments/summary_OR3.csv
```

也可以用 JSON 版本查看更详细的汇总：

```bash
cat logs/experiments/summary_OR3.json
```

### 4.4 运行分析脚本

```bash
bash analyze_dedup.sh
```

该脚本会自动汇总所有实验的去重统计和关键指标。

---

## 5. 预期结果

### 5.1 去重命中率

理想情况下，去重命中率应该：

- `dedup_hit / (dedup_hit + dedup_miss)` > 10%
- `stage2_pass / stage2_recheck` > 50%

如果去重命中率过低（< 5%），说明 Stage 1 cases 的区分度不够。

### 5.2 时间节省

OR_u1000 上的时间节省应该比 OR3 更显著：

- OR3：预期 `time_saved_ratio` ≈ 0.3% ~ 1%
- OR_u1000：预期 `time_saved_ratio` ≈ 2% ~ 5%

### 5.3 分数不下降

`best_score_diff_dedup_minus_baseline` 应该 >= 0，说明去重后解质量没有下降。

如果分数下降，说明去重过于激进，需要增加 Stage 2 cases 或调整 Stage 1 cases。

---

## 6. 故障排查

### 6.1 模型无法连接

```
WARNING: request exception retry=1: ConnectionRefusedError
```

解决：检查 LM Studio 是否启动，端口是否正确。

### 6.2 模型返回空响应

```
WARNING: sample rejected (empty/non-code after trim)
```

解决：检查模型是否支持当前的 prompt，可能需要调整 prompt 或换模型。

### 6.3 实验运行时间过长

如果实验运行时间过长，可以降低 `--max-samples` 和 `--repeats`：

```bash
# 降低 samples 和 repeats 来加速测试
python tools/run_experiment_matrix.py --dataset OR3 --max-samples 5 --repeats 1
```
