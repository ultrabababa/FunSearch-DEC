import argparse
import os
import shutil
import subprocess
import sys
import time
import json
from pathlib import Path
from urllib.parse import urlparse


def run_cmd(cmd: list[str], env: dict, cwd: Path) -> float:
    t0 = time.time()
    subprocess.run(cmd, cwd=str(cwd), env=env, check=True)
    return time.time() - t0


def _apply_cloud_env_mapping() -> None:
    cloud_base = os.getenv("FUNSEARCH_CLOUD_BASE_URL", "").strip()
    if not cloud_base:
        return

    parsed = urlparse(cloud_base if "://" in cloud_base else f"https://{cloud_base}")
    host = parsed.netloc
    if not host:
        return

    path = parsed.path.rstrip("/")
    if not path or path == "/v1":
        path = "/v1/chat/completions"

    os.environ.setdefault("FUNSEARCH_LLM_HOST", host)
    os.environ.setdefault("FUNSEARCH_LLM_USE_HTTPS", "1" if parsed.scheme.lower() == "https" else "0")
    os.environ.setdefault("FUNSEARCH_LLM_PATH", path)
    os.environ.setdefault("FUNSEARCH_LLM_MODEL", os.getenv("FUNSEARCH_CLOUD_MODEL", "gpt-5-nano"))

    cloud_key = os.getenv("FUNSEARCH_CLOUD_API_KEY", "").strip()
    if cloud_key:
        os.environ.setdefault("FUNSEARCH_LLM_API_KEY", cloud_key)


def run_one(
    repo_dir: Path,
    run_tag: str,
    dataset_key: str,
    dedup_enable: bool,
    max_samples: int,
) -> Path:
    env = os.environ.copy()
    env["FUNSEARCH_DATASET_KEY"] = dataset_key
    env["FUNSEARCH_DEDUP_ENABLE"] = "1" if dedup_enable else "0"
    env["FUNSEARCH_MAX_SAMPLES"] = str(max_samples)

    runtime_suffix = int(time.time() * 1000)
    log_root = repo_dir / "logs" / "runtime" / f"{run_tag}_{runtime_suffix}"
    env["FUNSEARCH_LOG_DIR"] = str(log_root)
    env["FUNSEARCH_SAMPLE_LOG_DIR"] = str(log_root / "raw_samples")
    env["FUNSEARCH_DEDUP_STATS_PATH"] = str(log_root / "dedup_stats.json")
    log_root.mkdir(parents=True, exist_ok=True)

    py = sys.executable
    t_funsearch = run_cmd([py, "funsearch_bin_packing_llm_api.py"], env, repo_dir)
    t_merge = run_cmd(
        [
            py,
            "tools/merge_sample_logs.py",
            "--raw-samples-dir",
            str(log_root / "raw_samples"),
            "--scores-dir",
            str(log_root / "samples"),
            "--output",
            str(log_root / "merged_samples.csv"),
        ],
        env,
        repo_dir,
    )
    t_inspect = run_cmd(
        [
            py,
            "tools/inspect_sample_quality.py",
            "--raw-samples-dir",
            str(log_root / "raw_samples"),
            "--csv",
            str(log_root / "merged_samples.csv"),
        ],
        env,
        repo_dir,
    )

    merged_csv = log_root / "merged_samples.csv"
    with merged_csv.open("r", encoding="utf-8") as f:
        line_count = sum(1 for _ in f)
    if line_count <= 1:
        raise RuntimeError(
            f"No merged sample rows for {run_tag}. "
            f"Check LLM sample logs under {log_root / 'raw_samples'} and FUNSEARCH_SAMPLE_LOG_DIR."
        )

    out_dir = repo_dir / "logs" / "experiments" / run_tag
    out_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy2(merged_csv, out_dir / "merged_samples.csv")
    if (log_root / "dedup_stats.json").exists():
        shutil.copy2(log_root / "dedup_stats.json", out_dir / "dedup_stats.json")

    metrics = {
        "run_tag": run_tag,
        "dataset": dataset_key,
        "dedup_enable": dedup_enable,
        "max_samples": max_samples,
        "wall_time_funsearch_sec": t_funsearch,
        "wall_time_merge_sec": t_merge,
        "wall_time_inspect_sec": t_inspect,
        "wall_time_total_sec": t_funsearch + t_merge + t_inspect,
    }
    (out_dir / "run_metrics.json").write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    return out_dir


def main() -> None:
    parser = argparse.ArgumentParser(description="Run baseline/dedup experiment matrix")
    all_datasets = ["OR3", "Weibull 5k", "OR_u120", "OR_u250", "OR_u500", "OR_u1000",
                    "OR_t60", "OR_t120", "OR_t249", "OR_t501"]
    parser.add_argument("--dataset", choices=all_datasets, required=True)
    parser.add_argument("--max-samples", type=int, default=8)
    parser.add_argument("--repeats", type=int, default=3)
    parser.add_argument("--stage1-case-count", type=int, default=None)
    parser.add_argument("--stage2-random-cases", type=int, default=None)
    parser.add_argument("--stage2-random-seed", type=int, default=None)
    parser.add_argument("--max-non-code-retries", type=int, default=None)
    args = parser.parse_args()

    _apply_cloud_env_mapping()

    if args.stage1_case_count is not None:
        os.environ["FUNSEARCH_STAGE1_CASE_COUNT"] = str(args.stage1_case_count)
    if args.stage2_random_cases is not None:
        os.environ["FUNSEARCH_STAGE2_RANDOM_CASES"] = str(args.stage2_random_cases)
    if args.stage2_random_seed is not None:
        os.environ["FUNSEARCH_STAGE2_RANDOM_SEED"] = str(args.stage2_random_seed)
    if args.max_non_code_retries is not None:
        os.environ["FUNSEARCH_MAX_NON_CODE_RETRIES"] = str(args.max_non_code_retries)

    repo_dir = Path(__file__).resolve().parents[1]
    for i in range(1, args.repeats + 1):
        run_one(repo_dir, f"baseline_{args.dataset.replace(' ', '_')}_r{i}", args.dataset, False, args.max_samples)
        run_one(repo_dir, f"dedup_{args.dataset.replace(' ', '_')}_r{i}", args.dataset, True, args.max_samples)

    print("Experiment matrix completed.")


if __name__ == "__main__":
    main()
