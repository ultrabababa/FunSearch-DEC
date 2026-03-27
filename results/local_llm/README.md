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
| Max Samples | 20 |
| Repeats | 6 |
| Datasets | OR_u120, OR_u250, OR_u500, OR_u1000, OR_t60, OR_t120, OR_t249, OR_t501 |
| Mode | Multi-dataset (all datasets evaluated per heuristic) |

## Results Summary

| Metric | Value |
|--------|-------|
| Median Time Saved | 58.9% |
| Median Pipeline Saved | 58.8% |
| Score Improvement (dedup vs baseline) | +35 to +93 (all positive) |
| Dedup Hit Rate | 75-80% |
| False Positive Rate | <5% |

## Files

- `summary_*.csv` - Detailed results per repeat
- `summary_*.json` - Aggregate statistics
- `dedup_stats_r*.json` - Dedup statistics per repeat

## Key Findings

1. DEC consistently finds better heuristics than baseline in ALL 6 repeats
2. Average time savings of 59% across all experiments
3. Stable dedup hit rate of 75-80%
4. Stage 2 filtering effectively reduces false positives to <5%
