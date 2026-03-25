from funsearch_bin_packing_llm_api import _resolve_proxy_endpoint


def test_resolve_proxy_endpoint_http():
    host, port = _resolve_proxy_endpoint("http://127.0.0.1:7897")
    assert host == "127.0.0.1"
    assert port == 7897


def test_resolve_proxy_endpoint_https_default_port():
    host, port = _resolve_proxy_endpoint("https://proxy.example.com")
    assert host == "proxy.example.com"
    assert port == 443
