import os

from funsearch_bin_packing_llm_api import _resolve_log_dir


def test_resolve_log_dir_defaults_to_funsearch_llm_api(monkeypatch):
    monkeypatch.delenv("FUNSEARCH_LOG_DIR", raising=False)
    assert _resolve_log_dir() == "logs/funsearch_llm_api"


def test_resolve_log_dir_from_env_and_trim_trailing_slash(monkeypatch):
    monkeypatch.setenv("FUNSEARCH_LOG_DIR", "logs/custom_runtime/")
    assert _resolve_log_dir() == "logs/custom_runtime"
