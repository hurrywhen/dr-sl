import json
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

OUT = Path(__file__).resolve().parent / "output" / "dr_sl_expansion_v1.jsonl"
V2 = Path(__file__).resolve().parent / "output" / "dr_sl_dataset_v2.jsonl"
DOMAINS = ("medical", "banking", "travel", "legal")


def load(path):
    with open(path) as f:
        return [json.loads(line) for line in f]


def test_exists_and_counts():
    items = load(OUT)
    assert len(items) == 480, len(items)
    te = [i for i in items if i["split"] == "test_ext"]
    tn = [i for i in items if i["split"] == "tnew"]
    assert len(te) == 240 and len(tn) == 240
    for d in DOMAINS:
        assert sum(1 for i in te if i["domain"] == d) == 60, d
        assert sum(1 for i in tn if i["domain"] == d) == 60, d
    tt = Counter(i["annotation_meta"].get("transform_type") for i in tn)
    assert tt["t1_lexical"] == tt["t2_type_inject"] == tt["t3_format"] == 80
    print("test_exists_and_counts OK")


def test_ids_unique_and_disjoint_from_v2():
    items = load(OUT)
    v2 = load(V2)
    ids_new = [i["id"] for i in items]
    assert len(ids_new) == len(set(ids_new))
    ids_v2 = {i["id"] for i in v2}
    assert not (set(ids_new) & ids_v2)
    print("test_ids_unique_and_disjoint_from_v2 OK")


def test_spans_consistent():
    for i in load(OUT):
        for cat in ("explicit_identifiers", "quasi_identifiers"):
            for e in i["annotations"][cat]:
                s, t = e["span"]
                assert i["prompt"][s:t] == e["value"], (i["id"], e["value"])
    print("test_spans_consistent OK")


def test_quasi_ratio():
    te = [i for i in load(OUT) if i["split"] == "test_ext"]
    ratio = sum(1 for i in te if i["annotations"]["has_quasi_identifier"]) / len(te)
    assert ratio >= 0.4, ratio
    print(f"test_quasi_ratio OK ({ratio:.3f})")


def test_t1_preserves_entities():
    tn = [i for i in load(OUT) if i["annotation_meta"].get("transform_type") == "t1_lexical"]
    v2 = load(V2)
    for i in tn:
        src = next(x for x in v2 if x["id"] == i["annotation_meta"]["source_instance_id"])
        vals_src = [e["value"] for cat in ("explicit_identifiers", "quasi_identifiers")
                    for e in src["annotations"][cat]]
        vals_new = [e["value"] for cat in ("explicit_identifiers", "quasi_identifiers")
                    for e in i["annotations"][cat]]
        assert vals_src == vals_new, i["id"]
    print("test_t1_preserves_entities OK")


def test_t2_injects_new_type():
    tn = [i for i in load(OUT) if i["annotation_meta"].get("transform_type") == "t2_type_inject"]
    v2 = load(V2)
    for i in tn:
        src = next(x for x in v2 if x["id"] == i["annotation_meta"]["source_instance_id"])
        types_src = {e["type"] for e in src["annotations"]["quasi_identifiers"]}
        types_new = {e["type"] for e in i["annotations"]["quasi_identifiers"]}
        added = types_new - types_src
        assert len(added) == 1, (i["id"], added)
    print("test_t2_injects_new_type OK")


def test_t3_format_markers():
    tn = [i for i in load(OUT) if i["annotation_meta"].get("transform_type") == "t3_format"]
    for i in tn:
        assert "用户：" in i["prompt"], i["id"]
    print("test_t3_format_markers OK")


def test_no_near_duplicates_with_v2():
    import difflib
    items = [i for i in load(OUT) if i["split"] == "test_ext"]
    v2_texts = [i["prompt"] for i in load(V2)]
    for i in items:
        assert not any(difflib.SequenceMatcher(None, i["prompt"], t).ratio() >= 0.85
                       for t in v2_texts), i["id"]
    print("test_no_near_duplicates_with_v2 OK")


if __name__ == "__main__":
    test_exists_and_counts()
    test_ids_unique_and_disjoint_from_v2()
    test_spans_consistent()
    test_quasi_ratio()
    test_t1_preserves_entities()
    test_t2_injects_new_type()
    test_t3_format_markers()
    test_no_near_duplicates_with_v2()
    print("ALL EXPANSION TESTS PASSED")
