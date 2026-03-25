import argparse
import csv
import itertools
import json
import os
import subprocess
from pathlib import Path


def _run(cmd: list[str], cwd: Path) -> None:
    subprocess.run(cmd, cwd=str(cwd), check=True)


def _load_aggregate(summary_json: Path) -> dict:
    data = json.loads(summary_json.read_text(encoding="utf-8"))
    return data.get("aggregate", {})


def _score_candidate(agg: dict) -> tuple[float, float, float]:
    time_saved = float(agg.get("median_time_saved_ratio") or 0.0)
    pipeline_saved = float(agg.get("median_pipeline_time_saved_ratio") or 0.0)
    target_balance = float((agg.get("target_reached_count_dedup") or 0) - (agg.get("target_reached_count_baseline") or 0))
    return (time_saved + 0.5 * pipeline_saved, time_saved, target_balance)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run OR3 dedup tuning grid")
    parser.add_argument("--max-samples", type=int, default=20)
    parser.add_argument("--repeats", type=int, default=3)
    parser.add_argument("--target-score", type=float, required=True)
    parser.add_argument("--stage1-options", default="6,10")
    parser.add_argument("--stage2-options", default="64,128")
    parser.add_argument("--retry-options", default="2,3")
    args = parser.parse_args()

    repo = Path(__file__).resolve().parents[1]
    logs_dir = repo / "logs" / "experiments"
    out_csv = logs_dir / "or3_tuning_grid.csv"

    stage1_options = [int(x) for x in args.stage1_options.split(",") if x.strip()]
    stage2_options = [int(x) for x in args.stage2_options.split(",") if x.strip()]
    retry_options = [int(x) for x in args.retry_options.split(",") if x.strip()]

    rows = []
    for stage1, stage2, retries in itertools.product(stage1_options, stage2_options, retry_options):
        env = os.environ.copy()
        env["FUNSEARCH_STAGE1_CASE_COUNT"] = str(stage1)
        env["FUNSEARCH_STAGE2_RANDOM_CASES"] = str(stage2)
        env["FUNSEARCH_MAX_NON_CODE_RETRIES"] = str(retries)

        run_cmd = [
            os.sys.executable,
            "tools/run_experiment_matrix.py",
            "--dataset",
            "OR3",
            "--max-samples",
            str(args.max_samples),
            "--repeats",
            str(args.repeats),
            "--stage1-case-count",
            str(stage1),
            "--stage2-random-cases",
            str(stage2),
            "--max-non-code-retries",
            str(retries),
        ]
        subprocess.run(run_cmd, cwd=str(repo), env=env, check=True)

        sum_cmd = [
            os.sys.executable,
            "tools/summarize_experiment_matrix.py",
            "--dataset",
            "OR3",
            "--repeats",
            str(args.repeats),
            "--target-score",
            str(args.target_score),
        ]
        subprocess.run(sum_cmd, cwd=str(repo), env=env, check=True)

        agg = _load_aggregate(logs_dir / "summary_OR3.json")
        score_primary, score_time, score_target = _score_candidate(agg)
        rows.append(
            {
                "stage1_case_count": stage1,
                "stage2_random_cases": stage2,
                "max_non_code_retries": retries,
                "median_time_saved_ratio": agg.get("median_time_saved_ratio"),
                "median_pipeline_time_saved_ratio": agg.get("median_pipeline_time_saved_ratio"),
                "target_reached_count_baseline": agg.get("target_reached_count_baseline"),
                "target_reached_count_dedup": agg.get("target_reached_count_dedup"),
                "score_primary": score_primary,
                "score_time": score_time,
                "score_target_balance": score_target,
            }
        )

    rows.sort(key=lambda r: (r["score_primary"], r["score_target_balance"]), reverse=True)
    logs_dir.mkdir(parents=True, exist_ok=True)
    with out_csv.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    print(f"Wrote tuning results: {out_csv}")
    print("Top 3 configurations:")
    for r in rows[:3]:
        print(r)


if __name__ == "__main__":
    main()
