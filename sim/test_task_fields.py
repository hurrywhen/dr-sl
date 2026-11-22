"""Task-field isolation tests (round-3 P0 fix, revision_protocol_v3.md §2).

The downstream experiment must use the explicit `task` field, never a
last-sentence heuristic.  These tests assert the field is a clean, short,
sensitive-free statement of the user request on every frozen holdout instance.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "dataset"))

from qi import load_dataset


def check_file(path, n_expected=80):
    items = load_dataset(str(path))
    assert len(items) == n_expected
    for it in items:
        task = it.get("task")
        assert task, f"missing task: {it['id']}"
        assert task != it["prompt"], f"task equals full prompt: {it['id']}"
        assert len(task) <= 0.5 * len(it["prompt"]), f"task too long: {it['id']}"
        gold = (it["annotations"]["explicit_identifiers"]
                + it["annotations"]["quasi_identifiers"])
        for e in gold:
            assert e["value"] not in task, f"task leaks gold value: {it['id']}"
        src = it.get("task_meta", {}).get("source")
        assert src in ("verbatim_request", "authored_dialogue_request")
        if src == "verbatim_request":
            assert task in it["prompt"]
    return len(items)


def test_holdout1_tasks():
    n = check_file(ROOT / "dataset/output/dr_sl_holdout_v1.jsonl")
    print(f"test_holdout1_tasks OK ({n} instances)")


def test_holdout2_tasks():
    n = check_file(ROOT / "dataset/output/dr_sl_holdout_v2.jsonl")
    print(f"test_holdout2_tasks OK ({n} instances)")


def test_holdout3_tasks():
    n = check_file(ROOT / "dataset/output/dr_sl_holdout_v3.jsonl")
    print(f"test_holdout3_tasks OK ({n} instances)")


def test_drift_series_tasks():
    total = 0
    for tag in ("p000", "p025", "p050", "p075", "p100"):
        total += check_file(ROOT / f"dataset/output/dr_sl_drift_{tag}.jsonl", n_expected=40)
    print(f"test_drift_series_tasks OK ({total} instances across 5 levels)")


def test_last_sentence_heuristic_was_unsafe():
    """Documents the round-2 contamination: the old heuristic returned (nearly)
    the full prompt for single-sentence field-list templates."""
    import re
    items = load_dataset(str(ROOT / "dataset/output/dr_sl_holdout_v1.jsonl"))

    def old_extract_task(prompt):
        p = re.sub(r"补充说明：.*$", "", prompt, flags=re.S).strip()
        sentences = [s.strip() for s in re.split(r"(?<=[。？])", p) if s.strip()]
        return sentences[-1] if sentences else p

    contaminated = [it["id"] for it in items
                    if len(old_extract_task(it["prompt"])) > 0.6 * len(it["prompt"])]
    assert len(contaminated) == 20  # 4 field-list templates x 5 instances
    print(f"test_last_sentence_heuristic_was_unsafe OK ({len(contaminated)} contaminated)")


if __name__ == "__main__":
    test_holdout1_tasks()
    test_holdout2_tasks()
    test_holdout3_tasks()
    test_drift_series_tasks()
    test_last_sentence_heuristic_was_unsafe()
    print("ALL TASK-FIELD TESTS PASSED")
