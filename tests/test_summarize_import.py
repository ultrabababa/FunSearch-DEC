import subprocess
from pathlib import Path


def test_summarize_script_imports_when_run_as_file(tmp_path: Path):
    project_root = Path(__file__).resolve().parents[1]
    cmd = [
        "python",
        "tools/summarize_experiment_matrix.py",
        "--dataset",
        "OR3",
        "--repeats",
        "1",
    ]
    result = subprocess.run(cmd, cwd=project_root, capture_output=True, text=True)
    assert "ModuleNotFoundError" not in result.stderr
