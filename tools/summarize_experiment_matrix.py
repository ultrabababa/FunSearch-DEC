import argparse
import csv
import json
from pathlib import Path
import sys
from statistics import median


THIS_DIR = Path(__file__).resolve().parent
if str(THIS_DIR) not in sys.path:
    sys.path.insert(0, str(THIS_DIR))

from compare_runs import summarize


def _to_float(value) -> float | None:
    if value in (None, "", "None"):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _safe_div(numerator: float | int | None, denominator: float | int | None) -> float | None:
    n = _to_float(numerator)
    d = _to_float(denominator)
    if n is None or d in (None, 0.0):
        return None
    return n / d


def _extract_target_fields(prefix: str, summary: dict) -> dict:
    return {
        f"{prefix}_target_score": summary.get("target_score"),
        f"{prefix}_target_reached": summary.get("target_reached"),
        f"{prefix}_calls_to_target": summary.get("calls_to_target"),
        f"{prefix}_sandbox_evals_to_target": summary.get("sandbox_evals_to_target"),
        f"{prefix}_pipeline_time_to_target_sec": summary.get("pipeline_time_to_target_sec"),
    }


def _both_reached_target(row: dict) -> bool:
    return row.get("baseline_target_reached") is True and row.get("dedup_target_reached") is True


def collect_run_summary(run_dir: Path) -> dict:
    csv_path = run_dir / "merged_samples.csv"
    dedup_stats = run_dir / "dedup_stats.json"
    summary = summarize(csv_path, dedup_stats if dedup_stats.exists() else None)
    metrics_path = run_dir / "run_metrics.json"
    if metrics_path.exists():
        summary["run_metrics"] = json.loads(metrics_path.read_text(encoding="utf-8"))
    else:
        summary["run_metrics"] = {}
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Summarize experiment matrix results")
    all_datasets = ["OR3", "Weibull 5k", "OR_u120", "OR_u250", "OR_u500", "OR_u1000",
                    "OR_t60", "OR_t120", "OR_t249", "OR_t501"]
    parser.add_argument("--dataset", choices=all_datasets, required=True)
    parser.add_argument("--repeats", type=int, default=3)
    parser.add_argument("--target-score", type=float, default=None)
    args = parser.parse_args()

    root = Path(__file__).resolve().parents[1] / "logs" / "experiments"
    tag = args.dataset.replace(" ", "_")
    rows = []

    for i in range(1, args.repeats + 1):
        base_dir = root / f"baseline_{tag}_r{i}"
        dedup_dir = root / f"dedup_{tag}_r{i}"
        b = summarize(
            base_dir / "merged_samples.csv",
            (base_dir / "dedup_stats.json") if (base_dir / "dedup_stats.json").exists() else None,
            target_score=args.target_score,
        )
        d = summarize(
            dedup_dir / "merged_samples.csv",
            (dedup_dir / "dedup_stats.json") if (dedup_dir / "dedup_stats.json").exists() else None,
            target_score=args.target_score,
        )

        b_metrics = json.loads((base_dir / "run_metrics.json").read_text(encoding="utf-8")) if (base_dir / "run_metrics.json").exists() else {}
        d_metrics = json.loads((dedup_dir / "run_metrics.json").read_text(encoding="utf-8")) if (dedup_dir / "run_metrics.json").exists() else {}

        rows.append(
            {
                "repeat": i,
                "dataset": args.dataset,
                "baseline_best_score": b["best_score"],
                "dedup_best_score": d["best_score"],
                "best_score_diff_dedup_minus_baseline": (
                    d["best_score"] - b["best_score"]
                    if b["best_score"] is not None and d["best_score"] is not None
                    else None
                ),
                "baseline_llm_calls": b["llm_calls"],
                "dedup_llm_calls": d["llm_calls"],
                "baseline_sandbox_evals": b["sandbox_evals"],
                "dedup_sandbox_evals": d["sandbox_evals"],
                "baseline_api_efficiency": _safe_div(b["llm_calls"], b["sandbox_evals"]),
                "dedup_api_efficiency": _safe_div(d["llm_calls"], d["sandbox_evals"]),
                "baseline_scored_rows": b["scored_rows"],
                "dedup_scored_rows": d["scored_rows"],
                "baseline_failed_rows": b["failed_rows"],
                "dedup_failed_rows": d["failed_rows"],
                "baseline_dedup_hits": b["dedup_hits"],
                "dedup_dedup_hits": d["dedup_hits"],
                "baseline_dedup_intercept_rate": b.get("dedup_intercept_rate"),
                "dedup_dedup_intercept_rate": d.get("dedup_intercept_rate"),
                "baseline_eval_failed": b["eval_failed"],
                "dedup_eval_failed": d["eval_failed"],
                "baseline_stage2_collision_reject_rate": b.get("stage2_collision_reject_rate"),
                "dedup_stage2_collision_reject_rate": d.get("stage2_collision_reject_rate"),
                "baseline_sample_time_total_sec": b.get("total_sample_time_sec"),
                "dedup_sample_time_total_sec": d.get("total_sample_time_sec"),
                "baseline_evaluate_time_total_sec": b.get("total_evaluate_time_sec"),
                "dedup_evaluate_time_total_sec": d.get("total_evaluate_time_sec"),
                "baseline_pipeline_time_total_sec": b.get("total_pipeline_time_sec"),
                "dedup_pipeline_time_total_sec": d.get("total_pipeline_time_sec"),
                "pipeline_time_saved_sec": (
                    (b.get("total_pipeline_time_sec") or 0)
                    - (d.get("total_pipeline_time_sec") or 0)
                ),
                "pipeline_time_saved_ratio": (
                    (
                        ((b.get("total_pipeline_time_sec") or 0)
                         - (d.get("total_pipeline_time_sec") or 0))
                        / (b.get("total_pipeline_time_sec") or 1)
                    )
                    if b.get("total_pipeline_time_sec")
                    else None
                ),
                "baseline_wall_time_total_sec": b_metrics.get("wall_time_total_sec"),
                "dedup_wall_time_total_sec": d_metrics.get("wall_time_total_sec"),
                "time_saved_sec": (
                    (b_metrics.get("wall_time_total_sec") or 0)
                    - (d_metrics.get("wall_time_total_sec") or 0)
                ),
                "time_saved_ratio": (
                    (
                        ((b_metrics.get("wall_time_total_sec") or 0)
                         - (d_metrics.get("wall_time_total_sec") or 0))
                        / (b_metrics.get("wall_time_total_sec") or 1)
                    )
                    if b_metrics.get("wall_time_total_sec")
                    else None
                ),
                **_extract_target_fields("baseline", b),
                **_extract_target_fields("dedup", d),
                "target_calls_saved": (
                    (b.get("calls_to_target") or 0) - (d.get("calls_to_target") or 0)
                    if b.get("calls_to_target") is not None and d.get("calls_to_target") is not None
                    else None
                ),
                "target_evals_saved": (
                    (b.get("sandbox_evals_to_target") or 0) - (d.get("sandbox_evals_to_target") or 0)
                    if b.get("sandbox_evals_to_target") is not None and d.get("sandbox_evals_to_target") is not None
                    else None
                ),
                "target_time_saved_sec": (
                    (b.get("pipeline_time_to_target_sec") or 0)
                    - (d.get("pipeline_time_to_target_sec") or 0)
                    if b.get("pipeline_time_to_target_sec") is not None and d.get("pipeline_time_to_target_sec") is not None
                    else None
                ),
                "target_time_saved_ratio": (
                    (
                        ((b.get("pipeline_time_to_target_sec") or 0)
                         - (d.get("pipeline_time_to_target_sec") or 0))
                        / (b.get("pipeline_time_to_target_sec") or 1)
                    )
                    if b.get("pipeline_time_to_target_sec") is not None
                    and d.get("pipeline_time_to_target_sec") is not None
                    and (b.get("pipeline_time_to_target_sec") or 0) > 0
                    else None
                ),
            }
        )

    out_csv = root / f"summary_{tag}.csv"
    out_json = root / f"summary_{tag}.json"
    out_csv.parent.mkdir(parents=True, exist_ok=True)

    with out_csv.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)

    both_reached_rows = [r for r in rows if _both_reached_target(r)]

    aggregate = {
        "dataset": args.dataset,
        "repeats": args.repeats,
        "target_score": args.target_score,
        "median_time_saved_ratio": median([r["time_saved_ratio"] for r in rows if r["time_saved_ratio"] is not None])
        if any(r["time_saved_ratio"] is not None for r in rows)
        else None,
        "median_pipeline_time_saved_ratio": median(
            [r["pipeline_time_saved_ratio"] for r in rows if r["pipeline_time_saved_ratio"] is not None]
        ) if any(r["pipeline_time_saved_ratio"] is not None for r in rows) else None,
        "median_target_time_saved_ratio": median(
            [r["target_time_saved_ratio"] for r in rows if r["target_time_saved_ratio"] is not None]
        ) if any(r["target_time_saved_ratio"] is not None for r in rows) else None,
        "target_reached_count_baseline": sum(1 for r in rows if r.get("baseline_target_reached") is True),
        "target_reached_count_dedup": sum(1 for r in rows if r.get("dedup_target_reached") is True),
        "target_reached_count_both": len(both_reached_rows),
        "median_target_time_saved_ratio_both_reached": median(
            [r["target_time_saved_ratio"] for r in both_reached_rows if r.get("target_time_saved_ratio") is not None]
        ) if any(r.get("target_time_saved_ratio") is not None for r in both_reached_rows) else None,
    }

    out_json.write_text(json.dumps({"rows": rows, "aggregate": aggregate}, indent=2), encoding="utf-8")
    print(f"Wrote: {out_csv}")
    print(f"Wrote: {out_json}")


if __name__ == "__main__":
    main()
