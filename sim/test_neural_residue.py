"""Round-6 regression tests for proposal/residue mechanisms (protocol v6).

No API calls.  Covers symmetric gold/proposal containment, repeated long/short
mentions, the three archived GLM fee cases, holdout-4 direct extraction evidence,
the definitional nature of complete-taxonomy FR_gap=0, and the additional
zero-charge sensitivity analysis.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "dataset"))

from revision_neural_analysis import classify_proposal_relation
from revision_neural_round5 import TYPES, locate_with_types
from runtime import external_gold_audit, run_runtime_item

ROOT = Path(__file__).resolve().parent.parent
R3 = ROOT / "results" / "revision_round3"


def test_five_proposal_relations():
    assert classify_proposal_relation(
        "city", "望海县", [("city", "望海县")])["kind"] == "exact_proposal"
    assert classify_proposal_relation(
        "income", "月收入约1.2万元", [("income", "1.2万元")])["kind"] == \
        "proposal_substring_of_gold"
    assert classify_proposal_relation(
        "charge", "0元", [("charge", "0元手续费")])["kind"] == \
        "gold_substring_of_proposal"
    assert classify_proposal_relation(
        "city", "望海县", [("hotel", "望海海景度假村")])["kind"] == \
        "related_but_noncontaining_proposal"
    assert classify_proposal_relation(
        "city", "望海县", [("hotel", "霜林山景酒店")])["kind"] == "never_proposed"
    # Incidental numeric substrings are retained as secondary matches, not
    # allowed to hide the same-type extended fee span.
    rel = classify_proposal_relation(
        "charge", "0元", [("amount", "160000元"), ("charge", "0元手续费")])
    assert rel["kind"] == "gold_substring_of_proposal"
    assert rel["matched_proposals"] == [{"type": "charge", "value": "0元手续费"}]
    assert rel["other_matching_proposals"] == [{"type": "amount", "value": "160000元"}]
    print("test_five_proposal_relations OK")


def test_repeated_long_short_mention_residue():
    prompt = ("客户：被收了0元手续费。请帮我核对这笔转账的风控要求。"
              "补充说明：前述0元情况请以本记录为准。")
    start = prompt.index("0元")
    item = {"id": "SYNTH-REPEAT-FEE", "domain": "banking", "prompt": prompt,
            "task": "请帮我核对这笔转账的风控要求。",
            "annotations": {"explicit_identifiers": [],
                            "quasi_identifiers": [
                                {"category": "quasi", "type": "charge", "value": "0元",
                                 "task_relevant": True, "span": [start, start + 2]}],
                            "combos": []}}
    ents, unlocatable, unknown = locate_with_types(
        prompt, [("charge", "0元手续费")], TYPES)
    assert not unlocatable and not unknown
    assert [(e["type"], e["value"]) for e in ents] == [("charge", "0元手续费")]
    row = run_runtime_item(item, method="closed_loop", task_profile="mixed", entities=ents)
    assert "0元手续费" not in row["D"]  # extended span was scrubbed
    assert "前述0元情况" in row["D"]      # short repeated form remains
    audit = external_gold_audit(item, row["D"], ents)
    assert audit["gold_literal_hit_values"] == ["0元"]
    print("test_repeated_long_short_mention_residue OK")


def test_archived_glm_fee_classification():
    data = json.loads((R3 / "neural_round6_analysis.json").read_text())
    details = data["glm_zero_charge_repeated_mention"]
    assert len(details) == 3
    assert {d["id"] for d in details} == {
        "DRSL-H3-BAN-0001", "DRSL-H3-BAN-0003", "DRSL-H3-BAN-0005"}
    for d in details:
        assert d["relation"]["kind"] == "gold_substring_of_proposal"
        assert d["relation"]["matched_proposals"] == [
            {"type": "charge", "value": "0元手续费"}]
        assert not d["extended_span_in_artifact"]
        assert d["short_form_in_artifact"]
    summary = json.loads((R3 / "neural_round5_summary.json").read_text())
    misses = summary["conditions"]["family_glm"]["fr_decomposition"]["declared_miss_detail"]
    fees = [m for m in misses if m["type"] == "charge"]
    assert len(fees) == 3
    assert all(m["kind"] == "gold_substring_of_proposal" for m in fees)
    print("test_archived_glm_fee_classification OK")


def test_h4_direct_extraction_and_definitional_zero():
    data = json.loads((R3 / "neural_round6_analysis.json").read_text())
    h4 = data["holdout4"]
    assert h4["FR_gap_zero_is_performance_evidence"] is False
    assert h4["FR_taxonomy_gap"]["k"] == 0
    for typ in ("room_no", "marriage_years", "work_years"):
        b = h4["per_type_extraction_and_residue"][typ]
        assert (b["n_gold"], b["value_exact"], b["type_value_exact"],
                b["released_residue_instances"]) == (10, 10, 10, 0)
    city = h4["per_type_extraction_and_residue"]["city"]
    assert (city["n_gold"], city["value_exact"], city["type_value_exact"],
            city["released_residue_instances"]) == (60, 59, 54, 1)
    assert len(h4["city_type_label_variation"]) == 5
    assert h4["city_value_misses"] == [{"id": "DRSL-H4-TRA-0004", "value": "望海县"}]
    assert h4["city_explanation_identified"] is False
    print("test_h4_direct_extraction_and_definitional_zero OK")


def test_zero_charge_sensitivity_scope():
    data = json.loads((R3 / "neural_round6_analysis.json").read_text())
    assert data["primary_metric_unchanged"] is True
    for name, b in data["zero_charge_sensitivity"].items():
        primary = b["primary_FR_gold"]
        sensitivity = b["FR_excluding_zero_charge"]
        assert primary["n"] == sensitivity["n"]
        if name == "neural_round5_family_glm":
            assert (primary["k"], primary["n"]) == (5, 25)
            assert (sensitivity["k"], sensitivity["n"]) == (2, 25)
            assert b["residue_only_zero_charge"]["k"] == 3
        else:
            assert primary["k"] == sensitivity["k"], name
    print("test_zero_charge_sensitivity_scope OK")


if __name__ == "__main__":
    test_five_proposal_relations()
    test_repeated_long_short_mention_residue()
    test_archived_glm_fee_classification()
    test_h4_direct_extraction_and_definitional_zero()
    test_zero_charge_sensitivity_scope()
    print("ALL NEURAL RESIDUE TESTS PASSED")
