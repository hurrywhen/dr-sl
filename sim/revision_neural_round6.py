#!/usr/bin/env python3
"""Round-6 archived-output corrections (protocol v6).  No API calls.

- Pin the three GLM zero-charge cases as gold-substring-of-proposal /
  repeated-mention span variants, not `never_proposed`.
- Report holdout-4 per-type direct extraction and released-residue evidence,
  separating value-level exact extraction from type-and-value exact extraction.
- Mark complete-taxonomy FR_gap=0 as a definitional identity, not performance
  evidence.
- Characterize the persistent city residue without choosing between a
  value/template omission and a city/county/address type-boundary explanation.
- Additional sensitivity only: exclude exact zero-yuan charge residues (`0元`),
  keeping release denominators and the primary FR metric unchanged.
"""
import hashlib
import json
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "dataset"))

from revision_neural_analysis import (classify_proposal_relation,
                                      fr_decomposition, gold_type_map,
                                      load_items)
from revision_neural_extractor import TYPES, parse_proposals
from revision_neural_round5 import TYPES_V2
from revision_stats import wilson_interval
from runtime import gold_entities

ROOT = Path(__file__).resolve().parent.parent
R2 = ROOT / "results" / "revision_20261121"
R3 = ROOT / "results" / "revision_round3"
FILES = {
    "holdout80": "dr_sl_holdout_v1.jsonl",
    "holdout80_v2": "dr_sl_holdout_v2.jsonl",
    "holdout80_v3": "dr_sl_holdout_v3.jsonl",
    "holdout80_v4": "dr_sl_holdout_v4.jsonl",
    "drift_p000": "dr_sl_drift_p000.jsonl",
    "drift_p025": "dr_sl_drift_p025.jsonl",
    "drift_p050": "dr_sl_drift_p050.jsonl",
    "drift_p075": "dr_sl_drift_p075.jsonl",
    "drift_p100": "dr_sl_drift_p100.jsonl",
}


def read_jsonl(path):
    return [json.loads(line) for line in path.open(encoding="utf-8")]


def load_all_items():
    items = {}
    for fname in FILES.values():
        items.update(load_items(fname))
    return items


def is_boundary_zero_charge(gold_type, value):
    return gold_type == "charge" and value == "0元"


def zero_charge_sensitivity(rows, items):
    """Additional construct sensitivity; does not alter primary FR rows."""
    released = [r for r in rows if r["release"]]
    original, kept, excluded_only = [], [], []
    for r in released:
        hits = list(r["gold_literal_hit_values"])
        tm = gold_type_map(items[r["id"]])
        remaining = [v for v in hits if not is_boundary_zero_charge(tm[v], v)]
        if hits:
            original.append(r["id"])
            if remaining:
                kept.append(r["id"])
            else:
                excluded_only.append(r["id"])
    n = len(released)

    def block(ids):
        return {"k": len(ids), "n": n,
                "rate": len(ids) / n if n else None,
                "wilson95": list(wilson_interval(len(ids), n)) if n else None,
                "ids": sorted(ids)}

    return {"primary_FR_gold": block(original),
            "FR_excluding_zero_charge": block(kept),
            "residue_only_zero_charge": block(excluded_only),
            "exclusion_rule": "gold type == charge and gold value == 0元; releases fixed"}


def h4_type_evidence(items, rows, cache):
    per_type = defaultdict(lambda: {"n_gold": 0, "value_exact": 0,
                                    "type_value_exact": 0,
                                    "released_residue_ids": set()})
    for iid, item in items.items():
        ents = cache[iid]["entities"]
        values = {e["value"] for e in ents}
        typed_values = {(e["type"], e["value"]) for e in ents}
        for e in gold_entities(item):
            b = per_type[e["type"]]
            b["n_gold"] += 1
            b["value_exact"] += e["value"] in values
            b["type_value_exact"] += (e["type"], e["value"]) in typed_values
    cl = [r for r in rows if r["condition"] == "h4_complete"
          and r["method"] == "closed_loop"]
    for r in cl:
        if not r["release"]:
            continue
        tm = gold_type_map(items[r["id"]])
        for v in r["gold_literal_hit_values"]:
            per_type[tm[v]]["released_residue_ids"].add(r["id"])
    out = {}
    for typ, b in sorted(per_type.items()):
        ids = sorted(b.pop("released_residue_ids"))
        b["released_residue_instances"] = len(ids)
        b["released_residue_ids"] = ids
        out[typ] = b
    return out


def glm_zero_charge_details(items, rows, cache):
    details = []
    for r in rows:
        if (r["condition"] != "family_glm" or r["method"] != "closed_loop"
                or not r["release"] or "0元" not in r["gold_literal_hit_values"]):
            continue
        iid = r["id"]
        if gold_type_map(items[iid]).get("0元") != "charge":
            continue
        raw = cache[(iid, "family_glm")]["raw"]
        proposals, ok = parse_proposals(raw)
        assert ok
        relation = classify_proposal_relation("charge", "0元", proposals)
        assert relation["kind"] == "gold_substring_of_proposal", (iid, relation)
        details.append({"id": iid, "gold_value": "0元", "gold_type": "charge",
                        "relation": relation,
                        "extended_span_in_artifact": "0元手续费" in r["D"],
                        "short_form_in_artifact": "前述0元情况" in r["D"],
                        "artifact": r["D"],
                        "mechanism": "extended fee span proposed and scrubbed; "
                                     "short form in appended clarification remains"})
    assert len(details) == 3, len(details)
    return details


def main():
    items = load_all_items()
    r4_rows = read_jsonl(R3 / "neural_extractor_rows.jsonl")
    r5_rows = read_jsonl(R3 / "neural_round5_rows.jsonl")
    r5_cache_list = read_jsonl(R3 / "neural_round5_cache.jsonl")
    r5_cache = {(r["id"], r["condition"]): r for r in r5_cache_list if "entities" in r}
    h4_items = {iid: it for iid, it in items.items() if iid.startswith("DRSL-H4-")}
    h4_cache = {iid: r for (iid, cond), r in r5_cache.items() if cond == "h4_complete"}
    assert len(h4_items) == len(h4_cache) == 80

    # Definitional identity, independently recomputed from archived rows.
    h4_gold_types = {e["type"] for it in h4_items.values() for e in gold_entities(it)}
    assert h4_gold_types <= TYPES_V2
    h4_cl = [r for r in r5_rows if r["condition"] == "h4_complete"
             and r["method"] == "closed_loop"]
    dec = fr_decomposition(h4_cl, h4_items, TYPES_V2)
    assert dec["FR_taxonomy_gap"]["k"] == 0

    type_evidence = h4_type_evidence(h4_items, r5_rows, h4_cache)
    for typ in ("room_no", "marriage_years", "work_years"):
        b = type_evidence[typ]
        assert (b["n_gold"], b["value_exact"], b["type_value_exact"],
                b["released_residue_instances"]) == (10, 10, 10, 0), (typ, b)
    assert type_evidence["city"]["n_gold"] == 60
    assert type_evidence["city"]["value_exact"] == 59
    assert type_evidence["city"]["type_value_exact"] == 54
    assert type_evidence["city"]["released_residue_instances"] == 1

    # City type-label variation is distinct from value-level omission.
    city_type_variation = []
    city_value_misses = []
    for iid, item in h4_items.items():
        ents = h4_cache[iid]["entities"]
        values = {e["value"] for e in ents}
        for e in gold_entities(item):
            if e["type"] != "city":
                continue
            same_value = [x for x in ents if x["value"] == e["value"]]
            if not same_value:
                city_value_misses.append({"id": iid, "value": e["value"]})
            other_types = sorted({x["type"] for x in same_value if x["type"] != "city"})
            if other_types:
                city_type_variation.append({"id": iid, "value": e["value"],
                                            "proposed_types": other_types})
    assert len(city_value_misses) == 1
    assert city_value_misses[0]["value"] == "望海县"
    assert len(city_type_variation) == 5

    # Additional zero-charge sensitivity over core deterministic and neural rows.
    r2_rows = read_jsonl(R2 / "offline_runtime.jsonl")
    h3_rows = read_jsonl(R3 / "offline_h3.jsonl")
    h4_det_rows = read_jsonl(R3 / "offline_h4.jsonl")
    groups = {
        "det_h1_original": [r for r in r2_rows if r["dataset"] == "holdout80"
                            and r["sensitive_set"] == "runtime"
                            and r["method"] == "closed_loop"],
        "det_h1_fixed": [r for r in h3_rows if r["dataset"] == "holdout80_diag_fixed"
                         and r["extractor"] == "fixed" and r["method"] == "closed_loop"],
        "det_h2_original": [r for r in r2_rows if r["dataset"] == "holdout80_v2"
                            and r["sensitive_set"] == "runtime"
                            and r["method"] == "closed_loop"],
        "det_h2_fixed": [r for r in h3_rows if r["dataset"] == "holdout80_v2_diag_fixed"
                         and r["extractor"] == "fixed" and r["method"] == "closed_loop"],
        "det_h3_original": [r for r in h3_rows if r["dataset"] == "holdout80_v3"
                            and r["extractor"] == "original" and r["method"] == "closed_loop"],
        "det_h3_fixed": [r for r in h3_rows if r["dataset"] == "holdout80_v3"
                         and r["extractor"] == "fixed" and r["method"] == "closed_loop"],
        "det_h4_original": [r for r in h4_det_rows if r["extractor"] == "original"
                            and r["method"] == "closed_loop"],
        "det_h4_fixed": [r for r in h4_det_rows if r["extractor"] == "fixed"
                         and r["method"] == "closed_loop"],
    }
    for tag in ("p000", "p025", "p050", "p075", "p100"):
        groups[f"det_drift_{tag}"] = [
            r for r in h3_rows if r["dataset"] == f"drift_{tag}"
            and r["extractor"] == "original" and r["method"] == "closed_loop"]
    for ds in ("holdout80", "holdout80_v3", "drift_p000"):
        groups[f"neural_round4_{ds}"] = [
            r for r in r4_rows if r["dataset"] == ds and r["method"] == "closed_loop"]
    for cond in ("stability_r1", "stability_r2", "family_glm", "h4_complete"):
        groups[f"neural_round5_{cond}"] = [
            r for r in r5_rows if r["condition"] == cond and r["method"] == "closed_loop"]
    sensitivity = {name: zero_charge_sensitivity(rows, items)
                   for name, rows in groups.items()}

    glm_details = glm_zero_charge_details(items, r5_rows, r5_cache)
    out = {
        "protocol": "revision_protocol_v6.md; archived outputs only; no API calls",
        "primary_metric_unchanged": True,
        "gold_literal_construct": (
            "FR_gold is a gold-annotated literal-residue audit proxy, not demonstrated "
            "privacy damage or re-identification; explicit identifiers, quasi-identifiers "
            "and context-dependent task-critical values are not equated in construct"),
        "zero_charge_annotation": {
            "basis": "conservative personal-financial quasi-identifier and banking task-relevance rule",
            "not_claimed": "a zero fee alone is private or identifying",
            "generator_disclosure": "whole-thousand quantization makes money(r,5,200) return 0元",
            "frozen_data_changed": False},
        "glm_zero_charge_repeated_mention": glm_details,
        "holdout4": {
            "FR_gap_zero_interpretation": "definitional identity: all h4 gold types are declared",
            "FR_gap_zero_is_performance_evidence": False,
            "FR_taxonomy_gap": dec["FR_taxonomy_gap"],
            "per_type_extraction_and_residue": type_evidence,
            "city_value_misses": city_value_misses,
            "city_type_label_variation": city_type_variation,
            "city_explanations": [
                "value/template-specific omission",
                "city/county/administrative-region versus address type-boundary mismatch"],
            "city_explanation_identified": False,
            "minimal_control_status": "future work; no new calls in round 6"},
        "zero_charge_sensitivity": sensitivity,
    }
    path = R3 / "neural_round6_analysis.json"
    path.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print("GLM zero-charge relations:",
          [(d["id"], d["relation"]["kind"],
            [p["value"] for p in d["relation"]["matched_proposals"]]) for d in glm_details])
    for typ in ("room_no", "marriage_years", "work_years", "city"):
        print("h4", typ, type_evidence[typ])
    for name, b in sensitivity.items():
        a, c = b["primary_FR_gold"], b["FR_excluding_zero_charge"]
        if a["k"] != c["k"]:
            print(f"sensitivity {name}: {a['k']}/{a['n']} -> {c['k']}/{c['n']}")
    print("wrote", path)


if __name__ == "__main__":
    main()
