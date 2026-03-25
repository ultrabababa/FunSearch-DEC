from tools.run_experiment_matrix import _apply_cloud_env_mapping


def test_apply_cloud_env_mapping_populates_llm_vars_from_cloud_env(monkeypatch):
    monkeypatch.setenv("FUNSEARCH_CLOUD_BASE_URL", "https://api.bltcy.ai")
    monkeypatch.setenv("FUNSEARCH_CLOUD_MODEL", "gpt-5-nano")
    monkeypatch.setenv("FUNSEARCH_CLOUD_API_KEY", "k-test")
    monkeypatch.delenv("FUNSEARCH_LLM_HOST", raising=False)
    monkeypatch.delenv("FUNSEARCH_LLM_PATH", raising=False)
    monkeypatch.delenv("FUNSEARCH_LLM_MODEL", raising=False)
    monkeypatch.delenv("FUNSEARCH_LLM_USE_HTTPS", raising=False)
    monkeypatch.delenv("FUNSEARCH_LLM_API_KEY", raising=False)

    _apply_cloud_env_mapping()

    import os

    assert os.getenv("FUNSEARCH_LLM_HOST") == "api.bltcy.ai"
    assert os.getenv("FUNSEARCH_LLM_PATH") == "/v1/chat/completions"
    assert os.getenv("FUNSEARCH_LLM_MODEL") == "gpt-5-nano"
    assert os.getenv("FUNSEARCH_LLM_USE_HTTPS") == "1"
    assert os.getenv("FUNSEARCH_LLM_API_KEY") == "k-test"
