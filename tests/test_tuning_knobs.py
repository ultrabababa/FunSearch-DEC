from funsearch_bin_packing_llm_api import DedupSandbox


class _FakeInnerSandbox:
    def run(self, *args, **kwargs):
        return -1.0, True


def test_stage1_case_count_respects_env(monkeypatch):
    monkeypatch.setenv("FUNSEARCH_STAGE1_CASE_COUNT", "6")
    sandbox = DedupSandbox(inner_sandbox=_FakeInnerSandbox(), enable_dedup=True)
    assert len(sandbox._stage1_cases) == 6


def test_stage2_random_cases_respects_env(monkeypatch):
    monkeypatch.setenv("FUNSEARCH_STAGE2_RANDOM_CASES", "128")
    sandbox = DedupSandbox(inner_sandbox=_FakeInnerSandbox(), enable_dedup=True)
    assert sandbox._stage2_random_cases == 128
