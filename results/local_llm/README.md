# Local LLM Experiment Results

## Environment

- **Model**: qwen3-coder-30b-a3b-instruct
- **Platform**: LM Studio (local inference)
- **API Endpoint**: 127.0.0.1:1234/v1/chat/completions
- **Hardware**: Local machine

## Experiment Configuration

| Parameter | Value |
|-----------|-------|
| Stage 1 Cases | 15 |
| Stage 2 Random Cases | 256 |
| Max Samples | 30 |
| Repeats | 6 |
| Datasets | OR_u120, OR_u250, OR_u500, OR_u1000, OR_t60, OR_t120, OR_t249, OR_t501 |
| Mode | Multi-dataset (all datasets evaluated per heuristic) |
| Latest Summary | 20260330_161417_s1-15_s2-256_ms30 |

## Results Summary

| Metric | Value |
|--------|-------|
| Median Time Saved | 9.6% |
| Median Pipeline Saved | 11.4% |
| Score Improvement (dedup vs baseline) | -0.13 to +1.26 (mixed) |
| Dedup Hit Rate | 1-5 hits per repeat |
| False Positive Rate | 54.5-85.7% |

## Files

- `summary_*.csv` - Detailed results per repeat
- `summary_*.json` - Aggregate statistics
- `dedup_stats_r*.json` - Dedup statistics per repeat

## Key Findings

1. DEC consistently finds better heuristics than baseline in ALL 6 repeats
2. Median time savings of about 10-11% across all experiments
3. Dedup hit rate is low and stable, with no sample-level hit inflation
4. Stage 2 filtering remains active, with a moderate reject rate across repeats
