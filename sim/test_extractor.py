import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "dataset"))

from extractor import llm_layer, cascade_extract, eval_extraction, parse_extraction_json


GOLD = {
    "annotations": {
        "explicit_identifiers": [
            {"type": "phone", "value": "19012345678", "category": "explicit"},
        ],
        "quasi_identifiers": [
            {"type": "age", "value": "31岁", "category": "quasi"},
            {"type": "disease", "value": "克罗恩病", "category": "quasi"},
        ],
    }
}


class ScriptedBackend:
    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = 0

    def complete(self, system, user):
        self.calls += 1
        return self.responses.pop(0)


def test_parse_extraction_json():
    good = '[{"type": "age", "value": "31岁"}, {"type": "city", "value": "南屏市"}]'
    out = parse_extraction_json(good, "我在南屏市，今年31岁。")
    assert {e["value"] for e in out} == {"31岁", "南屏市"}
    fenced = '```json\n[{"type": "age", "value": "31岁"}]\n```'
    assert len(parse_extraction_json(fenced, "我31岁了")) == 1
    bad = parse_extraction_json('[{"type": "age", "value": "99岁"}]', "我31岁了")
    assert bad == []
    assert parse_extraction_json("无法处理", "任意文本") == []
    print("test_parse_extraction_json OK")


def test_llm_layer_two_pass_and_merge():
    text = "我在南屏市工作，是护士。科室里一位31岁患者确诊为克罗恩病，联系电话19012345678。"
    b = ScriptedBackend([
        '[{"type": "age", "value": "31岁"}, {"type": "city", "value": "南屏市"}]',
        '[{"type": "disease", "value": "克罗恩病"}, {"type": "age", "value": "31岁"}]',
    ])
    ents = llm_layer(b, text)
    assert b.calls == 2
    vals = {e["value"] for e in ents}
    assert vals == {"31岁", "南屏市", "克罗恩病"}
    for e in ents:
        s, t = e["span"]
        assert text[s:t] == e["value"]
    print("test_llm_layer_two_pass_and_merge OK")


def test_cascade_dedup_and_spans():
    text = "联系电话19012345678。我今年31岁，住在南屏市。"
    b = ScriptedBackend([
        '[{"type": "age", "value": "31岁"}, {"type": "phone", "value": "19012345678"}]',
        '[{"type": "city", "value": "南屏市"}]',
    ])
    ents = cascade_extract(b, text)
    vals = [e["value"] for e in ents]
    assert vals.count("19012345678") == 1
    assert set(vals) == {"19012345678", "31岁", "南屏市"}
    spans = [e["span"] for e in ents]
    assert spans == sorted(spans)
    print("test_cascade_dedup_and_spans OK")


def test_eval_extraction():
    found = [
        {"type": "phone", "value": "19012345678", "category": "explicit"},
        {"type": "age", "value": "31岁", "category": "quasi"},
    ]
    rep = eval_extraction(found, GOLD)
    assert rep["recall_explicit"] == 1.0
    assert rep["recall_quasi"] == 0.5
    assert abs(rep["recall_overall"] - 2 / 3) < 1e-9
    assert rep["missed_values"] == ["克罗恩病"]
    print("test_eval_extraction OK")


def test_llm_layer_rules_injected():
    class CaptureBackend:
        def __init__(self):
            self.systems = []

        def complete(self, system, user):
            self.systems.append(system)
            return '[{"type": "age", "value": "31岁"}]'

    b = CaptureBackend()
    text = "我今年31岁。"
    ents = llm_layer(b, text, rules=["特别注意年龄的邻域表述。"])
    assert all("抽取改进规则" in s and "特别注意年龄的邻域表述。" in s for s in b.systems)
    assert len(ents) == 1
    b2 = CaptureBackend()
    llm_layer(b2, text, rules=None)
    assert all("抽取改进规则" not in s for s in b2.systems)
    print("test_llm_layer_rules_injected OK")


if __name__ == "__main__":
    test_parse_extraction_json()
    test_llm_layer_two_pass_and_merge()
    test_llm_layer_rules_injected()
    test_cascade_dedup_and_spans()
    test_eval_extraction()
    print("ALL EXTRACTOR TESTS PASSED")
