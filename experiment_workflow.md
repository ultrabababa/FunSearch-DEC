# FunSearch 实验流程（本地模型 + 云端 API）

本文档总结了当前实验设计，以及可直接执行的命令，用于对齐 proposal 的评估指标。

## 1）实验设计

- 主模式：**目标分数追踪（target-score tracking）**，从运行日志统计达到目标分数所需的 `calls/evals/time`。
- 辅助模式：**固定预算对比（fixed-budget）**，在相同 `max-samples` 下比较最终质量与总耗时。
- 数据集：`OR3`、`Weibull 5k`。
- 重复次数：建议 `10`（预算允许可更高）。

## 2）Proposal 指标与字段映射

统计来源：`logs/experiments/summary_<dataset>.csv` 和对应 `.json`。

- `Time Saved`
  - `time_saved_sec`、`time_saved_ratio`（矩阵运行器记录的 wall-clock）
  - `pipeline_time_saved_sec`、`pipeline_time_saved_ratio`（sample+evaluate 累计）
- `API Sample Efficiency`
  - `baseline_api_efficiency`、`dedup_api_efficiency`（`llm_calls / sandbox_evals`）
  - 目标分数口径：`*_calls_to_target`、`*_sandbox_evals_to_target`
- `False Positive Rate`（当前为 proxy）
  - `dedup_dedup_intercept_rate`
  - `dedup_stage2_collision_reject_rate`
- `Performance Quality`
  - `baseline_best_score`、`dedup_best_score`、`best_score_diff_dedup_minus_baseline`

## 3）本地模型模式（LM Studio / 本地 OpenAI 兼容端点）

适用于你现在的本地模型（例如 `qwen3-coder-30b-a3b-instruct`）：

```bash
cd funsearch
source .venv/bin/activate

export FUNSEARCH_LLM_HOST="127.0.0.1:1234"
export FUNSEARCH_LLM_PATH="/v1/chat/completions"
export FUNSEARCH_LLM_MODEL="qwen3-coder-30b-a3b-instruct"
export FUNSEARCH_LLM_USE_HTTPS="0"
export FUNSEARCH_DISABLE_THINKING="auto"
export FUNSEARCH_THINKING_PARAM_MODE="both"
export FUNSEARCH_MAX_NON_CODE_RETRIES="0"
export FUNSEARCH_VERBOSE_SAMPLES="0"
```

运行实验矩阵：

```bash
python tools/run_experiment_matrix.py --dataset OR3 --max-samples 8 --repeats 10
python tools/run_experiment_matrix.py --dataset "Weibull 5k" --max-samples 8 --repeats 10
```

生成汇总（目标分数填入你基线中位数）：

```bash
python tools/summarize_experiment_matrix.py --dataset OR3 --repeats 10 --target-score <TARGET_OR3> -212.75
python tools/summarize_experiment_matrix.py --dataset "Weibull 5k" --repeats 10 --target-score <TARGET_WEIBULL> -2071.8
```

## 4）目标分数如何设定

推荐稳健方案：

1. 先做 baseline 预跑（同预算，例如 `repeats=10`）。
2. 对每个数据集计算 `baseline_best_score` 的中位数。
3. 将该中位数作为正式 baseline-vs-dedup 对比的目标分数。

这样可兼顾“可达性”和“统计稳定性”。

### OR3 示例（你刚跑完 `repeats=10` 可直接用）

先生成一次不带 target 的汇总：

```bash
python tools/summarize_experiment_matrix.py --dataset OR3 --repeats 10
```

再从 `summary_OR3.csv` 提取 `baseline_best_score` 的中位数（作为 `TARGET_OR3`）：

```bash
python - <<'PY'
import csv, statistics
rows = list(csv.DictReader(open('logs/experiments/summary_OR3.csv', encoding='utf-8')))
vals = [float(r['baseline_best_score']) for r in rows if r['baseline_best_score'] not in ('', 'None')]
print('TARGET_OR3=', statistics.median(vals))
PY
```

最后带上目标分数重新生成汇总（会产出 to-target 字段）：

```bash
python tools/summarize_experiment_matrix.py --dataset OR3 --repeats 10 --target-score <TARGET_OR3> -212.575
```

> 当前执行建议：先只用 `TARGET_OR3`（中位数）完成主实验和主结论。
> 后续扩展分析再增加一个更严格阈值（hard target，例如中位数之上的下一个唯一分数或更高分位数）。

### Weibull 5k 同样步骤

```bash
python tools/summarize_experiment_matrix.py --dataset "Weibull 5k" --repeats 10

python - <<'PY'
import csv, statistics
rows = list(csv.DictReader(open('logs/experiments/summary_Weibull_5k.csv', encoding='utf-8')))
vals = [float(r['baseline_best_score']) for r in rows if r['baseline_best_score'] not in ('', 'None')]
print('TARGET_WEIBULL=', statistics.median(vals))
PY

python tools/summarize_experiment_matrix.py --dataset "Weibull 5k" --repeats 10 --target-score <TARGET_WEIBULL>
```

> 同样地，先用 `TARGET_WEIBULL`（中位数）作为主目标；hard target 作为后续补充实验。

## 5）云端 API 模式（兼容课程 API key notebook）

参考：`test_your_api_key.ipynb`（`OpenAI(base_url=HOST_URL + "/v1", api_key=...)`）。

本项目已新增 `funsearch_bin_packing_cloud_api.py`，会将云端环境变量映射到现有 API runner。

云端环境变量：

- `FUNSEARCH_CLOUD_API_KEY`（必填）
- `FUNSEARCH_CLOUD_BASE_URL`（默认：`https://api.bltcy.ai`）
- `FUNSEARCH_CLOUD_MODEL`（默认：`gpt-5-nano`）

### 0. 快速校验云端配置（建议先执行）

新增了快速校验脚本：`tools/test_cloud_api_config.py`。

它会：

- 读取云端环境变量；
- 打印解析后的 host/path/https；
- 发一个最小 chat 请求并返回结果预览；
- 成功时输出 `CLOUD_API_CONFIG_OK`。

```bash
cd funsearch
source .venv/bin/activate

export FUNSEARCH_CLOUD_API_KEY="<YOUR_API_KEY>"
export FUNSEARCH_CLOUD_BASE_URL="https://api.bltcy.ai"
export FUNSEARCH_CLOUD_MODEL="gpt-5-nano"

python tools/test_cloud_api_config.py
```

可选参数（例如 10 秒超时）：

```bash
python tools/test_cloud_api_config.py --timeout 10
```

如果你的网络必须走代理（例如你本机设置了 Clash 7897），请确保代理环境变量已设置：

```bash
export HTTPS_PROXY="http://127.0.0.1:7897"
export HTTP_PROXY="http://127.0.0.1:7897"
```

说明：当前脚本与主运行器均已支持读取 `HTTPS_PROXY/HTTP_PROXY` 并通过代理发起请求。

示例：

```bash
cd funsearch
source .venv/bin/activate

export FUNSEARCH_CLOUD_API_KEY="<YOUR_API_KEY>"
export FUNSEARCH_CLOUD_BASE_URL="https://api.bltcy.ai"
export FUNSEARCH_CLOUD_MODEL="gpt-5-nano"

export FUNSEARCH_DATASET_KEY="OR3"
export FUNSEARCH_DEDUP_ENABLE="1"
export FUNSEARCH_MAX_SAMPLES="8"
export FUNSEARCH_VERBOSE_SAMPLES="0"
```

### A. 单次连通性测试（仅用于确认云端 API 可用）

这一步只用于验证“能否正常请求云端模型并产生日志”，不用于正式对比结论。

```bash
python funsearch_bin_packing_cloud_api.py
python tools/merge_sample_logs.py
python tools/inspect_sample_quality.py
```

### B. 正式矩阵实验（用于报告）

确认 A 成功后，直接跑矩阵。`run_experiment_matrix.py` 会在每个 repeat 内自动跑：

1. baseline（`FUNSEARCH_DEDUP_ENABLE=0`）
2. dedup（`FUNSEARCH_DEDUP_ENABLE=1`）

因此你不需要手动切换 dedup 开关。

```bash
python tools/run_experiment_matrix.py --dataset OR3 --max-samples 8 --repeats 10
python tools/run_experiment_matrix.py --dataset "Weibull 5k" --max-samples 8 --repeats 10
```

矩阵完成后，再生成带目标分数的汇总：

```bash
python tools/summarize_experiment_matrix.py --dataset OR3 --repeats 10 --target-score <TARGET_OR3>
python tools/summarize_experiment_matrix.py --dataset "Weibull 5k" --repeats 10 --target-score <TARGET_WEIBULL>
```

## 6）输出文件

- 单次运行目录：`logs/experiments/<baseline|dedup>_<dataset>_rN/`
- 矩阵运行时的中间日志目录：`logs/runtime/<run_tag>/`（已隔离，避免并发互相覆盖）
- 云端单次运行默认日志目录：`logs/funsearch_cloud_api/`
- 如需自定义日志目录，可设置：`FUNSEARCH_LOG_DIR=/your/log/dir`
- 最终汇总：
  - `logs/experiments/summary_OR3.csv`
  - `logs/experiments/summary_OR3.json`
  - `logs/experiments/summary_Weibull_5k.csv`
  - `logs/experiments/summary_Weibull_5k.json`

# 最新实验
python tools/run_experiment_matrix.py --dataset OR3 --max-samples 50 --repeats 10
python tools/summarize_experiment_matrix.py --dataset OR3 --repeats 10

❯ python - <<'PY'
import csv, statistics
rows = list(csv.DictReader(open('logs/experiments/summary_OR3.csv', encoding='utf-8')))
vals = [float(r['baseline_best_score']) for r in rows if r['baseline_best_score'] not in ('', 'None')]
print('TARGET_OR3=', statistics.median(vals))
PY
TARGET_OR3= -212.575

❯ python tools/summarize_experiment_matrix.py --dataset OR3 --repeats 10 --target-score -212.575
Wrote: /mnt/d/study/cityu/cs5491-ai/project/funsearch/logs/experiments/summary_OR3.csv
Wrote: /mnt/d/study/cityu/cs5491-ai/project/funsearch/logs/experiments/summary_OR3.json

python tools/run_experiment_matrix.py --dataset "Weibull 5k" --max-samples 50 --repeats 10
python tools/summarize_experiment_matrix.py --dataset "Weibull 5k" --repeats 10

python - <<'PY'
import csv, statistics
rows = list(csv.DictReader(open('logs/experiments/summary_Weibull_5k.csv', encoding='utf-8')))
vals = [float(r['baseline_best_score']) for r in rows if r['baseline_best_score'] not in ('', 'None')]
print('TARGET_WEIBULL=', statistics.median(vals))
PY

python tools/summarize_experiment_matrix.py --dataset "Weibull 5k" --repeats 10 --target-score -2070.5
