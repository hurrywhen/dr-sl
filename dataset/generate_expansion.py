import difflib
import json
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import synth_values as sv
from templates import TEMPLATES, TEMPLATE_META, TEMPLATE_STRUCTURE, ADVERSARIAL_TYPE

SEED = 20260829
V2_PATH = Path(__file__).resolve().parent / "output" / "dr_sl_dataset_v2.jsonl"
OUTPUT = Path(__file__).resolve().parent / "output" / "dr_sl_expansion_v1.jsonl"
STATS = Path(__file__).resolve().parent / "output" / "expansion_stats.json"
DOMAINS = ("medical", "banking", "travel", "legal")
DUP_THRESHOLD = 0.85

from generate_dataset import (
    assemble, apply_length, length_bucket_of, density_of, difficulty_of,
    build_combos, plan_length_buckets, make_item, verify_spans,
    LENGTH_RATIO, REDUNDANCY, DOMAIN_PREFIX,
)

PERTURB_MAP = {
    "相关背景情况已在前期沟通中说明，此处不再赘述。": "此前已经沟通过背景情况，这里就不再重复了。",
    "时间比较紧，希望能尽快得到答复，谢谢。": "因为时间比较赶，麻烦尽快回复，谢谢。",
    "家庭经济状况一般，请在建议中考虑成本因素。": "家里经济条件普通，请给出建议时把费用也考虑进去。",
    "此前已咨询过其他渠道，但意见不一致，希望得到更明确的分析。": "之前也问过别的渠道，说法不太一样，希望这次能给出更明确的分析。",
    "如有需要补充的信息，请列出清单，我会尽快提供。": "如果还需要我补充什么信息，请列个清单，我会尽快补齐。",
    "请结合上述情况给出专业、可操作的建议，并说明理由。": "麻烦结合上面的情况给出专业且可操作的建议，并说明依据。",
}


def load_v2():
    with open(V2_PATH) as f:
        return [json.loads(line) for line in f]


def sentences(text):
    out, buf = [], ""
    for ch in text:
        buf += ch
        if ch in "。！？；":
            out.append(buf)
            buf = ""
    if buf:
        out.append(buf)
    return out


def contains_entity(sent, entities):
    return any(e["value"] in sent for e in entities)


def realign(new_text, entities):
    new_entities, pos = [], 0
    for e in entities:
        idx = new_text.find(e["value"], pos)
        if idx < 0:
            idx = new_text.find(e["value"])
        assert idx >= 0, f"entity lost: {e['value']}"
        ne = dict(e)
        ne["span"] = [idx, idx + len(e["value"])]
        new_entities.append(ne)
        pos = idx + len(e["value"])
    return new_entities


def t1_lexical(text, entities, rng):
    sents = sentences(text)
    fixed = [s for s in sents if contains_entity(s, entities)]
    free = [s for s in sents if not contains_entity(s, entities)]
    free = [PERTURB_MAP.get(s, s) for s in free]
    rng.shuffle(free)
    merged_free = "".join(free)
    parts, fi = [], 0
    for s in sents:
        if contains_entity(s, entities):
            parts.append(s)
        else:
            if fi == 0:
                parts.append(merged_free)
            fi += 1
    if fi == 0:
        parts.append(merged_free)
    new_text = "".join(parts)
    return new_text, realign(new_text, entities)


INJECT_TEMPLATES = {
    "income": lambda rng: f"另外说明一下，我的年收入约{rng.choice([8, 12, 18, 25, 35, 50])}万元。",
    "occupation": lambda rng: f"补充一点，我目前的职业是{rng.choice(sv.OCCUPATIONS)}。",
    "disease": lambda rng: f"另外，我有{rng.choice(sv.DISEASES_COMMON)}的病史。",
    "city": lambda rng: f"我现在住在{rng.choice(sv.CITIES)}。",
    "age": lambda rng: f"我今年{rng.randint(22, 70)}岁。",
    "gender": lambda rng: f"我是{rng.choice(['男', '女'])}性。",
}


def t2_type_inject(text, entities, rng):
    present = {e["type"] for e in entities}
    candidates = [t for t in INJECT_TEMPLATES if t not in present]
    assert candidates, "no injectable type"
    t = rng.choice(candidates)
    phrase = INJECT_TEMPLATES[t](rng)
    base = text if text.endswith(("。", "！", "？")) else text + "。"
    start = len(base)
    new_text = base + phrase
    value = phrase
    new_entities = [dict(e) for e in entities]
    new_entities.append({
        "type": t,
        "category": "quasi",
        "value": value.rstrip("。"),
        "span": [start, start + len(value.rstrip("。"))],
        "task_relevant": False,
    })
    return new_text, new_entities, t


def t3_format(text, entities, rng):
    prefix = "用户："
    new_text = prefix + text + "\n助手：好的，我已经了解您说明的情况，让我梳理一下再给您答复。"
    return new_text, realign(new_text, entities)


def rebuild_annotations(entities):
    return {
        "explicit_identifiers": [e for e in entities if e["category"] == "explicit"],
        "quasi_identifiers": [e for e in entities if e["category"] == "quasi"],
        "combos": build_combos(entities),
        "has_quasi_identifier": any(e["category"] == "quasi" for e in entities),
    }


def make_variant(idx, src, transform_type, text, entities, rng):
    return {
        "id": f"DRSL-{DOMAIN_PREFIX[src['domain']]}-NEW-{idx:04d}",
        "domain": src["domain"],
        "split": "tnew",
        "prompt": text,
        "template_id": src["template_id"],
        "structure": "dialogue" if transform_type == "t3_format" else src["structure"],
        "length_bucket": length_bucket_of(text),
        "sensitivity_density": density_of(entities),
        "difficulty": difficulty_of(entities, src["structure"]),
        "annotations": rebuild_annotations(entities),
        "source": "synthetic_shift_variant",
        "license": "synthetic-fictional",
        "annotation_meta": {
            "annotator": "auto_v1",
            "needs_human_review": True,
            "adversarial_type": None,
            "transform_type": transform_type,
            "source_instance_id": src["id"],
        },
    }


def generate_test_ext(rng, v2_texts):
    items, seen = [], list(v2_texts)
    idx_by_domain = {}
    for domain in DOMAINS:
        tids = TEMPLATE_META[domain]["test"]
        target = 60
        buckets = plan_length_buckets(target, rng)
        accepted = []
        attempts = 0
        while len(accepted) < target and attempts < target * REDUNDANCY * 8:
            attempts += 1
            tid = tids[attempts % len(tids)]
            parts = TEMPLATES[tid](rng)
            text, entities = assemble(parts)
            text = apply_length(text, buckets[len(accepted)], rng)
            if any(difflib.SequenceMatcher(None, text, s).ratio() >= DUP_THRESHOLD for s in seen):
                continue
            seen.append(text)
            accepted.append({"template_id": tid, "prompt": text, "entities": entities,
                             "length_bucket": length_bucket_of(text)})
        assert len(accepted) == target, domain
        for i, rec in enumerate(accepted, 1):
            rec2 = dict(rec)
            item = make_item_lite(domain, i, rec2)
            verify_spans(item)
            items.append(item)
    return items


def make_item_lite(domain, idx, rec):
    entities = rec["entities"]
    return {
        "id": f"DRSL-{DOMAIN_PREFIX[domain]}-TSE-{idx:04d}",
        "domain": domain,
        "split": "test_ext",
        "prompt": rec["prompt"],
        "template_id": rec["template_id"],
        "structure": TEMPLATE_STRUCTURE[rec["template_id"]],
        "length_bucket": rec["length_bucket"],
        "sensitivity_density": density_of(entities),
        "difficulty": difficulty_of(entities, TEMPLATE_STRUCTURE[rec["template_id"]]),
        "annotations": rebuild_annotations(entities),
        "source": "synthetic_template",
        "license": "synthetic-fictional",
        "annotation_meta": {
            "annotator": "auto_v1",
            "needs_human_review": True,
            "adversarial_type": ADVERSARIAL_TYPE.get(rec["template_id"]),
        },
    }


def generate_tnew(rng, v2):
    sources = [i for i in v2 if i["split"] == "test"]
    items = []
    idx = 0
    plan = []
    for domain in DOMAINS:
        dom_src = [s for s in sources if s["domain"] == domain]
        for ti, ttype in enumerate(("t1_lexical", "t2_type_inject", "t3_format")):
            for k in range(20):
                src = dom_src[(ti * 20 + k) % len(dom_src)]
                plan.append((src, ttype))
    rng.shuffle(plan)
    used_pairs = set()
    for src, ttype in plan:
        key = (src["id"], ttype)
        while key in used_pairs:
            src = rng.choice([s for s in sources if s["domain"] == src["domain"]])
            key = (src["id"], ttype)
        used_pairs.add(key)
        entities = src["annotations"]["explicit_identifiers"] + src["annotations"]["quasi_identifiers"]
        entities = sorted(entities, key=lambda e: e["span"][0])
        if ttype == "t1_lexical":
            text, new_ent = t1_lexical(src["prompt"], entities, rng)
            item = make_variant(idx, src, ttype, text, new_ent, rng)
        elif ttype == "t2_type_inject":
            text, new_ent, injected = t2_type_inject(src["prompt"], entities, rng)
            item = make_variant(idx, src, ttype, text, new_ent, rng)
            item["annotation_meta"]["injected_type"] = injected
        else:
            text, new_ent = t3_format(src["prompt"], entities, rng)
            item = make_variant(idx, src, ttype, text, new_ent, rng)
        verify_spans(item)
        idx += 1
        items.append(item)
    return items


def main():
    rng = random.Random(SEED)
    v2 = load_v2()
    te = generate_test_ext(rng, [i["prompt"] for i in v2])
    tn = generate_tnew(rng, v2)
    items = te + tn
    ids = [i["id"] for i in items]
    assert len(ids) == len(set(ids))
    with open(OUTPUT, "w", encoding="utf-8") as f:
        for i in items:
            f.write(json.dumps(i, ensure_ascii=False) + "\n")
    from collections import Counter
    report = {
        "total": len(items),
        "by_split": dict(Counter(i["split"] for i in items)),
        "by_domain": dict(Counter(i["domain"] for i in items)),
        "transform_types": dict(Counter(i["annotation_meta"].get("transform_type")
                                         for i in items if i["split"] == "tnew")),
        "quasi_ratio_test_ext": round(sum(1 for i in te if i["annotations"]["has_quasi_identifier"]) / len(te), 4),
    }
    with open(STATS, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
