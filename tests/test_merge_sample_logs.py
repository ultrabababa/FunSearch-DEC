import json
from pathlib import Path

from tools.merge_sample_logs import build_rows, load_manifests, load_scores


def test_build_rows_maps_manifest_samples_to_sample_orders(tmp_path: Path):
    manifests_dir = tmp_path / "raw_samples"
    scores_dir = tmp_path / "samples"
    manifests_dir.mkdir()
    scores_dir.mkdir()

    manifest = {
        "prompt_round": 1,
        "samples_per_prompt": 4,
        "prompt_file": "raw_samples/sample_00001_prompt.txt",
        "samples": [
            {
                "sample_index": 1,
                "raw_file": "raw_samples/sample_00001_01_raw.txt",
                "trimmed_file": "raw_samples/sample_00001_01_trimmed.txt",
            },
            {
                "sample_index": 2,
                "raw_file": "raw_samples/sample_00001_02_raw.txt",
                "trimmed_file": "raw_samples/sample_00001_02_trimmed.txt",
            },
        ],
    }
    (manifests_dir / "sample_00001_manifest.json").write_text(json.dumps(manifest), encoding="utf-8")

    score_sample_2 = {
        "sample_order": 2,
        "score": -212.75,
        "function": "def priority(...):\n    return bins",
        "status": "SUCCESS",
        "sample_time": 1.2,
        "evaluate_time": 2.3,
    }
    (scores_dir / "samples_2.json").write_text(json.dumps(score_sample_2), encoding="utf-8")

    manifests = load_manifests(manifests_dir)
    scores = load_scores(scores_dir)
    rows = build_rows(manifests, scores, samples_per_prompt=4, first_sample_order=2)

    assert len(rows) == 2
    assert rows[0]["sample_order"] == 2
    assert rows[0]["score"] == -212.75
    assert rows[0]["has_score"] is True
    assert rows[0]["failure_reason"] == ""
    assert rows[0]["status"] == "SUCCESS"
    assert rows[0]["sample_time"] == 1.2
    assert rows[0]["evaluate_time"] == 2.3

    assert rows[1]["sample_order"] == 3
    assert rows[1]["score"] is None
    assert rows[1]["has_score"] is False
    assert rows[1]["failure_reason"] == "eval_failed_unknown"
    assert rows[1]["status"] == "EVAL_FAILED"


def test_build_rows_marks_rejected_samples_with_reason(tmp_path: Path):
    manifests_dir = tmp_path / "raw_samples"
    scores_dir = tmp_path / "samples"
    manifests_dir.mkdir()
    scores_dir.mkdir()

    manifest = {
        "prompt_round": 1,
        "samples_per_prompt": 1,
        "prompt_file": "raw_samples/sample_00001_prompt.txt",
        "samples": [
            {
                "sample_index": 1,
                "raw_file": "raw_samples/sample_00001_01_raw.txt",
                "trimmed_file": "raw_samples/sample_00001_01_trimmed.txt",
                "accepted_for_eval": False,
            }
        ],
    }
    (manifests_dir / "sample_00001_manifest.json").write_text(json.dumps(manifest), encoding="utf-8")

    manifests = load_manifests(manifests_dir)
    scores = load_scores(scores_dir)
    rows = build_rows(manifests, scores, samples_per_prompt=1, first_sample_order=2)

    assert len(rows) == 1
    assert rows[0]["score"] is None
    assert rows[0]["accepted_for_eval"] is False
    assert rows[0]["failure_reason"] == "rejected_pre_eval"
    assert rows[0]["status"] == "DEDUP_INTERCEPTED"


def test_build_rows_marks_dedup_intercepted_from_score_status(tmp_path: Path):
    manifests_dir = tmp_path / "raw_samples"
    scores_dir = tmp_path / "samples"
    manifests_dir.mkdir()
    scores_dir.mkdir()

    manifest = {
        "prompt_round": 1,
        "samples_per_prompt": 1,
        "prompt_file": "raw_samples/sample_00001_prompt.txt",
        "samples": [
            {
                "sample_index": 1,
                "raw_file": "raw_samples/sample_00001_01_raw.txt",
                "trimmed_file": "raw_samples/sample_00001_01_trimmed.txt",
                "accepted_for_eval": True,
            }
        ],
    }
    (manifests_dir / "sample_00001_manifest.json").write_text(json.dumps(manifest), encoding="utf-8")

    score_sample_2 = {
        "sample_order": 2,
        "score": None,
        "status": "DEDUP_INTERCEPTED",
    }
    (scores_dir / "samples_2.json").write_text(json.dumps(score_sample_2), encoding="utf-8")

    manifests = load_manifests(manifests_dir)
    scores = load_scores(scores_dir)
    rows = build_rows(manifests, scores, samples_per_prompt=1, first_sample_order=2)

    assert len(rows) == 1
    assert rows[0]["status"] == "DEDUP_INTERCEPTED"
    assert rows[0]["failure_reason"] == "dedup_intercepted"
