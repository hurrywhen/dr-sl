"""Automatic taxonomy-coverage tests (round 5, protocol v5 §1.1/§4).

Pins the disclosure so manual statements cannot silently drift again:
- compares every dataset's gold type set against the round-4 frozen declared
  taxonomy and asserts the DOCUMENTED per-dataset omission sets;
- asserts the complete taxonomy (TYPES_V2) covers every dataset incl. holdout-4;
- asserts prompt v2 differs from the round-4 prompt by exactly the three added
  type declarations;
- asserts the localization algorithm is unchanged;
- asserts holdout-4 actually contains the three previously omitted types
  (non-vacuous validation) and the subset selection rule.
No API calls.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "dataset"))

from qi import load_dataset
from revision_neural_extractor import EXTRACT_SYSTEM, TYPES, locate
from revision_neural_round5 import (CONDITIONS, EXTRACT_SYSTEM_V2, TYPES_V2,
                                    locate_with_types, select_subset)
from revision_neural_analysis import DOCUMENTED_OMISSIONS

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "dataset" / "output"
OMITTED_THREE = {"room_no", "marriage_years", "work_years"}

ALL_FILES = {
    "holdout80": "dr_sl_holdout_v1.jsonl",
    "holdout80_v2": "dr_sl_holdout_v2.jsonl",
    "holdout80_v3": "dr_sl_holdout_v3.jsonl",
    "holdout80_v4": "dr_sl_holdout_v4.jsonl",
    "drift_p000": "dr_sl_drift_p000.jsonl",
    "drift_p025": "dr_sl_drift_p025.jsonl",
    "drift_p050": "dr_sl_drift_p050.jsonl",
    "drift_p075": "dr_sl_drift_p075.jsonl",
    "drift_p100": "dr_sl_drift_p100.jsonl",
}


def gold_types(fname):
    ts = set()
    for it in load_dataset(str(OUT / fname)):
        for e in (it["annotations"]["explicit_identifiers"]
                  + it["annotations"]["quasi_identifiers"]):
            ts.add(e["type"])
    return ts


def test_round4_omissions_are_exactly_three():
    """The round-4 taxonomy omits room_no/marriage_years/work_years on the
    family-#1 datasets and drift series; holdout-3 is fully declared."""
    for ds, fname in ALL_FILES.items():
        omitted = gold_types(fname) - TYPES
        if ds in DOCUMENTED_OMISSIONS:
            assert omitted == DOCUMENTED_OMISSIONS[ds], (ds, omitted)
        elif ds == "holdout80_v4":
            assert omitted == OMITTED_THREE, (ds, omitted)  # h4 uses family-#4 types
        else:
            assert omitted == OMITTED_THREE, (ds, omitted)
    assert OMITTED_THREE <= set().union(*(gold_types(f) for f in ALL_FILES.values()))
    print("test_round4_omissions_are_exactly_three OK (9 datasets)")


def test_complete_taxonomy_covers_everything():
    assert TYPES_V2 == TYPES | OMITTED_THREE
    assert len(TYPES_V2) == 43
    for ds, fname in ALL_FILES.items():
        assert gold_types(fname) <= TYPES_V2, (ds, gold_types(fname) - TYPES_V2)
    print("test_complete_taxonomy_covers_everything OK (43 types, 9 datasets)")


def test_prompt_v2_minimal_delta():
    added = "children_count(孩子个数), room_no(房间号), marriage_years(婚龄), work_years(工作年限)。"
    assert EXTRACT_SYSTEM.count("children_count(孩子个数)。") == 1
    assert EXTRACT_SYSTEM_V2.replace(added, "children_count(孩子个数)。") == EXTRACT_SYSTEM
    for t in ("room_no(房间号)", "marriage_years(婚龄)", "work_years(工作年限)"):
        assert t in EXTRACT_SYSTEM_V2
    print("test_prompt_v2_minimal_delta OK")


def test_localization_unchanged():
    text = "客户张三申请150000元，房号954，婚龄8年，工作18年。"
    props = [("name", "张三"), ("amount", "150000元"), ("room_no", "954"),
             ("marriage_years", "8年"), ("work_years", "18年"), ("bogus", "张三")]
    assert locate(text, props) == locate_with_types(text, props, TYPES)
    ents, unloc, unknown = locate_with_types(text, props, TYPES_V2)
    assert unknown == 1 and unloc == 0
    assert {e["type"] for e in ents} == {"name", "amount", "room_no", "marriage_years", "work_years"}
    print("test_localization_unchanged OK")


def test_holdout4_non_vacuous():
    from collections import Counter
    cnt = Counter()
    n = 0
    for it in load_dataset(str(OUT / "dr_sl_holdout_v4.jsonl")):
        n += 1
        for e in (it["annotations"]["explicit_identifiers"]
                  + it["annotations"]["quasi_identifiers"]):
            cnt[e["type"]] += 1
    assert n == 80
    for t in OMITTED_THREE:
        assert cnt[t] >= 5, (t, cnt[t])  # validation must exercise the omitted types
    print(f"test_holdout4_non_vacuous OK (room_no={cnt['room_no']}, "
          f"work_years={cnt['work_years']}, marriage_years={cnt['marriage_years']})")


def test_subset_selection():
    sub = select_subset()
    assert len(sub) == 60
    from collections import Counter
    per_ds = Counter(ds for ds, _ in sub)
    assert per_ds == {"holdout80": 20, "holdout80_v3": 20, "drift_p000": 20}
    per_dom = Counter((ds, it["domain"]) for ds, it in sub)
    assert all(v == 5 for v in per_dom.values())
    # deterministic: first 5 per domain in sorted-id order
    for ds, fname in (("holdout80", "dr_sl_holdout_v1.jsonl"),):
        items = {it["id"]: it for it in load_dataset(str(OUT / fname))}
        for dom in {it["domain"] for it in items.values()}:
            expect = sorted(i for i in items if items[i]["domain"] == dom)[:5]
            got = sorted(it["id"] for d, it in sub if d == ds and it["domain"] == dom)
            assert got == expect
    print("test_subset_selection OK (60 instances, 5/domain/dataset)")


def test_conditions_pre_registered():
    assert CONDITIONS["stability_r1"]["seed"] == 20261126
    assert CONDITIONS["stability_r2"]["seed"] == 20261127
    assert CONDITIONS["family_glm"]["seed"] == 20261128
    assert CONDITIONS["h4_complete"]["seed"] == 20261129
    for c in ("stability_r1", "stability_r2", "family_glm"):
        assert CONDITIONS[c]["prompt"] == EXTRACT_SYSTEM  # byte-identical round-4 prompt
        assert CONDITIONS[c]["types"] == TYPES
    assert CONDITIONS["h4_complete"]["prompt"] == EXTRACT_SYSTEM_V2
    assert CONDITIONS["h4_complete"]["types"] == TYPES_V2
    assert CONDITIONS["family_glm"]["role"] == "online_alt"  # second family (GLM)
    print("test_conditions_pre_registered OK")


if __name__ == "__main__":
    test_round4_omissions_are_exactly_three()
    test_complete_taxonomy_covers_everything()
    test_prompt_v2_minimal_delta()
    test_localization_unchanged()
    test_holdout4_non_vacuous()
    test_subset_selection()
    test_conditions_pre_registered()
    print("ALL NEURAL TAXONOMY TESTS PASSED")
