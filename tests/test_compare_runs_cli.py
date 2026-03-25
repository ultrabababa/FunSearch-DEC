import subprocess
from pathlib import Path


def test_compare_runs_reports_missing_input_files(tmp_path: Path):
    project_root = Path(__file__).resolve().parents[1]
    cmd = [
        "python",
        "tools/compare_runs.py",
        "--baseline-csv",
        "logs/funsearch_llm_api/not_exist_baseline.csv",
        "--dedup-csv",
        "logs/funsearch_llm_api/not_exist_dedup.csv",
    ]
    result = subprocess.run(cmd, cwd=project_root, capture_output=True, text=True)

    assert result.returncode != 0
    assert "input csv not found" in result.stderr.lower()
