import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "dataset"))

from distill import (memorization_check, build_refine_prompt, parse_rules,
                     degrade, DegradeLevels)


def test_memorization_rejects_literal_values():
    ok, reason = memorization_check("遇到年龄属性时应泛化为年龄档。",
                                    forbidden_values=["31岁", "张三"],
                                    source_texts=["我今年31岁。"])
    assert ok and reason == "pass"
    ok, reason = memorization_check("例如31岁应泛化为30多岁。",
                                    forbidden_values=["31岁"],
                                    source_texts=["我今年31岁。"])
    assert not ok and reason == "literal_value"
    print("test_memorization_rejects_literal_values OK")


def test_memorization_rejects_long_quotes():
    src = "这是一段比较长的原始材料文本用于测试引文检查是否生效的完整句子。"
    ok, reason = memorization_check("注意：" + src[:20] + " 这类表述要泛化。",
                                    forbidden_values=[], source_texts=[src], ell=16)
    assert not ok and reason == "long_quote"
    ok, reason = memorization_check("长文本材料需要整体泛化处理。",
                                    forbidden_values=[], source_texts=[src], ell=16)
    assert ok
    print("test_memorization_rejects_long_quotes OK")


def test_memorization_genscore():
    calls = []

    def scorer(rule):
        calls.append(rule)
        return 2

    ok, reason = memorization_check("规则内容", [], [], gen_scorer=scorer, gen_min=4)
    assert not ok and reason == "gen_score" and len(calls) == 1

    def scorer_ok(rule):
        return 5

    ok, reason = memorization_check("规则内容", [], [], gen_scorer=scorer_ok, gen_min=4)
    assert ok
    print("test_memorization_genscore OK")


def test_parse_rules():
    raw = '```json\n["规则一：年龄泛化为档位。", "规则二：地址只保留城市级别。"]\n```'
    rules = parse_rules(raw)
    assert rules == ["规则一：年龄泛化为档位。", "规则二：地址只保留城市级别。"]
    assert parse_rules("无法输出") == []
    print("test_parse_rules OK")


def test_build_refine_prompt():
    p = build_refine_prompt(["规则A。", "规则B。"])
    assert "规则A。" in p and "规则B。" in p
    p0 = build_refine_prompt([])
    assert isinstance(p0, str) and len(p0) > 0
    print("test_build_refine_prompt OK")


def test_degrade_levels():
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "dataset"))
    from qi import load_dataset
    rows = load_dataset(str(Path(__file__).resolve().parent.parent / "dataset" / "output" / "dr_sl_dataset_v2.jsonl"))
    item = next(r for r in rows if r["split"] == "test"
                and r["annotations"]["explicit_identifiers"]
                and any(e.get("task_relevant") for e in r["annotations"]["quasi_identifiers"]))
    ds = degrade(item)
    assert ds[DegradeLevels.D0] == item["prompt"]
    for e in item["annotations"]["explicit_identifiers"]:
        assert e["value"] not in ds[DegradeLevels.D1]
        assert e["value"] not in ds[DegradeLevels.D2]
        assert e["value"] not in ds[DegradeLevels.D3]
    tr = [e for e in item["annotations"]["quasi_identifiers"] if e.get("task_relevant")]
    assert any(e["value"] in ds[DegradeLevels.D3] for e in tr) is False
    d2_has_gen = any(e["value"] not in ds[DegradeLevels.D2] for e in tr)
    assert d2_has_gen
    print("test_degrade_levels OK")


if __name__ == "__main__":
    test_memorization_rejects_literal_values()
    test_memorization_rejects_long_quotes()
    test_memorization_genscore()
    test_parse_rules()
    test_build_refine_prompt()
    test_degrade_levels()
    print("ALL DISTILL TESTS PASSED")
