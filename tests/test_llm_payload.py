from funsearch_bin_packing_llm_api import (
    _build_chat_payload,
    _resolve_disable_thinking,
    _trim_preface_of_body,
)


def test_build_chat_payload_disables_thinking_with_both_modes():
    payload = _build_chat_payload(prompt="hello", model="qwen", disable_thinking=True, thinking_mode="both")

    assert payload["model"] == "qwen"
    assert payload["messages"][0]["role"] == "system"
    assert payload["messages"][1]["content"] == "hello"
    assert payload["chat_template_kwargs"]["enable_thinking"] is False
    assert payload["enable_thinking"] is False


def test_build_chat_payload_uses_chat_template_mode_only():
    payload = _build_chat_payload(prompt="hello", model="qwen", disable_thinking=True, thinking_mode="chat_template")

    assert payload["chat_template_kwargs"]["enable_thinking"] is False
    assert "enable_thinking" not in payload


def test_build_chat_payload_uses_alibaba_mode_only():
    payload = _build_chat_payload(prompt="hello", model="qwen", disable_thinking=True, thinking_mode="alibaba")

    assert payload["enable_thinking"] is False
    assert "chat_template_kwargs" not in payload


def test_build_chat_payload_omits_thinking_controls_when_disabled():
    payload = _build_chat_payload(prompt="hello", model="qwen", disable_thinking=False, thinking_mode="both")

    assert "chat_template_kwargs" not in payload
    assert "enable_thinking" not in payload


def test_resolve_disable_thinking_auto_for_qwen35_model():
    assert _resolve_disable_thinking("auto", "qwen3.5-27b") is True


def test_resolve_disable_thinking_auto_for_coder_instruct_model():
    assert _resolve_disable_thinking("auto", "qwen3-coder-30b-a3b-instruct") is False


def test_trim_preface_rejects_obviously_truncated_body():
    sample = """
def priority(item: float, bins: np.ndarray) -> np.ndarray:
    if item <= 0:
        return np.zeros_like(bins)
    for i in range(len(bins)):
        if bins[i] > 0:
            priorities[i] = 1.0
    if item > 0.5:
        priorities[i] =
"""
    assert _trim_preface_of_body(sample) == ""


def test_trim_preface_accepts_complete_body():
    sample = """
def priority(item: float, bins: np.ndarray) -> np.ndarray:
    priorities = np.zeros_like(bins)
    if item <= 0:
        return priorities
    for i in range(len(bins)):
        priorities[i] = bins[i] - item
    return priorities
"""
    trimmed = _trim_preface_of_body(sample)
    assert "return priorities" in trimmed
