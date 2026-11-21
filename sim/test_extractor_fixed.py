"""Tests for the fixed-contrast extractor (round 3, protocol v3 §3).

Verifies each clear-defect fix and that the fixes do not degrade name recall on
the frozen holdout-1.  The original extractor must remain unchanged.
"""
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "sim"))
sys.path.insert(0, str(ROOT / "dataset"))

from qi import load_dataset
from runtime_extractor import runtime_extract
from runtime_extractor_fixed import runtime_extract_fixed


def _vals(ents, typ):
    return {e["value"] for e in ents if e["type"] == typ}


def test_money_wired():
    ents = runtime_extract_fixed("申请金额：150000元，手续费15元。")
    assert "150000元" in _vals(ents, "amount")
    assert "15元" in _vals(ents, "charge")
    # original never extracts money (defined-but-unused pattern)
    assert not _vals(runtime_extract("申请金额：150000元"), "amount")
    print("test_money_wired OK")


def test_email_ascii_local_part():
    ents = runtime_extract_fixed("联系邮箱abcdefgh@example.org。")
    assert "abcdefgh@example.org" in _vals(ents, "email")
    # original over-matches the Chinese label prefix
    assert "联系邮箱abcdefgh@example.org" in _vals(runtime_extract("联系邮箱abcdefgh@example.org。"), "email")
    print("test_email_ascii_local_part OK")


def test_allergy_forms():
    for text, want in (("过敏史：海鲜，目前用药二甲双胍", "海鲜"),
                       ("孩子对海鲜过敏。请推荐", "海鲜"),
                       ("，对牛奶过敏。", "牛奶")):
        assert want in _vals(runtime_extract_fixed(text), "allergy"), text
    print("test_allergy_forms OK")


def test_income_not_double_counted():
    ents = runtime_extract_fixed("收入情况：月收入约5000元")
    assert "月收入约5000元" in _vals(ents, "income")
    assert not _vals(ents, "amount")  # longer income span wins
    print("test_income_not_double_counted OK")


def test_name_recall_not_degraded():
    items = load_dataset(str(ROOT / "dataset/output/dr_sl_holdout_v1.jsonl"))
    for it in items:
        gold_names = {e["value"] for e in it["annotations"]["explicit_identifiers"]
                      if e["type"] == "name"}
        orig = _vals(runtime_extract(it["prompt"]), "name")
        fixed = _vals(runtime_extract_fixed(it["prompt"]), "name")
        assert gold_names & orig <= fixed, f"name recall degraded on {it['id']}"
    print("test_name_recall_not_degraded OK (80 instances)")


def test_original_extractor_frozen():
    m = json.loads((ROOT / "results/revision_20261121/freeze_manifest.json").read_text())
    key = "sim/runtime_extractor.py"
    cur = hashlib.sha256((ROOT / key).read_bytes()).hexdigest()
    assert cur == m[key], "original extractor was modified after round-2 freeze"
    print("test_original_extractor_frozen OK")


if __name__ == "__main__":
    test_money_wired()
    test_email_ascii_local_part()
    test_allergy_forms()
    test_income_not_double_counted()
    test_name_recall_not_degraded()
    test_original_extractor_frozen()
    print("ALL FIXED-EXTRACTOR TESTS PASSED")
