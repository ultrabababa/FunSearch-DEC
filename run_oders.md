1) 跑 Baseline（不去重）
cd funsearch
source .venv/bin/activate
# 公共配置
export FUNSEARCH_LLM_HOST="127.0.0.1:1234"
export FUNSEARCH_LLM_PATH="/v1/chat/completions"
export FUNSEARCH_LLM_MODEL="qwen3-coder-30b-a3b-instruct"
export FUNSEARCH_LLM_USE_HTTPS="0"
export FUNSEARCH_DISABLE_THINKING="auto"
export FUNSEARCH_THINKING_PARAM_MODE="both"
export FUNSEARCH_MAX_NON_CODE_RETRIES="0"
export FUNSEARCH_VERBOSE_SAMPLES="0"
# baseline: 关闭去重
export FUNSEARCH_DEDUP_ENABLE=0
# 清日志并运行
rm -rf logs/funsearch_llm_api/raw_samples logs/funsearch_llm_api/samples logs/funsearch_llm_api/merged_samples.csv logs/funsearch_llm_api/dedup_stats.json
mkdir -p logs/funsearch_llm_api
python funsearch_bin_packing_llm_api.py
# 合并结果
python tools/merge_sample_logs.py
cp logs/funsearch_llm_api/merged_samples.csv logs/funsearch_llm_api/merged_samples_baseline.csv
cp logs/funsearch_llm_api/dedup_stats.json logs/funsearch_llm_api/dedup_stats_baseline.json
---
2) 跑 Dedup（开启去重）
# dedup: 开启去重
export FUNSEARCH_DEDUP_ENABLE=1
# 清日志并运行
rm -rf logs/funsearch_llm_api/raw_samples logs/funsearch_llm_api/samples logs/funsearch_llm_api/merged_samples.csv logs/funsearch_llm_api/dedup_stats.json

mkdir -p logs/funsearch_llm_api

python funsearch_bin_packing_llm_api.py
# 合并结果
python tools/merge_sample_logs.py

cp logs/funsearch_llm_api/merged_samples.csv logs/funsearch_llm_api/merged_samples_dedup.csv

cp logs/funsearch_llm_api/dedup_stats.json logs/funsearch_llm_api/dedup_stats_dedup.json
---
3) 一键对比
我已经加好了对比脚本：tools/compare_runs.py
python tools/compare_runs.py \
  --baseline-csv logs/funsearch_llm_api/merged_samples_baseline.csv \
  --dedup-csv logs/funsearch_llm_api/merged_samples_dedup.csv \
  --baseline-dedup-stats logs/funsearch_llm_api/dedup_stats_baseline.json \
  --dedup-dedup-stats logs/funsearch_llm_api/dedup_stats_dedup.json \
  --output-json logs/funsearch_llm_api/compare_baseline_vs_dedup.json
它会输出并保存：
- 总样本数
- 有分样本数
- 失败样本数
- dedup 命中数
- best score
- 两者差值
---
怎么解读结果
- dedup_hits 越高：说明你确实拦截了重复评估
- scored_rows 下降但 best_score 接近：说明省评估但性能不掉太多
- best_score_diff 接近 0 或更好：去重策略可用


怎么跑你要的 proposal evaluation（建议命令）
先设置公共环境（模型/endpoint你按本机）：
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
跑 OR3 实验矩阵（baseline+dedup，重复3次）：
python tools/run_experiment_matrix.py --dataset OR3 --max-samples 8 --repeats 3
python tools/summarize_experiment_matrix.py --dataset OR3 --repeats 3
跑 Weibull 5k：
python tools/run_experiment_matrix.py --dataset "Weibull 5k" --max-samples 8 --repeats 3
python tools/summarize_experiment_matrix.py --dataset "Weibull 5k" --repeats 3
输出位置：
- logs/experiments/summary_OR3.csv
- logs/experiments/summary_Weibull_5k.csv
- 对应 JSON 也会生成
---
你现在已经可以按 proposal 的指标做统计了：
- Time Saved（用 sample/evaluate 时间累计）
- API Sample Efficiency（calls vs scored evals）
- False Positive Rate（目前是 proxy，Stage 2 再做严格版）
- Performance Quality（best score 对比）
