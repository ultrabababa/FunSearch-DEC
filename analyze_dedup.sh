#!/bin/bash
# ============================================================
# 快速分析去重效果的辅助脚本
# ============================================================

echo "=== 去重统计 ==="
for f in logs/experiments/*/dedup_stats.json; do
    if [ -f "$f" ]; then
        echo "--- $f ---"
        cat "$f"
        echo ""
    fi
done

echo ""
echo "=== 实验汇总 ==="
for f in logs/experiments/summary_*.csv; do
    if [ -f "$f" ]; then
        echo "--- $f ---"
        head -5 "$f"
        echo "..."
        echo ""
    fi
done

echo ""
echo "=== 关键指标对比 ==="
echo "查看 logs/experiments/summary_*.csv 中的以下列："
echo "  - time_saved_ratio: 时间节省比例"
echo "  - dedup_hit: 去重命中次数"
echo "  - dedup_miss: 去重未命中次数"
echo "  - stage2_recheck: Stage 2 复查次数"
echo "  - stage2_pass: Stage 2 确认重复次数"
echo "  - stage2_reject: Stage 2 判定为新算法次数"
