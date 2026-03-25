import os
import runpy
from urllib.parse import urlparse


def _resolve_cloud_endpoint(base_url: str) -> tuple[str, bool, str]:
    parsed = urlparse(base_url if "://" in base_url else f"https://{base_url}")
    host = parsed.netloc
    if not host:
        raise ValueError(f"Invalid FUNSEARCH_CLOUD_BASE_URL: {base_url}")
    path = parsed.path.rstrip("/")
    if not path:
        path = "/v1/chat/completions"
    elif path == "/v1":
        path = "/v1/chat/completions"
    return host, parsed.scheme.lower() == "https", path


def _apply_cloud_env_defaults() -> None:
    base_url = os.getenv("FUNSEARCH_CLOUD_BASE_URL", "https://api.bltcy.ai")
    model = os.getenv("FUNSEARCH_CLOUD_MODEL", "gpt-5-nano")
    api_key = os.getenv("FUNSEARCH_CLOUD_API_KEY", "")

    host, use_https, path = _resolve_cloud_endpoint(base_url)

    os.environ.setdefault("FUNSEARCH_LLM_HOST", host)
    os.environ.setdefault("FUNSEARCH_LLM_USE_HTTPS", "1" if use_https else "0")
    os.environ.setdefault("FUNSEARCH_LLM_PATH", path)
    os.environ.setdefault("FUNSEARCH_LLM_MODEL", model)
    os.environ.setdefault("FUNSEARCH_LOG_DIR", "logs/funsearch_cloud_api")
    if api_key:
        os.environ.setdefault("FUNSEARCH_LLM_API_KEY", api_key)

    os.environ.setdefault("FUNSEARCH_DISABLE_THINKING", "auto")
    os.environ.setdefault("FUNSEARCH_THINKING_PARAM_MODE", "both")


if __name__ == "__main__":
    _apply_cloud_env_defaults()
    runpy.run_path("funsearch_bin_packing_llm_api.py", run_name="__main__")
