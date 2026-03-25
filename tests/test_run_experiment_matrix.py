from pathlib import Path

from tools import run_experiment_matrix as rem


def test_run_one_removes_existing_runtime_dir(monkeypatch, tmp_path: Path):
    repo = tmp_path
    (repo / "logs" / "runtime" / "baseline_OR3_r1" / "raw_samples").mkdir(parents=True)
    (repo / "logs" / "runtime" / "baseline_OR3_r1" / "raw_samples" / "x.txt").write_text("x", encoding="utf-8")

    runtime_root = repo / "logs" / "runtime"
    out_runtime = runtime_root / "baseline_OR3_r1"
    out_exp = repo / "logs" / "experiments" / "baseline_OR3_r1"

    calls = []

    def fake_run_cmd(cmd, env, cwd):
        calls.append(cmd)
        cur_runtime = Path(env["FUNSEARCH_LOG_DIR"])
        cur_runtime.mkdir(parents=True, exist_ok=True)
        (cur_runtime / "raw_samples").mkdir(parents=True, exist_ok=True)
        (cur_runtime / "samples").mkdir(parents=True, exist_ok=True)
        (cur_runtime / "merged_samples.csv").write_text("a,b\n1,2\n", encoding="utf-8")
        return 0.01

    monkeypatch.setattr(rem, "run_cmd", fake_run_cmd)

    res = rem.run_one(repo, "baseline_OR3_r1", "OR3", False, 8)
    assert res == out_exp
    assert (out_exp / "merged_samples.csv").exists()
    assert (out_exp / "run_metrics.json").exists()
    assert runtime_root.exists()
    assert calls


def test_run_one_forces_sample_log_dir_under_runtime(monkeypatch, tmp_path: Path):
    repo = tmp_path
    out_exp = repo / "logs" / "experiments" / "baseline_OR3_r1"

    captured_env = {}

    def fake_run_cmd(cmd, env, cwd):
        captured_env.update(env)
        cur_runtime = Path(env["FUNSEARCH_LOG_DIR"])
        (cur_runtime / "raw_samples").mkdir(parents=True, exist_ok=True)
        (cur_runtime / "samples").mkdir(parents=True, exist_ok=True)
        (cur_runtime / "merged_samples.csv").write_text("a,b\n1,2\n", encoding="utf-8")
        return 0.01

    monkeypatch.setattr(rem, "run_cmd", fake_run_cmd)
    monkeypatch.setenv("FUNSEARCH_SAMPLE_LOG_DIR", "logs/funsearch_llm_api/raw_samples")

    rem.run_one(repo, "baseline_OR3_r1", "OR3", False, 8)

    assert captured_env["FUNSEARCH_SAMPLE_LOG_DIR"].endswith("/raw_samples")
    assert "baseline_OR3_r1_" in captured_env["FUNSEARCH_SAMPLE_LOG_DIR"]
    assert (out_exp / "merged_samples.csv").exists()
