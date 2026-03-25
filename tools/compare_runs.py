import argparse
import csv
import json
from pathlib import Path


def _to_float(value) -> float | None:
    if value in (None, "", "None"):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _to_bool(value) -> bool | None:
    if isinstance(value, bool):
        return value
    if value is None:
        return None
    if isinstance(value, str):
        v = value.strip().lower()
        if v in ("true", "1", "yes"):
            return True
        if v in ("false", "0", "no"):
            return False
    return None


def _is_dedup_intercepted(row: dict) -> bool:
    accepted_for_eval = _to_bool(row.get("accepted_for_eval"))
    return (
        accepted_for_eval is False
        or row.get("failure_reason") in ("rejected_pre_eval", "dedup_intercepted")
        or row.get("status") == "DEDUP_INTERCEPTED"
    )


def _ordered_rows(rows: list[dict]) -> list[dict]:
    ordered = []
    for row in rows:
        sample_order = row.get("sample_order", "")
        try:
            idx = int(sample_order)
        except (TypeError, ValueError):
            continue
        ordered.append((idx, row))
    ordered.sort(key=lambda x: x[0])
    return [row for _, row in ordered]


def _to_target_metrics(rows: list[dict], target_score: float) -> dict:
    best_so_far = float("-inf")
    llm_calls = 0
    sandbox_evals = 0
    sample_time_sum = 0.0
    evaluate_time_sum = 0.0

    for row in _ordered_rows(rows):
        llm_calls += 1
        sample_time = _to_float(row.get("sample_time"))
        evaluate_time = _to_float(row.get("evaluate_time"))
        if sample_time is not None:
            sample_time_sum += sample_time
        if evaluate_time is not None:
            evaluate_time_sum += evaluate_time

        if not _is_dedup_intercepted(row):
            sandbox_evals += 1

        score = _to_float(row.get("score"))
        if score is not None and score > best_so_far:
            best_so_far = score

        if best_so_far >= target_score:
            return {
                "target_score": target_score,
                "target_reached": True,
                "calls_to_target": llm_calls,
                "sandbox_evals_to_target": sandbox_evals,
                "sample_time_to_target_sec": sample_time_sum,
                "evaluate_time_to_target_sec": evaluate_time_sum,
                "pipeline_time_to_target_sec": sample_time_sum + evaluate_time_sum,
                "best_score_seen": best_so_far,
            }

    return {
        "target_score": target_score,
        "target_reached": False,
        "calls_to_target": None,
        "sandbox_evals_to_target": None,
        "sample_time_to_target_sec": None,
        "evaluate_time_to_target_sec": None,
        "pipeline_time_to_target_sec": None,
        "best_score_seen": None if best_so_far == float("-inf") else best_so_far,
    }


def summarize(csv_path: Path, dedup_stats_path: Path | None = None, target_score: float | None = None) -> dict:
    if not csv_path.exists():
        raise FileNotFoundError(f"Input CSV not found: {csv_path}")
    rows = list(csv.DictReader(csv_path.open('r', encoding='utf-8')))
    total = len(rows)
    scored_rows = [r for r in rows if _to_float(r.get('score')) is not None]
    scored = len(scored_rows)
    failed = total - scored
    scored_values = [_to_float(r.get('score')) for r in scored_rows]
    scored_values = [v for v in scored_values if v is not None]
    best_score = max(scored_values, default=None)
    dedup_hits = sum(1 for r in rows if _is_dedup_intercepted(r))
    eval_failed = sum(
        1
        for r in rows
        if r.get('status') == 'EVAL_FAILED' or r.get('failure_reason') == 'eval_failed_unknown'
    )
    llm_calls = total
    sandbox_evals = sum(1 for r in rows if not _is_dedup_intercepted(r))
    total_sample_time_sec = sum(_to_float(r.get('sample_time')) or 0.0 for r in rows)
    total_evaluate_time_sec = sum(_to_float(r.get('evaluate_time')) or 0.0 for r in rows)

    dedup_stats = {}
    if dedup_stats_path and dedup_stats_path.exists():
        dedup_stats = json.loads(dedup_stats_path.read_text(encoding='utf-8'))
        # Prefer runtime sandbox counters over csv heuristics.
        dedup_hits = int(dedup_stats.get('dedup_hit', dedup_hits))
        # Runtime dedup counter is the most reliable source when available.
        sandbox_evals = max(0, llm_calls - dedup_hits)

    stage2_recheck = dedup_stats.get('stage2_recheck')
    stage2_reject = dedup_stats.get('stage2_reject')
    stage2_collision_reject_rate = None
    if isinstance(stage2_recheck, int) and stage2_recheck > 0 and isinstance(stage2_reject, int):
        stage2_collision_reject_rate = stage2_reject / stage2_recheck

    to_target = {}
    if target_score is not None:
        to_target = _to_target_metrics(rows, target_score)

    return {
        'csv': str(csv_path),
        'total_rows': total,
        'llm_calls': llm_calls,
        'sandbox_evals': sandbox_evals,
        'scored_rows': scored,
        'failed_rows': failed,
        'dedup_hits': dedup_hits,
        'dedup_intercept_rate': (dedup_hits / llm_calls) if llm_calls else None,
        'eval_failed': eval_failed,
        'best_score': best_score,
        'total_sample_time_sec': total_sample_time_sec,
        'total_evaluate_time_sec': total_evaluate_time_sec,
        'total_pipeline_time_sec': total_sample_time_sec + total_evaluate_time_sec,
        'stage2_collision_reject_rate': stage2_collision_reject_rate,
        'dedup_stats': dedup_stats,
        **to_target,
    }


def print_summary(tag: str, s: dict) -> None:
    print(f'[{tag}]')
    print(f"  csv: {s['csv']}")
    print(f"  total_rows: {s['total_rows']}")
    print(f"  llm_calls: {s['llm_calls']}")
    print(f"  sandbox_evals: {s['sandbox_evals']}")
    print(f"  scored_rows: {s['scored_rows']}")
    print(f"  failed_rows: {s['failed_rows']}")
    print(f"  dedup_hits: {s['dedup_hits']}")
    print(f"  dedup_intercept_rate: {s['dedup_intercept_rate']}")
    print(f"  eval_failed: {s['eval_failed']}")
    print(f"  best_score: {s['best_score']}")
    print(f"  total_sample_time_sec: {s['total_sample_time_sec']}")
    print(f"  total_evaluate_time_sec: {s['total_evaluate_time_sec']}")
    print(f"  total_pipeline_time_sec: {s['total_pipeline_time_sec']}")
    if 'target_score' in s:
        print(f"  target_score: {s['target_score']}")
        print(f"  target_reached: {s['target_reached']}")
        print(f"  calls_to_target: {s['calls_to_target']}")
        print(f"  sandbox_evals_to_target: {s['sandbox_evals_to_target']}")
        print(f"  pipeline_time_to_target_sec: {s['pipeline_time_to_target_sec']}")


def main() -> None:
    parser = argparse.ArgumentParser(description='Compare baseline and dedup run summaries')
    parser.add_argument('--baseline-csv', required=True)
    parser.add_argument('--dedup-csv', required=True)
    parser.add_argument('--baseline-dedup-stats', default='')
    parser.add_argument('--dedup-dedup-stats', default='')
    parser.add_argument('--output-json', default='')
    parser.add_argument('--target-score', type=float, default=None)
    args = parser.parse_args()

    baseline_stats = Path(args.baseline_dedup_stats) if args.baseline_dedup_stats else None
    dedup_stats = Path(args.dedup_dedup_stats) if args.dedup_dedup_stats else None
    try:
        baseline = summarize(Path(args.baseline_csv), baseline_stats, target_score=args.target_score)
        dedup = summarize(Path(args.dedup_csv), dedup_stats, target_score=args.target_score)
    except FileNotFoundError as e:
        raise SystemExit(str(e))

    print_summary('BASELINE', baseline)
    print_summary('DEDUP', dedup)

    if args.output_json:
        out = {
            'baseline': baseline,
            'dedup': dedup,
            'delta': {
                'scored_rows_diff': dedup['scored_rows'] - baseline['scored_rows'],
                'failed_rows_diff': dedup['failed_rows'] - baseline['failed_rows'],
                'dedup_hits_diff': dedup['dedup_hits'] - baseline['dedup_hits'],
                'llm_calls_diff': dedup['llm_calls'] - baseline['llm_calls'],
                'sandbox_evals_diff': dedup['sandbox_evals'] - baseline['sandbox_evals'],
                'best_score_diff': None
                if baseline['best_score'] is None or dedup['best_score'] is None
                else dedup['best_score'] - baseline['best_score'],
            },
        }
        Path(args.output_json).write_text(json.dumps(out, indent=2), encoding='utf-8')
        print(f'Wrote comparison JSON: {args.output_json}')


if __name__ == '__main__':
    main()
