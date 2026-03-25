import argparse
import json
import subprocess
from pathlib import Path


def _run(cmd: list[str], cwd: Path) -> None:
    print("$", " ".join(cmd))
    subprocess.run(cmd, cwd=str(cwd), check=True)


def _infer_target_from_summary_csv(summary_csv: Path) -> float:
    import csv
    import statistics

    rows = list(csv.DictReader(summary_csv.open(encoding="utf-8")))
    vals = [float(r["baseline_best_score"]) for r in rows if r.get("baseline_best_score") not in ("", "None", None)]
    if not vals:
        raise RuntimeError(f"Cannot infer target from {summary_csv}: no baseline_best_score values")
    return float(statistics.median(vals))


def main() -> None:
    parser = argparse.ArgumentParser(description="Run tuned OR3/Weibull pipeline")
    parser.add_argument("--max-samples", type=int, default=50)
    parser.add_argument("--repeats", type=int, default=10)
    parser.add_argument("--stage1-case-count", type=int, default=10)
    parser.add_argument("--stage2-random-cases", type=int, default=128)
    parser.add_argument("--max-non-code-retries", type=int, default=2)
    parser.add_argument("--datasets", default="OR3,Weibull 5k")
    args = parser.parse_args()

    repo = Path(__file__).resolve().parents[1]
    logs = repo / "logs" / "experiments"
    datasets = [d.strip() for d in args.datasets.split(",") if d.strip()]

    for dataset in datasets:
        _run(
            [
                "python",
                "tools/run_experiment_matrix.py",
                "--dataset",
                dataset,
                "--max-samples",
                str(args.max_samples),
                "--repeats",
                str(args.repeats),
                "--stage1-case-count",
                str(args.stage1_case_count),
                "--stage2-random-cases",
                str(args.stage2_random_cases),
                "--max-non-code-retries",
                str(args.max_non_code_retries),
            ],
            repo,
        )

        _run(
            [
                "python",
                "tools/summarize_experiment_matrix.py",
                "--dataset",
                dataset,
                "--repeats",
                str(args.repeats),
            ],
            repo,
        )

        tag = dataset.replace(" ", "_")
        summary_csv = logs / f"summary_{tag}.csv"
        target = _infer_target_from_summary_csv(summary_csv)
        print(f"Inferred target for {dataset}: {target}")

        _run(
            [
                "python",
                "tools/summarize_experiment_matrix.py",
                "--dataset",
                dataset,
                "--repeats",
                str(args.repeats),
                "--target-score",
                str(target),
            ],
            repo,
        )

    print("Pipeline complete.")
    print(f"OR3 summary: {(logs / 'summary_OR3.json')}")
    print(f"Weibull summary: {(logs / 'summary_Weibull_5k.json')}")


if __name__ == "__main__":
    main()
