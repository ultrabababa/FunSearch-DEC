# FunSearch-DEC Complete Guide (English)

## 1. Project Overview

This project extends the course baseline `RayZhhh/funsearch` for online bin packing with a sample-efficiency enhancement called **Two-Stage Dynamic Equivalence Checking (DEC)**.

Core idea: intercept functionally duplicate heuristics early, reduce expensive sandbox evaluations, and preserve search quality.

---

## 2. Background and Motivation

FunSearch often generates programs that are syntactically different but behaviorally equivalent on bin-selection decisions. Evaluating those duplicates repeatedly wastes:

- LLM budget (API calls)
- Sandbox compute time
- Search iterations that could explore new behaviors

DEC addresses this by adding a fast behavior-level dedup layer before full evaluation.

---

## 3. Goals

1. Reduce total search time and expensive evaluations.
2. Improve API sample efficiency.
3. Keep or improve solution quality (best score).
4. Track false-positive risk carefully and transparently.

Primary evaluation logic: compare baseline vs DEC on **time/calls/evals to reach a target score**, plus fixed-budget quality checks.

---

## 4. Method Summary

### 4.1 Stage 1 (Curated Edge Cases)

- Execute candidate `priority()` on curated mock bin-packing states.
- Convert outputs into decision traces (`argmax` bin index sequence).
- Build Stage-1 behavior signature/hash quickly.

### 4.2 Stage 2 (Random Micro-Trace Recheck)

- For Stage-1 hash collisions, run random micro-cases and compare behavior traces.
- Only when Stage-2 trace matches cached traces, mark as duplicate and intercept.

### 4.3 Notes on Equivalence

Current equivalence is **behavioral/policy-level** (decision trace match), not strict symbolic function equivalence.

---

## 5. Parameter Decisions and Rationale

### 5.1 Tuned Default (current recommended)

- `FUNSEARCH_STAGE1_CASE_COUNT=10`
- `FUNSEARCH_STAGE2_RANDOM_CASES=128`
- `FUNSEARCH_MAX_NON_CODE_RETRIES=2`

Rationale:

- Better runtime-quality balance than weaker Stage-1 settings.
- Stage-2=128 gives stronger collision filtering than 64 with acceptable cost.
- Retries=2 reduces invalid/truncated sample failures without excessive latency.

### 5.2 Tuning Evidence

OR3 tuning grid output: `logs/experiments/or3_tuning_grid.csv`

- Candidate `stage1=6` often looked faster but had weaker target-reaching reliability.
- `stage1=10, stage2=128` stayed more stable for quality/consistency.

---

## 6. Implementation Architecture

### 6.1 Core Files

- `funsearch_bin_packing_llm_api.py`
  - Main API-based FunSearch entry
  - LLM request/response handling
  - `DedupSandbox` (Stage1+Stage2 DEC)
  - Dedup stats logging

- `funsearch_bin_packing_cloud_api.py`
  - Cloud wrapper
  - Maps `FUNSEARCH_CLOUD_*` to runtime settings

- `tools/run_experiment_matrix.py`
  - Runs paired baseline/dedup experiment matrix
  - Now supports cloud env auto-mapping
  - Uses isolated runtime log dirs

- `tools/summarize_experiment_matrix.py`
  - Produces `summary_<dataset>.csv/.json`
  - Computes aggregate metrics

- `tools/compare_runs.py`
  - Per-run summary extraction and comparison
  - Target-related metrics and dedup stats integration

- `tools/merge_sample_logs.py`
  - Merges raw samples and score logs into one CSV

- `tools/inspect_sample_quality.py`
  - Checks for empty/invalid/contaminated sample outputs

- `tools/run_best_config_pipeline.py`
  - One-command pipeline for OR3 + Weibull with tuned params
  - Auto-infers target from baseline median best score

- `tools/run_or3_tuning_grid.py`
  - Small-grid search for OR3 parameter tuning

### 6.2 Test Files (key)

- `tests/test_dedup_sandbox.py`
- `tests/test_llm_payload.py`
- `tests/test_run_experiment_matrix.py`
- `tests/test_cloud_env_mapping.py`
- `tests/test_tuning_knobs.py`
- `tests/test_evaluation_summary.py`

---

## 7. Experimental Environment and Configuration

### 7.1 Local Environment

```bash
cd funsearch
source .venv/bin/activate
```

### 7.2 Local LLM (LM Studio / local OpenAI-compatible)

Recommended settings used in this project:

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

### 7.3 Cloud API

```bash
export FUNSEARCH_CLOUD_API_KEY="<YOUR_API_KEY>"
export FUNSEARCH_CLOUD_BASE_URL="https://api.bltcy.ai"
export FUNSEARCH_CLOUD_MODEL="gpt-5-nano"
```

Connectivity check:

```bash
python tools/test_cloud_api_config.py --timeout 30
```

If needed, set proxy:

```bash
export HTTPS_PROXY="http://127.0.0.1:7897"
export HTTP_PROXY="http://127.0.0.1:7897"
```

---

## 8. Run Guide

### 8.1 One-command tuned pipeline (recommended)

```bash
python tools/run_best_config_pipeline.py \
  --max-samples 50 \
  --repeats 10 \
  --stage1-case-count 10 \
  --stage2-random-cases 128 \
  --max-non-code-retries 2
```

### 8.2 Colab Notebook

Use: `cloud_api_experiment_colab.ipynb`

Contains:

- setup + dependency install
- cloud config and connectivity check
- OR3 smoke mode (`repeats=1`)
- full OR3 + Weibull run
- aggregate display and file download

---

## 9. Result Metrics Definition

- `time_saved_ratio`: wall-clock saving ratio for fixed budget
- `pipeline_time_saved_ratio`: sample+evaluate time saving ratio
- `baseline_api_efficiency` / `dedup_api_efficiency`: `llm_calls / sandbox_evals`
- `target_reached_count_*`: count of runs reaching target
- `*_calls_to_target`, `*_sandbox_evals_to_target`, `*_pipeline_time_to_target_sec`
- `best_score_diff_dedup_minus_baseline`: quality difference

---

## 10. Latest Observed Results (Current Snapshot)

From:

- `logs/experiments/summary_OR3.json`
- `logs/experiments/summary_Weibull_5k.json`

Current run snapshot (tuned pipeline):

- OR3
  - `median_time_saved_ratio ≈ +0.003`
  - `median_pipeline_time_saved_ratio ≈ +0.029`
  - target reached: baseline `7`, dedup `5`

- Weibull 5k
  - `median_time_saved_ratio ≈ +0.038`
  - `median_pipeline_time_saved_ratio ≈ +0.029`
  - target reached: baseline `6`, dedup `4`

Interpretation:

- Runtime has improved versus earlier unstable phases.
- Target-reaching consistency still needs improvement (dedup trails baseline in this snapshot).

---

## 11. Known Limitations

1. Behavioral equivalence (trace match) is not full formal equivalence.
2. Target-time aggregates are sensitive when both-reached sample count is small.
3. Performance remains dataset-dependent (OR3 vs Weibull can diverge).

---

## 12. Expected Outcome Direction

Expected near-term target:

- Maintain positive `time_saved_ratio` and `pipeline_time_saved_ratio` on both datasets.
- Reduce target-reaching gap (dedup vs baseline).
- Keep quality non-degrading relative to baseline.
