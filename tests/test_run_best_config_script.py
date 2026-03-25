import subprocess
from pathlib import Path


def test_run_best_config_script_help() -> None:
    project_root = Path(__file__).resolve().parents[1]
    result = subprocess.run(
        ["python", "tools/run_best_config_pipeline.py", "--help"],
        cwd=project_root,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert "Run tuned OR3/Weibull pipeline" in result.stdout
