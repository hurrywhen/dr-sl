import json
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from templates import TEMPLATES, TEMPLATE_META, TEMPLATE_STRUCTURE, ADVERSARIAL_TYPE
from generate_dataset import (assemble, apply_length, length_bucket_of, density_of,
                              difficulty_of, build_combos, plan_length_buckets,
                              DOMAIN_PREFIX, DUP_THRESHOLD, REDUNDANCY)

SEED = 20260908
OUTPUT = Path(__file__).resolve().parent / "output" / "dr_sl_mixed.jsonl"
DOMAINS = ("medical", "banking", "travel", "legal")
PER_DOMAIN = 30

CRITICAL_TYPES = {
    "medical": {"age", "disease", "drug", "allergy"},
    "banking": {"amount", "charge"},
    "travel": {"date", "visit_date", "city"},
    "legal": {"case_type", "amount", "date"},
}


def load_existing_texts():
    texts = []
    out = Path(__file__).resolve().parent / "output"
    for f in ("dr_sl_dataset_v2.jsonl", "dr_sl_expansion_v1.jsonl", "dr_sl_stage2_stream.jsonl"):
        p = out / f
        if p.exists():
            for line in open(p):
                texts.append(json.loads(line)["prompt"])
    return texts


def reannotate(entities, domain):
    crit = CRITICAL_TYPES[domain]
    ents = []
    for e in entities:
        e2 = dict(e)
        if e2["category"] == "quasi":
            e2["task_relevant"] = e2["type"] in crit
        else:
            e2["task_relevant"] = False
        ents.append(e2)
    return {
        "explicit_identifiers": [e for e in ents if e["category"] == "explicit"],
        "quasi_identifiers": [e for e in ents if e["category"] == "quasi"],
        "combos": build_combos(ents),
        "has_quasi_identifier": any(e["category"] == "quasi" for e in ents),
    }


def main():
    rng = random.Random(SEED)
    seen = load_existing_texts()
    items = []
    for domain in DOMAINS:
        tids = TEMPLATE_META[domain]["train"]
        buckets = plan_length_buckets(PER_DOMAIN, rng)
        accepted, attempts = [], 0
        while len(accepted) < PER_DOMAIN and attempts < PER_DOMAIN * REDUNDANCY * 8:
            attempts += 1
            tid = tids[attempts % len(tids)]
            parts = TEMPLATES[tid](rng)
            text, entities = assemble(parts)
            text = apply_length(text, buckets[len(accepted)], rng)
            if any(__import__("difflib").SequenceMatcher(None, text, s).ratio() >= DUP_THRESHOLD for s in seen):
                continue
            seen.append(text)
            accepted.append({"template_id": tid, "prompt": text, "entities": entities,
                             "length_bucket": length_bucket_of(text)})
        assert len(accepted) == PER_DOMAIN, domain
        for i, rec in enumerate(accepted, 1):
            ann = reannotate(rec["entities"], domain)
            n_qi = len(ann["quasi_identifiers"])
            n_crit = sum(1 for e in ann["quasi_identifiers"] if e["task_relevant"])
            items.append({
                "id": f"DRSL-{DOMAIN_PREFIX[domain]}-MIX-{i:04d}",
                "domain": domain,
                "split": "mixed",
                "prompt": rec["prompt"],
                "template_id": rec["template_id"],
                "structure": TEMPLATE_STRUCTURE[rec["template_id"]],
                "length_bucket": rec["length_bucket"],
                "sensitivity_density": density_of(rec["entities"]),
                "difficulty": difficulty_of(rec["entities"], TEMPLATE_STRUCTURE[rec["template_id"]]),
                "annotations": ann,
                "coupling_ratio": round(n_crit / n_qi, 3) if n_qi else 0.0,
                "source": "synthetic_template_mixed_coupling",
                "license": "synthetic-fictional",
                "annotation_meta": {"annotator": "rule_based_task_critical",
                                    "needs_human_review": True,
                                    "adversarial_type": ADVERSARIAL_TYPE.get(rec["template_id"])},
            })
    ids = [i["id"] for i in items]
    assert len(ids) == len(set(ids))
    with open(OUTPUT, "w", encoding="utf-8") as f:
        for i in items:
            f.write(json.dumps(i, ensure_ascii=False) + "\n")
    from collections import Counter
    import statistics
    print(json.dumps({"total": len(items),
                      "by_domain": dict(Counter(i["domain"] for i in items)),
                      "mean_coupling_ratio": round(statistics.mean(i["coupling_ratio"] for i in items), 3)},
                     ensure_ascii=False))


if __name__ == "__main__":
    main()
