#!/bin/bash
# ============================================================
# Stage 1 Case 优化实验 - 本地模型版
# ============================================================
# 用法：
#   bash run_stage1_optimization.sh <实验编号>
#   bash run_stage1_optimization.sh 1      # 跑实验 1
#   bash run_stage1_optimization.sh all    # 跑全部实验
#   bash run_stage1_optimization.sh list   # 列出所有实验
# ============================================================

# --- 通用环境变量 ---
export FUNSEARCH_LLM_HOST="127.0.0.1:1234"
export FUNSEARCH_LLM_PATH="/v1/chat/completions"
export FUNSEARCH_LLM_MODEL="qwen3-coder-30b-a3b-instruct"
export FUNSEARCH_LLM_USE_HTTPS="0"
export FUNSEARCH_DISABLE_THINKING="auto"
export FUNSEARCH_THINKING_PARAM_MODE="both"
export FUNSEARCH_MAX_NON_CODE_RETRIES="2"
export FUNSEARCH_VERBOSE_SAMPLES="${FUNSEARCH_VERBOSE_SAMPLES:-1}"

# --- 列出所有实验 ---
if [ "$1" = "list" ] || [ -z "$1" ]; then
    echo "可用实验："
    echo "  1 - 基线无去重 (OR3, 10 samples, 3 repeats)"
    echo "  2 - 新15 cases有去重 (OR3, 10 samples, 3 repeats)"
    echo "  3 - 基线无去重 (OR_u1000, 5 samples, 3 repeats)"
    echo "  4 - 新15 cases有去重 (OR_u1000, 5 samples, 3 repeats)"
    echo "  5 - Stage2=64 (OR3)"
    echo "  6 - Stage2=128 (OR3)"
    echo "  7 - Stage2=256 (OR3)"
    echo "  8 - Stage1=10 cases (OR3)"
    echo "  9 - Stage1=15 cases (OR3)"
    echo "  all - 跑全部实验"
    echo ""
    echo "用法: bash run_stage1_optimization.sh <编号>"
    exit 0
fi

run_experiment() {
    echo ""
    echo "============================================================"
    echo "  实验 $1: $2"
    echo "============================================================"
    echo ""
}

run_summarize() {
    python tools/summarize_experiment_matrix.py --dataset "$1" --repeats 3
}

# --- 实验 1: 基线无去重 (OR3) ---
run_1() {
    run_experiment "1" "基线无去重 (OR3, 10 samples, 3 repeats)"
    export FUNSEARCH_DEDUP_ENABLE="0"
    export FUNSEARCH_DATASET_KEY="OR3"
    export FUNSEARCH_MAX_SAMPLES="10"
    python tools/run_experiment_matrix.py --dataset OR3 --max-samples 10 --repeats 3
    run_summarize "OR3"
}

# --- 实验 2: 新15 cases有去重 (OR3) ---
run_2() {
    run_experiment "2" "新15 cases有去重 (OR3, 10 samples, 3 repeats)"
    export FUNSEARCH_DEDUP_ENABLE="1"
    export FUNSEARCH_DATASET_KEY="OR3"
    export FUNSEARCH_MAX_SAMPLES="10"
    export FUNSEARCH_STAGE1_CASE_COUNT="15"
    python tools/run_experiment_matrix.py --dataset OR3 --max-samples 10 --repeats 3 --stage1-case-count 15
    run_summarize "OR3"
}

# --- 实验 3: 基线无去重 (OR_u1000) ---
run_3() {
    run_experiment "3" "基线无去重 (OR_u1000, 5 samples, 3 repeats)"
    export FUNSEARCH_DEDUP_ENABLE="0"
    export FUNSEARCH_DATASET_KEY="OR_u1000"
    export FUNSEARCH_MAX_SAMPLES="5"
    python tools/run_experiment_matrix.py --dataset OR_u1000 --max-samples 5 --repeats 3
    run_summarize "OR_u1000"
}

# --- 实验 4: 新15 cases有去重 (OR_u1000) ---
run_4() {
    run_experiment "4" "新15 cases有去重 (OR_u1000, 5 samples, 3 repeats)"
    export FUNSEARCH_DEDUP_ENABLE="1"
    export FUNSEARCH_DATASET_KEY="OR_u1000"
    export FUNSEARCH_MAX_SAMPLES="5"
    export FUNSEARCH_STAGE1_CASE_COUNT="15"
    python tools/run_experiment_matrix.py --dataset OR_u1000 --max-samples 5 --repeats 3 --stage1-case-count 15
    run_summarize "OR_u1000"
}

# --- 实验 5: Stage2=64 (OR3) ---
run_5() {
    run_experiment "5" "Stage2=64 (OR3, 10 samples, 3 repeats)"
    export FUNSEARCH_DEDUP_ENABLE="1"
    export FUNSEARCH_DATASET_KEY="OR3"
    export FUNSEARCH_MAX_SAMPLES="10"
    export FUNSEARCH_STAGE1_CASE_COUNT="15"
    python tools/run_experiment_matrix.py --dataset OR3 --max-samples 10 --repeats 3 --stage1-case-count 15 --stage2-random-cases 64
    run_summarize "OR3"
}

# --- 实验 6: Stage2=128 (OR3) ---
run_6() {
    run_experiment "6" "Stage2=128 (OR3, 10 samples, 3 repeats)"
    export FUNSEARCH_DEDUP_ENABLE="1"
    export FUNSEARCH_DATASET_KEY="OR3"
    export FUNSEARCH_MAX_SAMPLES="10"
    export FUNSEARCH_STAGE1_CASE_COUNT="15"
    python tools/run_experiment_matrix.py --dataset OR3 --max-samples 10 --repeats 3 --stage1-case-count 15 --stage2-random-cases 128
    run_summarize "OR3"
}

# --- 实验 7: Stage2=256 (OR3) ---
run_7() {
    run_experiment "7" "Stage2=256 (OR3, 10 samples, 3 repeats)"
    export FUNSEARCH_DEDUP_ENABLE="1"
    export FUNSEARCH_DATASET_KEY="OR3"
    export FUNSEARCH_MAX_SAMPLES="10"
    export FUNSEARCH_STAGE1_CASE_COUNT="15"
    python tools/run_experiment_matrix.py --dataset OR3 --max-samples 10 --repeats 3 --stage1-case-count 15 --stage2-random-cases 256
    run_summarize "OR3"
}

# --- 实验 8: Stage1=10 cases (OR3) ---
run_8() {
    run_experiment "8" "Stage1=10 cases (OR3, 10 samples, 3 repeats)"
    export FUNSEARCH_DEDUP_ENABLE="1"
    export FUNSEARCH_DATASET_KEY="OR3"
    export FUNSEARCH_MAX_SAMPLES="10"
    python tools/run_experiment_matrix.py --dataset OR3 --max-samples 10 --repeats 3 --stage1-case-count 10
    run_summarize "OR3"
}

# --- 实验 9: Stage1=15 cases (OR3) ---
run_9() {
    run_experiment "9" "Stage1=15 cases (OR3, 10 samples, 3 repeats)"
    export FUNSEARCH_DEDUP_ENABLE="1"
    export FUNSEARCH_DATASET_KEY="OR3"
    export FUNSEARCH_MAX_SAMPLES="10"
    python tools/run_experiment_matrix.py --dataset OR3 --max-samples 10 --repeats 3 --stage1-case-count 15
    run_summarize "OR3"
}

# --- 执行指定实验 ---
if [ "$1" = "all" ]; then
    for i in 1 2 3 4 5 6 7 8 9; do
        run_$i
    done
else
    case "$1" in
        1) run_1 ;;
        2) run_2 ;;
        3) run_3 ;;
        4) run_4 ;;
        5) run_5 ;;
        6) run_6 ;;
        7) run_7 ;;
        8) run_8 ;;
        9) run_9 ;;
        *) echo "未知实验编号: $1"; echo "用 'bash run_stage1_optimization.sh list' 查看可用实验"; exit 1 ;;
    esac
fi

echo ""
echo "============================================================"
echo "  实验完成！查看结果："
echo "============================================================"
echo ""
echo "  cat logs/experiments/summary_OR3.csv"
echo "  cat logs/experiments/summary_OR_u1000.csv"
echo "  cat logs/funsearch_llm_api/dedup_stats.json"
