import argparse
import http.client
import json
import os
import sys
from pathlib import Path
from urllib.parse import urlparse


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from funsearch_bin_packing_cloud_api import _resolve_cloud_endpoint


def _resolve_proxy_endpoint(proxy_url: str) -> tuple[str, int]:
    parsed = urlparse(proxy_url if "://" in proxy_url else f"http://{proxy_url}")
    host = parsed.hostname
    if not host:
        raise ValueError(f"Invalid proxy URL: {proxy_url}")
    if parsed.port is not None:
        return host, parsed.port
    return host, 443 if parsed.scheme.lower() == "https" else 80


def main() -> int:
    parser = argparse.ArgumentParser(description="Quick check for cloud API configuration")
    parser.add_argument("--prompt", default="Reply with exactly: CLOUD_API_OK")
    parser.add_argument("--timeout", type=int, default=30)
    parser.add_argument("--max-tokens", type=int, default=64)
    parser.add_argument("--model", default="")
    args = parser.parse_args()

    api_key = os.getenv("FUNSEARCH_CLOUD_API_KEY", "").strip()
    base_url = os.getenv("FUNSEARCH_CLOUD_BASE_URL", "https://api.bltcy.ai").strip()
    model = (args.model or os.getenv("FUNSEARCH_CLOUD_MODEL", "gpt-5-nano")).strip()

    if not api_key:
        print("ERROR: FUNSEARCH_CLOUD_API_KEY is empty")
        return 2

    try:
        host, use_https, path = _resolve_cloud_endpoint(base_url)
    except ValueError as exc:
        print(f"ERROR: {exc}")
        return 2

    payload = {
        "model": model,
        "max_tokens": args.max_tokens,
        "messages": [
            {"role": "system", "content": "You are a concise assistant."},
            {"role": "user", "content": args.prompt},
        ],
    }
    payload_text = json.dumps(payload)
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "User-Agent": "funsearch-cloud-config-check/1.0",
    }

    proxy_url = os.getenv("HTTPS_PROXY" if use_https else "HTTP_PROXY", "").strip()
    if not proxy_url:
        proxy_url = os.getenv("https_proxy" if use_https else "http_proxy", "").strip()

    print("=== Effective Cloud API Config ===")
    print(f"FUNSEARCH_CLOUD_BASE_URL={base_url}")
    print(f"FUNSEARCH_CLOUD_MODEL={model}")
    print(f"resolved_host={host}")
    print(f"resolved_path={path}")
    print(f"resolved_https={use_https}")
    print(f"proxy={proxy_url or '<none>'}")
    print(f"timeout={args.timeout}s")
    print("==================================")

    try:
        if use_https and proxy_url:
            proxy_host, proxy_port = _resolve_proxy_endpoint(proxy_url)
            conn = http.client.HTTPConnection(proxy_host, proxy_port, timeout=args.timeout)
            conn.set_tunnel(host)
        else:
            conn_cls = http.client.HTTPSConnection if use_https else http.client.HTTPConnection
            conn = conn_cls(host, timeout=args.timeout)
        conn.request("POST", path, payload_text, headers)
        resp = conn.getresponse()
        raw = resp.read().decode("utf-8", errors="replace")
    except Exception as exc:
        print(f"REQUEST_ERROR: {repr(exc)}")
        return 1

    print(f"HTTP_STATUS={resp.status}")
    if resp.status < 200 or resp.status >= 300:
        print(raw[:1000])
        return 1

    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        print("ERROR: response is not valid JSON")
        print(raw[:1000])
        return 1

    content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
    usage = data.get("usage", {})
    print("RESPONSE_PREVIEW:")
    print((content or "").strip()[:300])
    print("USAGE:", usage)
    print("CLOUD_API_CONFIG_OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
