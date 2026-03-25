from funsearch_bin_packing_cloud_api import _resolve_cloud_endpoint


def test_resolve_cloud_endpoint_defaults_to_chat_completions_path():
    host, use_https, path = _resolve_cloud_endpoint("https://api.bltcy.ai")
    assert host == "api.bltcy.ai"
    assert use_https is True
    assert path == "/v1/chat/completions"


def test_resolve_cloud_endpoint_keeps_custom_path_and_http_scheme():
    host, use_https, path = _resolve_cloud_endpoint("http://127.0.0.1:1234/custom")
    assert host == "127.0.0.1:1234"
    assert use_https is False
    assert path == "/custom"
