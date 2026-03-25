# FunSearch-DEC 完整指南（中文）

## 1. 项目说明

本项目基于课程 baseline `RayZhhh/funsearch`，针对在线装箱问题实现了 **Two-Stage Dynamic Equivalence Checking（DEC）**，目标是提升 FunSearch 的样本效率与整体运行效率。

核心思想：在昂贵的完整 sandbox 评估前，先拦截行为重复（功能等价）的候选启发式。

---

## 2. 背景与动机

FunSearch 在生成代码时，常出现“语法不同但决策行为一致”的程序。若每次都进入完整评估，会浪费：

- API 调用预算
- 沙盒评估时间
- 可用于探索新策略的迭代机会

DEC 用两阶段机制做快速去重，减少这类重复开销。

---

## 3. 项目目标

1. 降低总耗时与评估开销。
2. 提升 API Sample Efficiency。
3. 保证（或提升）最终性能质量（best score）。
4. 对误拦截风险进行可追踪统计。

主实验逻辑：比较 baseline 与 DEC 在“达到目标分数”时的耗时/调用/评估数量，并辅以 fixed-budget 对比。

---

## 4. 方法说明

### 4.1 Stage 1（精选边界样本）

- 在一组精心设计的 mock 状态上执行 `priority()`。
- 将输出转成决策轨迹（`argmax` 序列）。
- 快速得到 Stage-1 行为签名/hash。

### 4.2 Stage 2（随机微样本复核）

- 对 Stage-1 哈希碰撞样本做随机微样本轨迹复核。
- 仅当 Stage-2 轨迹完全匹配缓存轨迹时，判定重复并拦截。

### 4.3 等价性口径

当前等价性是**行为/策略层面**（决策轨迹一致），不是严格符号函数等价。

---

## 5. 参数决策与理由

### 5.1 当前推荐参数

- `FUNSEARCH_STAGE1_CASE_COUNT=10`
- `FUNSEARCH_STAGE2_RANDOM_CASES=128`
- `FUNSEARCH_MAX_NON_CODE_RETRIES=2`

理由：

- 相比更弱 Stage1 配置，稳定性更好。
- Stage2=128 相比 64 有更强碰撞过滤能力，代价可接受。
- retries=2 可降低无效输出失败率，且不会显著拖慢采样。

### 5.2 调参证据

OR3 网格搜索结果：`logs/experiments/or3_tuning_grid.csv`

- `stage1=6` 组合有时更快，但达标稳定性偏弱。
- `stage1=10, stage2=128` 在稳定性与质量一致性上更平衡。

---

## 6. 实现架构与代码路径

### 6.1 核心实现

- `funsearch_bin_packing_llm_api.py`
  - API 版主入口
  - LLM 请求与响应处理
  - `DedupSandbox`（Stage1+Stage2）
  - 去重统计输出

- `funsearch_bin_packing_cloud_api.py`
  - 云端封装入口
  - 将 `FUNSEARCH_CLOUD_*` 映射到运行参数

- `tools/run_experiment_matrix.py`
  - baseline/dedup 成对矩阵实验
  - 支持 cloud 环境变量自动映射
  - 使用隔离 runtime 日志目录

- `tools/summarize_experiment_matrix.py`
  - 生成 `summary_<dataset>.csv/.json`
  - 聚合实验指标

- `tools/compare_runs.py`
  - 单轮汇总与对比
  - 包含 target 指标和 dedup 统计整合

- `tools/merge_sample_logs.py`
  - 合并 raw sample 与 score 日志

- `tools/inspect_sample_quality.py`
  - 检查空样本、污染样本等质量问题

- `tools/run_best_config_pipeline.py`
  - 一键执行 OR3+Weibull 推荐参数流程
  - 自动根据 baseline 中位数推断 target

- `tools/run_or3_tuning_grid.py`
  - OR3 小网格调参脚本

### 6.2 关键测试

- `tests/test_dedup_sandbox.py`
- `tests/test_llm_payload.py`
- `tests/test_run_experiment_matrix.py`
- `tests/test_cloud_env_mapping.py`
- `tests/test_tuning_knobs.py`
- `tests/test_evaluation_summary.py`

---

## 7. 实验环境配置

### 7.1 本地环境

```bash
cd funsearch
source .venv/bin/activate
```

### 7.2 本地 LLM（LM Studio / 本地兼容 API）

本项目建议配置：

```bash
export FUNSEARCH_LLM_HOST="127.0.0.1:1234"
export FUNSEARCH_LLM_PATH="/v1/chat/completions"
export FUNSEARCH_LLM_MODEL="qwen3-coder-30b-a3b-instruct"
export FUNSEARCH_LLM_USE_HTTPS="0"
export FUNSEARCH_DISABLE_THINKING="auto"
export FUNSEARCH_THINKING_PARAM_MODE="both"
export FUNSEARCH_MAX_NON_CODE_RETRIES="2"
export FUNSEARCH_VERBOSE_SAMPLES="0"
```

### 7.3 云端 API

```bash
export FUNSEARCH_CLOUD_API_KEY="<YOUR_API_KEY>"
export FUNSEARCH_CLOUD_BASE_URL="https://api.bltcy.ai"
export FUNSEARCH_CLOUD_MODEL="gpt-5-nano"
```

连通性检查：

```bash
python tools/test_cloud_api_config.py --timeout 30
```

如需代理：

```bash
export HTTPS_PROXY="http://127.0.0.1:7897"
export HTTP_PROXY="http://127.0.0.1:7897"
```

---

## 8. 运行指南

### 8.1 一键推荐流程（建议）

```bash
python tools/run_best_config_pipeline.py \
  --max-samples 50 \
  --repeats 10 \
  --stage1-case-count 10 \
  --stage2-random-cases 128 \
  --max-non-code-retries 2
```

### 8.2 Colab Notebook

使用：`cloud_api_experiment_colab.ipynb`

包含：

- 环境搭建与依赖安装
- 云端配置与连通性检查
- OR3 快速 smoke 模式（`repeats=1`）
- OR3 + Weibull 全量实验
- 聚合展示与结果下载

---

## 9. 指标定义（与 proposal 对齐）

- `time_saved_ratio`：固定预算下 wall-clock 节省比例（>0 更好）
- `pipeline_time_saved_ratio`：sample+evaluate 过程节省比例（>0 更好）
- `baseline_api_efficiency` / `dedup_api_efficiency`：`llm_calls / sandbox_evals`
- `target_reached_count_*`：达到目标分数的轮次数
- `*_calls_to_target`、`*_sandbox_evals_to_target`、`*_pipeline_time_to_target_sec`
- `best_score_diff_dedup_minus_baseline`：质量差值（>0 表示 dedup 更优）

---

## 10. 当前结果快照（最新）

来源：

- `logs/experiments/summary_OR3.json`
- `logs/experiments/summary_Weibull_5k.json`

当前一轮完整流程结果（示例快照）：

- OR3
  - `median_time_saved_ratio ≈ +0.003`
  - `median_pipeline_time_saved_ratio ≈ +0.029`
  - target 达标：baseline `7`，dedup `5`

- Weibull 5k
  - `median_time_saved_ratio ≈ +0.038`
  - `median_pipeline_time_saved_ratio ≈ +0.029`
  - target 达标：baseline `6`，dedup `4`

解读：

- 与早期不稳定阶段相比，时间指标已回正。
- 但达标稳定性仍需继续提升（当前 dedup 仍落后 baseline）。

---

## 11. 已知限制

1. 当前是行为等价判定，不是形式化函数等价证明。
2. 两边都达标样本较少时，to-target 聚合对波动敏感。
3. 跨数据集泛化存在差异（OR3 与 Weibull 表现可能不一致）。

---

## 12. 预期结果方向

下一阶段目标：

- 在两个数据集上维持 `time_saved_ratio`、`pipeline_time_saved_ratio` 为正。
- 缩小 dedup 与 baseline 的 target 达标差距。
- 保持质量不退化。
