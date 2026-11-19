"""The hand-check sample must stay reproducible & fully labelled."""
import json
import sys

from run_suite import ROOT

sys.path.insert(0, str(ROOT / "review"))


def test_sample_is_thirty_seeded_mutants_and_all_are_labelled():
    from sample import SAMPLE_SIZE, draw_sample
    first, second = draw_sample(), draw_sample()
    assert first == second and len(first) == SAMPLE_SIZE == 30
    labels = json.loads((ROOT / "review" / "hand_labels.json").read_text())["random_sample"]
    assert {f"{task}/{m.id}" for task, m in first} == set(labels)
    for info in labels.values():
        assert info["label"] in ("bug", "equivalent") and len(info["reason"]) > 10


def test_sample_spans_many_tasks():
    from sample import draw_sample
    assert len({task for task, _ in draw_sample()}) >= 8
