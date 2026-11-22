"""Offline tests for the neural-extractor parsing/localization interface
(round 4, protocol v4 §7).  No API calls.
"""
from revision_neural_extractor import locate, parse_proposals


def test_parse_clean_and_fenced():
    raw = '{"entities":[{"type":"name","value":"张三"},{"type":"amount","value":"150000元"}]}'
    p, ok = parse_proposals(raw)
    assert ok and p == [("name", "张三"), ("amount", "150000元")]
    p2, ok2 = parse_proposals("```json\n" + raw + "\n```")
    assert ok2 and p2 == p
    p3, ok3 = parse_proposals("好的，以下是结果：\n" + raw + "\n以上。")
    assert ok3 and p3 == p
    print("test_parse_clean_and_fenced OK")


def test_parse_failures():
    for bad in ("", "no json here", '{"entities": "oops"}', '{"entities":[{"type":1}]}'):
        p, ok = parse_proposals(bad)
        assert not ok or p == []
    # empty entity list is a valid parse
    p, ok = parse_proposals('{"entities":[]}')
    assert ok and p == []
    print("test_parse_failures OK")


def test_locate_all_occurrences_and_unlocatable():
    text = "客户张三申请150000元。张三的电话是13800000000。"
    proposals = [("name", "张三"), ("amount", "150000元"),
                 ("phone", "13800000000"), ("name", "李四")]  # 李四 not in text
    ents, unloc, unknown = locate(text, proposals)
    assert unloc == 1 and unknown == 0
    names = [e for e in ents if e["type"] == "name"]
    assert len(names) == 2  # both occurrences of 张三
    assert all(text[e["span"][0]:e["span"][1]] == e["value"] for e in ents)
    assert all(e["source"] == "neural_llm" for e in ents)
    print("test_locate_all_occurrences_and_unlocatable OK")


def test_locate_unknown_type_and_overlap():
    text = "月收入约5000元，申请5000元。"
    proposals = [("income", "月收入约5000元"), ("amount", "5000元"),
                 ("bogus_type", "5000元")]
    ents, unloc, unknown = locate(text, proposals)
    assert unknown == 1
    # longer income span wins the overlap at the first occurrence; the second
    # standalone 5000元 remains an amount.
    types = [(e["type"], e["value"]) for e in ents]
    assert ("income", "月收入约5000元") in types
    assert ("amount", "5000元") in types
    spans = [e["span"] for e in ents]
    # explicit non-overlap check
    for i in range(len(spans)):
        for j in range(i + 1, len(spans)):
            s1, t1 = spans[i]; s2, t2 = spans[j]
            assert t1 <= s2 or t2 <= s1
    print("test_locate_unknown_type_and_overlap OK")


def test_categories_match_explicit_set():
    ents, _, _ = locate("邮箱a@b.com，手机13800000000，城市南京，金额100元",
                        [("email", "a@b.com"), ("phone", "13800000000"),
                         ("city", "南京"), ("amount", "100元")])
    cat = {e["type"]: e["category"] for e in ents}
    assert cat["email"] == "explicit" and cat["phone"] == "explicit"
    assert cat["city"] == "quasi" and cat["amount"] == "quasi"
    print("test_categories_match_explicit_set OK")


if __name__ == "__main__":
    test_parse_clean_and_fenced()
    test_parse_failures()
    test_locate_all_occurrences_and_unlocatable()
    test_locate_unknown_type_and_overlap()
    test_categories_match_explicit_set()
    print("ALL NEURAL PARSER TESTS PASSED")