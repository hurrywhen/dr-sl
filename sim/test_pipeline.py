import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "dataset"))

from pipeline import (
    ATTR_NAMES, gen_probe_questions, grade, branch1_stats,
    extract_explicit, parse_dehydrate_json, PipelineMockBackend,
    attack_run, qa_probe_run, dehydrate_run,
)
from qi import load_dataset

DATA = Path(__file__).resolve().parent.parent / "dataset" / "output" / "dr_sl_dataset_v2.jsonl"


def sample_items():
    rows = load_dataset(str(DATA))
    return [r for r in rows if r["split"] == "test"][:8]


def test_grade():
    assert grade("她的年龄是31岁。", "31岁", "value") == 1
    assert grade("31", "31岁", "value") == 1
    assert grade("大约三十多岁", "31岁", "value") == 0
    assert grade("UNKNOWN", "31岁", "value") == 0
    assert grade("能，组合可唯一确定", "能", "judge") == 1
    assert grade("不能", "能", "judge") == 0
    assert grade("信息不足", "不能", "judge") == 0
    assert grade("不能", "不能", "judge") == 0
    assert grade("能确定", "不能", "judge") == 0
    assert grade("80多岁", "84岁", "value", tolerant=False) == 0
    assert grade("80多岁", "84岁", "value", tolerant=True) == 1
    print("test_grade OK")


def test_probe_questions():
    items = sample_items()
    item = next(i for i in items if i["annotations"]["quasi_identifiers"])
    qs = gen_probe_questions(item)
    n_entities = len(item["annotations"]["quasi_identifiers"]) + len(item["annotations"]["explicit_identifiers"])
    n_judge = 1
    assert len(qs) == n_entities + n_judge
    assert all(kind in ("value", "judge") for _, _, kind in qs)
    judge = [t for _, t, k in qs if k == "judge"]
    expected = "能" if item["annotations"]["combos"] else "不能"
    assert judge == [expected]
    print("test_probe_questions OK")


def test_branch1_stats():
    res = branch1_stats(hits=0, n=75, tau_l=0.05)
    assert res["pass_gate"]
    res2 = branch1_stats(hits=0, n=15, tau_l=0.05)
    assert not res2["pass_gate"]
    res3 = branch1_stats(hits=3, n=20, tau_l=0.05)
    assert res3["L"] == 0.15 and not res3["pass_gate"]
    print("test_branch1_stats OK")


def test_extract_explicit():
    text = "我的手机号是13912345678，邮箱zhang@example.com，身份证110101199003074321。"
    ents = extract_explicit(text)
    types = {e["type"] for e in ents}
    assert "phone" in types and "email" in types and "id_card" in types
    for e in ents:
        s, t = e["span"]
        assert text[s:t] == e["value"]
    print("test_extract_explicit OK")


def test_qa_probe_perfect_when_D_equals_X():
    items = sample_items()
    item = next(i for i in items if any(
        e.get("task_relevant") for e in i["annotations"]["quasi_identifiers"]))
    mb = PipelineMockBackend(mode="echo_truth_from_context")
    mb.set_truths(item)
    res = qa_probe_run(mb, item["prompt"], item)
    assert res["n"] > 0
    assert res["U"] == 1.0, res
    print("test_qa_probe_perfect_when_D_equals_X OK")


def test_attack_run_counts_hits():
    items = sample_items()
    item = next(i for i in items if i["annotations"]["quasi_identifiers"])
    mb = PipelineMockBackend(mode="answer_nothing")
    mb.set_truths(item)
    res = attack_run(mb, "（已脱敏文本，不含任何细节）", item, level="A_0")
    assert res["hits"] == 0
    assert res["n"] == len(gen_probe_questions(item))
    mb2 = PipelineMockBackend(mode="echo_truth_from_context")
    mb2.set_truths(item)
    res2 = attack_run(mb2, item["prompt"], item, level="A_0")
    n_value = len(item["annotations"]["quasi_identifiers"]) + len(item["annotations"]["explicit_identifiers"])
    expected = n_value + (1 if item["annotations"]["combos"] else 0)
    assert res2["hits"] == expected, (res2["hits"], expected)
    print("test_attack_run_counts_hits OK")


def test_parse_dehydrate_json():
    good = '{"text": "匿名化文本", "removed": ["张三"], "generalized": [{"from": "31岁", "to": "30多岁"}]}'
    out = parse_dehydrate_json(good)
    assert out["text"] == "匿名化文本"
    bad = '```json\n{"text": "t", "removed": [], "generalized": []}\n```'
    assert parse_dehydrate_json(bad)["text"] == "t"
    try:
        parse_dehydrate_json("无法解析")
        raise SystemExit("should raise")
    except ValueError:
        pass
    print("test_parse_dehydrate_json OK")


def test_dehydrate_run_with_mock():
    items = sample_items()
    item = next(i for i in items if i["annotations"]["quasi_identifiers"])
    mb = PipelineMockBackend(mode="dehydrate_scripted")
    out = dehydrate_run(mb, item)
    assert out["D"]
    assert isinstance(out["removed"], list)
    print("test_dehydrate_run_with_mock OK")


def test_dehydrate_fallback_on_bad_output():
    from pipeline import deterministic_dehydrate

    class BadBackend:
        def complete(self, system, user):
            return "我无法按要求输出。"

    items = sample_items()
    item = next(i for i in items if i["annotations"]["quasi_identifiers"])
    out = dehydrate_run(BadBackend(), item)
    assert out.get("fallback") is True
    for e in item["annotations"]["quasi_identifiers"]:
        assert e["value"] not in out["D"], e["value"]
    det = deterministic_dehydrate(item)
    for e in item["annotations"]["explicit_identifiers"]:
        assert e["value"] not in det["D"]
    print("test_dehydrate_fallback_on_bad_output OK")


def test_attr_names_cover_dataset_types():
    from collections import Counter
    types = Counter()
    for r in load_dataset(str(DATA)):
        for cat in ("explicit_identifiers", "quasi_identifiers"):
            for e in r["annotations"][cat]:
                types[e["type"]] += 1
    missing = [t for t in types if t not in ATTR_NAMES]
    assert not missing, missing
    print("test_attr_names_cover_dataset_types OK")


def test_grade_numeric_tolerance():
    assert grade("大约30多岁", "31岁", "value") == 1
    assert grade("大约40多岁", "31岁", "value") == 0
    assert grade("收入约29万元", "年收入约30万元", "value") == 1
    assert grade("收入30万至35万元左右", "年收入约30万元", "value") == 1
    assert grade("金额约40000至50000", "转账金额48500元", "value") == 1
    print("test_grade_numeric_tolerance OK")


def test_det_policy():
    from pipeline import det_dehydrate, det_strengthen, det_loosen
    rows = load_dataset(str(DATA))
    item = next(i for i in rows if i["split"] == "test" and any(
        e.get("task_relevant") for e in i["annotations"]["quasi_identifiers"])
        and i["annotations"]["explicit_identifiers"])
    d0 = det_dehydrate(item)
    for e in item["annotations"]["quasi_identifiers"]:
        assert e["value"] not in d0["D"], e["value"]
    loose = det_loosen(item)
    tr = [e for e in item["annotations"]["quasi_identifiers"] if e.get("task_relevant")]
    assert any(e["value"] in loose["D"] for e in tr)
    qname = None
    for e in item["annotations"]["quasi_identifiers"]:
        if e["type"] in ("age", "city", "disease"):
            qname = ATTR_NAMES[e["type"]]
            break
    st = det_strengthen(d0["D"], item, f"{qname}=x", {"applied_pairs": []})
    assert st is None or st.get("changed") in (True, False)
    print("test_det_policy OK")


def test_attack_run_bundle_expands_to_75():
    from pipeline import attack_run_bundle
    items = load_dataset(str(DATA))
    item = next(i for i in items if i["split"] == "test" and i["annotations"]["quasi_identifiers"])
    mb = PipelineMockBackend(mode="answer_nothing")
    mb.set_truths(item)
    res = attack_run_bundle(mb, "（空材料）", item, min_questions=75)
    assert res["n"] >= 75
    assert res["hits"] == 0
    print("test_attack_run_bundle_expands_to_75 OK")


def test_det_dehydrate_all_occurrences():
    from pipeline import det_dehydrate, hard_line_scrub
    item = {
        "prompt": "我叫张三，电话13912345678。张三今年确诊了高血压，请联系13912345678。",
        "annotations": {
            "explicit_identifiers": [
                {"type": "name", "category": "explicit", "value": "张三", "span": [3, 5], "task_relevant": False},
                {"type": "phone", "category": "explicit", "value": "13912345678", "span": [8, 19], "task_relevant": False},
            ],
            "quasi_identifiers": [
                {"type": "disease", "category": "quasi", "value": "高血压", "span": [25, 28], "task_relevant": True},
            ],
            "combos": [],
        },
    }
    d = det_dehydrate(item)["D"]
    assert d.count("张三") == 0 and d.count("13912345678") == 0 and d.count("高血压") == 0
    item2 = {
        "prompt": "患者84岁，确诊重症肌无力。84岁患者需专人照护，重症肌无力属罕见病。",
        "annotations": {
            "explicit_identifiers": [],
            "quasi_identifiers": [
                {"type": "age", "category": "quasi", "value": "84岁", "span": [2, 5], "task_relevant": True},
                {"type": "disease", "category": "quasi", "value": "重症肌无力", "span": [7, 12], "task_relevant": True},
            ],
            "combos": [],
        },
    }
    d2 = det_dehydrate(item2)["D"]
    assert d2.count("84岁") == 0 and d2.count("重症肌无力") == 0
    assert "80多岁" in d2
    leaky = "残留文本提到张三和13912345678以及高血压。"
    scrubbed = hard_line_scrub(leaky, item)
    assert "张三" not in scrubbed["D"] and "13912345678" not in scrubbed["D"]
    assert set(scrubbed["removed"]) == {"张三", "13912345678", "高血压"}
    clean = hard_line_scrub("无敏感内容", item)
    assert clean["D"] == "无敏感内容" and clean["removed"] == []
    print("test_det_dehydrate_all_occurrences OK")


def test_attack_enum_bundle():
    from pipeline import attack_enum_bundle, gen_probe_questions
    items = load_dataset(str(DATA))
    item = next(i for i in items if i["split"] == "test" and i["annotations"]["quasi_identifiers"])

    class EnumMock:
        def __init__(self, values):
            self.values = values
            self.calls = 0

        def complete(self, system, user):
            self.calls += 1
            return json.dumps({"values": self.values})

    qs = gen_probe_questions(item)
    m = max(1, -(-75 // len(qs)))
    bundle = (qs * m)[:max(75, len(qs))]
    n_value = sum(1 for _, _, k in bundle if k == "value")

    gold = [e["value"] for cat in ("explicit_identifiers", "quasi_identifiers")
            for e in item["annotations"][cat]]
    res = attack_enum_bundle(EnumMock(gold), "材料", item, min_questions=75)
    assert res["n"] >= 75
    assert res["hits"] == n_value, (res["hits"], n_value)
    res2 = attack_enum_bundle(EnumMock([]), "材料", item, min_questions=75)
    assert res2["hits"] == 0
    print("test_attack_enum_bundle OK")


if __name__ == "__main__":
    test_grade()
    test_grade_numeric_tolerance()
    test_probe_questions()
    test_branch1_stats()
    test_extract_explicit()
    test_qa_probe_perfect_when_D_equals_X()
    test_attack_run_counts_hits()
    test_attack_run_bundle_expands_to_75()
    test_attack_enum_bundle()
    test_parse_dehydrate_json()
    test_dehydrate_run_with_mock()
    test_dehydrate_fallback_on_bad_output()
    test_det_policy()
    test_det_dehydrate_all_occurrences()
    test_attr_names_cover_dataset_types()
    print("ALL PIPELINE TESTS PASSED")
