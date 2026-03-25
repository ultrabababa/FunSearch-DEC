import argparse
import csv
import json
from pathlib import Path


def load_manifests(manifests_dir: Path) -> list[dict]:
    manifests = []
    for path in sorted(manifests_dir.glob("sample_*_manifest.json")):
        with path.open("r", encoding="utf-8") as f:
            manifests.append(json.load(f))
    return manifests


def load_scores(scores_dir: Path) -> dict[int, dict]:
    scores = {}
    for path in sorted(scores_dir.glob("samples_*.json")):
        with path.open("r", encoding="utf-8") as f:
            sample = json.load(f)
        sample_order = sample.get("sample_order")
        if isinstance(sample_order, int):
            scores[sample_order] = sample
    return scores


def build_rows(
    manifests: list[dict],
    scores_by_order: dict[int, dict],
    samples_per_prompt: int,
    first_sample_order: int,
) -> list[dict]:
    rows = []
    for manifest in manifests:
        prompt_round = manifest.get("prompt_round")
        if not isinstance(prompt_round, int):
            continue
        prompt_file = manifest.get("prompt_file", "")

        for sample in manifest.get("samples", []):
            sample_index = sample.get("sample_index")
            if not isinstance(sample_index, int):
                continue

            sample_order = first_sample_order + (prompt_round - 1) * samples_per_prompt + (sample_index - 1)
            score_data = scores_by_order.get(sample_order, {})
            score = score_data.get("score")
            has_score = score is not None
            accepted_for_eval = bool(sample.get("accepted_for_eval", True))
            sample_time = score_data.get("sample_time")
            evaluate_time = score_data.get("evaluate_time")
            status_from_score = score_data.get("status")
            if not accepted_for_eval:
                failure_reason = "rejected_pre_eval"
                status = "DEDUP_INTERCEPTED"
            elif has_score:
                failure_reason = ""
                status = "SUCCESS"
            else:
                status = status_from_score or "EVAL_FAILED"
                if status == "DEDUP_INTERCEPTED":
                    failure_reason = "dedup_intercepted"
                else:
                    failure_reason = "eval_failed_unknown"

            rows.append(
                {
                    "prompt_round": prompt_round,
                    "sample_index": sample_index,
                    "sample_order": sample_order,
                    "score": score,
                    "has_score": has_score,
                    "accepted_for_eval": accepted_for_eval,
                    "failure_reason": failure_reason,
                    "status": status,
                    "sample_time": sample_time,
                    "evaluate_time": evaluate_time,
                    "prompt_file": prompt_file,
                    "raw_file": sample.get("raw_file", ""),
                    "trimmed_file": sample.get("trimmed_file", ""),
                    "raw_length": sample.get("raw_length", ""),
                    "trimmed_length": sample.get("trimmed_length", ""),
                    "function": score_data.get("function", ""),
                }
            )
    return rows


def write_csv(rows: list[dict], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    headers = [
        "prompt_round",
        "sample_index",
        "sample_order",
        "score",
        "has_score",
        "accepted_for_eval",
        "failure_reason",
        "status",
        "sample_time",
        "evaluate_time",
        "prompt_file",
        "raw_file",
        "trimmed_file",
        "raw_length",
        "trimmed_length",
        "function",
    ]
    with output_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser(description="Merge FunSearch raw sample manifests with evaluated scores.")
    parser.add_argument(
        "--raw-samples-dir",
        default="logs/funsearch_llm_api/raw_samples",
        help="Directory containing sample_*_manifest.json files.",
    )
    parser.add_argument(
        "--scores-dir",
        default="logs/funsearch_llm_api/samples",
        help="Directory containing samples_*.json evaluator outputs.",
    )
    parser.add_argument(
        "--output",
        default="logs/funsearch_llm_api/merged_samples.csv",
        help="Output CSV path.",
    )
    parser.add_argument(
        "--samples-per-prompt",
        type=int,
        default=4,
        help="Configured samples_per_prompt used during run.",
    )
    parser.add_argument(
        "--first-sample-order",
        type=int,
        default=2,
        help="Global sample order of the first generated sample (default 2).",
    )
    args = parser.parse_args()

    manifests_dir = Path(args.raw_samples_dir)
    scores_dir = Path(args.scores_dir)
    output_path = Path(args.output)

    manifests = load_manifests(manifests_dir)
    scores = load_scores(scores_dir)
    rows = build_rows(
        manifests,
        scores,
        samples_per_prompt=args.samples_per_prompt,
        first_sample_order=args.first_sample_order,
    )
    write_csv(rows, output_path)

    print(f"Merged {len(rows)} rows -> {output_path}")


if __name__ == "__main__":
    main()
