import json
import random
import difflib
from collections import Counter, defaultdict

import synth_values as sv
from templates import TEMPLATES, TEMPLATE_META, TEMPLATE_STRUCTURE, ADVERSARIAL_TYPE

SEED = 20260825
OUTPUT = "output/dr_sl_dataset_v1.jsonl"
STATS = "output/stats_report.json"

SPLIT_TARGETS = {
    "calibration": 50,
    "train": 60,
    "test": 40,
    "adversarial": 20,
}
LENGTH_RATIO = {"short": 0.30, "medium": 0.40, "long": 0.30}
DENSITY_RATIO = {"low": 0.30, "medium": 0.50, "high": 0.20}
DUP_THRESHOLD = 0.85
REDUNDANCY = 3

DOMAIN_PREFIX = {"medical": "MED", "banking": "BNK", "travel": "TRV", "legal": "LEG"}
SPLIT_PREFIX = {"calibration": "CAL", "train": "TRN", "test": "TST", "adversarial": "ADV"}


def assemble(parts):
    text, entities, pos = "", [], 0
    for part in parts:
        if isinstance(part, tuple) and part[0] == "text":
            text += part[1]
            pos += len(part[1])
        else:
            payload = part
            start = pos
            text += payload["value"]
            pos += len(payload["value"])
            entities.append({
                "type": payload["type"],
                "category": payload["category"],
                "value": payload["value"],
                "span": [start, pos],
                "task_relevant": payload.get("task_relevant", False),
            })
    return text, entities


def apply_length(text, bucket, rng):
    if bucket == "short":
        return text
    fillers = rng.sample(sv.FILLER, k=len(sv.FILLER))
    i = 0
    while bucket == "medium" and len(text) < 150 or bucket == "long" and len(text) < 400:
        text += fillers[i % len(fillers)]
        i += 1
        if i > len(fillers) * 3:
            break
    return text


def length_bucket_of(text):
    n = len(text)
    return "short" if n < 150 else ("medium" if n < 400 else "long")


def density_of(entities):
    n = len(entities)
    return "low" if n <= 2 else ("medium" if n <= 5 else "high")


def difficulty_of(entities, structure):
    quasi = sum(1 for e in entities if e["category"] == "quasi")
    if quasi >= 3 or structure in ("dialogue", "longform"):
        return "hard"
    if quasi >= 1 or len(entities) >= 4:
        return "medium"
    return "easy"


COMBO_LOCALIZERS = {"city", "employer", "school", "hospital", "detention"}
COMBO_ATTRIBUTES = {"age", "gender", "occupation", "disease", "income", "charge", "case_type"}


def build_combos(entities):
    quasis = [e for e in entities if e["category"] == "quasi"]
    types = {e["type"] for e in quasis}
    combos = []
    if len(quasis) >= 2 and types & COMBO_LOCALIZERS and types & COMBO_ATTRIBUTES:
        combos.append({
            "members": [e["span"] for e in quasis],
            "member_types": [e["type"] for e in quasis],
            "risk": "reidentification",
            "note": "定位性属性+人口学/敏感属性组合，可在小范围群体内唯一化个体",
        })
    return combos


def plan_length_buckets(n, rng):
    counts = {"short": round(n * LENGTH_RATIO["short"]),
              "medium": round(n * LENGTH_RATIO["medium"])}
    counts["long"] = n - counts["short"] - counts["medium"]
    buckets = [b for b, c in counts.items() for _ in range(c)]
    rng.shuffle(buckets)
    return buckets


def generate_split(domain, split, rng):
    target = SPLIT_TARGETS[split]
    tids = TEMPLATE_META[domain][split]
    buckets = plan_length_buckets(target, rng)
    accepted, seen = [], []
    attempts = 0
    max_attempts = target * REDUNDANCY * 6
    while len(accepted) < target and attempts < max_attempts:
        attempts += 1
        tid = tids[attempts % len(tids)]
        bucket = buckets[len(accepted)]
        parts = TEMPLATES[tid](rng)
        text, entities = assemble(parts)
        text = apply_length(text, bucket, rng)
        if any(difflib.SequenceMatcher(None, text, s).ratio() >= DUP_THRESHOLD for s in seen):
            continue
        seen.append(text)
        accepted.append({"template_id": tid, "prompt": text, "entities": entities,
                         "length_bucket": length_bucket_of(text)})
    if len(accepted) < target:
        raise RuntimeError(f"{domain}/{split} 仅生成 {len(accepted)}/{target}，去重后不足")
    return accepted


def make_item(domain, split, idx, rec):
    entities = rec["entities"]
    has_quasi = any(e["category"] == "quasi" for e in entities)
    item = {
        "id": f"DRSL-{DOMAIN_PREFIX[domain]}-{SPLIT_PREFIX[split]}-{idx:04d}",
        "domain": domain,
        "split": split,
        "prompt": rec["prompt"],
        "template_id": rec["template_id"],
        "structure": TEMPLATE_STRUCTURE[rec["template_id"]],
        "length_bucket": rec["length_bucket"],
        "sensitivity_density": density_of(entities),
        "difficulty": difficulty_of(entities, TEMPLATE_STRUCTURE[rec["template_id"]]),
        "annotations": {
            "explicit_identifiers": [e for e in entities if e["category"] == "explicit"],
            "quasi_identifiers": [e for e in entities if e["category"] == "quasi"],
            "combos": build_combos(entities),
            "has_quasi_identifier": has_quasi,
        },
        "source": "synthetic_template",
        "license": "synthetic-fictional",
        "annotation_meta": {
            "annotator": "auto_v1",
            "needs_human_review": True,
            "adversarial_type": ADVERSARIAL_TYPE.get(rec["template_id"]),
        },
    }
    return item


def verify_spans(item):
    for cat in ("explicit_identifiers", "quasi_identifiers"):
        for e in item["annotations"][cat]:
            s, t = e["span"]
            assert item["prompt"][s:t] == e["value"], f"span mismatch in {item['id']}"


def stats(items):
    by_split = Counter(i["split"] for i in items)
    by_domain = Counter(i["domain"] for i in items)
    quasi_ratio = sum(1 for i in items if i["annotations"]["has_quasi_identifier"]) / len(items)
    out = {
        "total": len(items),
        "by_split": dict(by_split),
        "by_domain": dict(by_domain),
        "quasi_identifier_ratio": round(quasi_ratio, 4),
        "length_buckets": dict(Counter(i["length_bucket"] for i in items)),
        "structures": dict(Counter(i["structure"] for i in items)),
        "density": dict(Counter(i["sensitivity_density"] for i in items)),
        "difficulty": dict(Counter(i["difficulty"] for i in items)),
        "entity_type_counts": dict(Counter(
            e["type"] for i in items
            for cat in ("explicit_identifiers", "quasi_identifiers")
            for e in i["annotations"][cat])),
        "explicit_entity_total": sum(len(i["annotations"]["explicit_identifiers"]) for i in items),
        "quasi_entity_total": sum(len(i["annotations"]["quasi_identifiers"]) for i in items),
        "combo_total": sum(len(i["annotations"]["combos"]) for i in items),
        "split_domain_matrix": {
            f"{d}/{s}": sum(1 for i in items if i["domain"] == d and i["split"] == s)
            for d in DOMAIN_PREFIX for s in SPLIT_PREFIX
        },
    }
    return out


def main():
    rng = random.Random(SEED)
    items = []
    for domain in ("medical", "banking", "travel", "legal"):
        for split in ("calibration", "train", "test", "adversarial"):
            recs = generate_split(domain, split, rng)
            for idx, rec in enumerate(recs, 1):
                item = make_item(domain, split, idx, rec)
                verify_spans(item)
                items.append(item)

    ids = [i["id"] for i in items]
    assert len(ids) == len(set(ids)), "duplicate ids"

    import os
    os.makedirs("output", exist_ok=True)
    with open(OUTPUT, "w", encoding="utf-8") as f:
        for i in items:
            f.write(json.dumps(i, ensure_ascii=False) + "\n")

    rep = stats(items)
    with open(STATS, "w", encoding="utf-8") as f:
        json.dump(rep, f, ensure_ascii=False, indent=2)
    print(json.dumps(rep, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
