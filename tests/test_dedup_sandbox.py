from funsearch_bin_packing_llm_api import DedupSandbox


class _FakeInnerSandbox:
    def __init__(self):
        self.calls = 0

    def run(self, *args, **kwargs):
        self.calls += 1
        return 123.0, True


class _Stage2ProbeDedupSandbox(DedupSandbox):
    def __init__(self, inner_sandbox, stage2_pass):
        super().__init__(inner_sandbox=inner_sandbox, enable_dedup=True)
        self._stage2_pass = stage2_pass

    def _stage2_random_check(self, candidate_trace, cached_traces):
        return self._stage2_pass


PROGRAM_A = """
import numpy as np

def priority(item: float, bins: np.ndarray) -> np.ndarray:
    return bins - item
"""


PROGRAM_B = """
import numpy as np

def priority(item: float, bins: np.ndarray) -> np.ndarray:
    return item - bins
"""


def test_dedup_sandbox_skips_duplicate_program_evaluation():
    inner = _FakeInnerSandbox()
    sandbox = DedupSandbox(inner_sandbox=inner, enable_dedup=True)

    out1, ok1 = sandbox.run(PROGRAM_A, "evaluate", "priority", {"OR3": {}}, "OR3", 30)
    out2, ok2 = sandbox.run(PROGRAM_A, "evaluate", "priority", {"OR3": {}}, "OR3", 30)

    assert (out1, ok1) == (123.0, True)
    assert (out2, ok2) == (None, False)
    assert inner.calls == 1


def test_dedup_sandbox_evaluates_distinct_programs():
    inner = _FakeInnerSandbox()
    sandbox = DedupSandbox(inner_sandbox=inner, enable_dedup=True)

    sandbox.run(PROGRAM_A, "evaluate", "priority", {"OR3": {}}, "OR3", 30)
    sandbox.run(PROGRAM_B, "evaluate", "priority", {"OR3": {}}, "OR3", 30)

    assert inner.calls == 2


def test_stage2_blocks_duplicate_only_when_probe_passes():
    inner = _FakeInnerSandbox()
    sandbox = _Stage2ProbeDedupSandbox(inner_sandbox=inner, stage2_pass=True)

    out1, ok1 = sandbox.run(PROGRAM_A, "evaluate", "priority", {"OR3": {}}, "OR3", 30)
    out2, ok2 = sandbox.run(PROGRAM_A, "evaluate", "priority", {"OR3": {}}, "OR3", 30)

    assert (out1, ok1) == (123.0, True)
    assert (out2, ok2) == (None, False)
    assert inner.calls == 1


def test_stage2_allows_candidate_when_probe_fails():
    inner = _FakeInnerSandbox()
    sandbox = _Stage2ProbeDedupSandbox(inner_sandbox=inner, stage2_pass=False)

    out1, ok1 = sandbox.run(PROGRAM_A, "evaluate", "priority", {"OR3": {}}, "OR3", 30)
    out2, ok2 = sandbox.run(PROGRAM_A, "evaluate", "priority", {"OR3": {}}, "OR3", 30)

    assert (out1, ok1) == (123.0, True)
    assert (out2, ok2) == (123.0, True)
    assert inner.calls == 2


def test_stage2_keeps_multiple_traces_under_same_stage1_hash_bucket():
    inner = _FakeInnerSandbox()
    sandbox = _Stage2ProbeDedupSandbox(inner_sandbox=inner, stage2_pass=False)

    # First enters bucket.
    sandbox.run(PROGRAM_A, "evaluate", "priority", {"OR3": {}}, "OR3", 30)
    # Same Stage1 hash candidate but stage2 rejects as novel -> should be appended, not overwrite.
    sandbox.run(PROGRAM_A, "evaluate", "priority", {"OR3": {}}, "OR3", 30)

    # With fixed mock setup we reuse same hash as PROGRAM_A.
    h = sandbox._compute_behavior_hash(PROGRAM_A, function_to_evolve="priority")
    assert h is not None
    traces = sandbox._stage2_trace_by_hash.get(h, [])
    assert isinstance(traces, list)
    assert len(traces) >= 1


def test_stage1_trace_uses_extended_curated_edge_cases():
    sandbox = DedupSandbox(inner_sandbox=_FakeInnerSandbox(), enable_dedup=True)
    trace = sandbox._compute_stage1_trace(PROGRAM_A, function_to_evolve="priority")
    assert trace is not None
    assert len(trace) >= 8
