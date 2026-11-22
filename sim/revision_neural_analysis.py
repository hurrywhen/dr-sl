#!/usr/bin/env python3
"""Round-5 P0 re-analysis of the ROUND-4 neural-extractor archive (protocol v5 §1).

No API calls.  Reads the byte-intact round-4 archive
(neural_extraction_cache.jsonl / neural_extractor_rows.jsonl) and recomputes:

1. FR decomposition by failure source: taxonomy-gap (residual gold type NOT in
   the frozen declared taxonomy) vs declared-type miss (type declared).  The
   round-4 taxonomy omitted THREE types (room_no, marriage_years, work_years)
   on holdout-1/drift-p000; holdout-3's gold types are fully declared.
2. Three coverage layers, reported separately:
   - exact gold-span recall (value-based, the round-4 `recall`);
   - sensitive character coverage: fraction of gold-entity characters covered
     by the union of extracted spans (partial-span extraction, e.g. income
     `1.2万元` inside gold `月收入约1.2万元`, covers the sensitive content);
   - final gold-literal residue (gold_L / FR, unchanged).
3. Partial-span-only gold value counts and unlocatable/unknown-type counts
   (round 4: n_unlocatable = 0 — income proposals are verbatim proper
   substrings, NOT non-verbatim output).
4. Declared-type-miss characterization: was the residual gold value ever
   proposed (under any type), or only a proper substring of it?

Bound scoping (protocol v5 §1.3): exact-span recall is a conservative
measurement under the current prompt/taxonomy; FR is conditional on the
incomplete taxonomy with NO general bound direction (omitted types can RAISE
FR).  This script makes no lower-bound claim about FR.

Shared helpers are imported by sim/revision_neural_round5.py.
"""
import hashlib
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "dataset"))

from qi import load_dataset
from revision_neural_extractor import TYPES, parse_proposals
from revision_stats import cluster_bootstrap, wilson_interval
from runtime import gold_entities

ROOT = Path(__file__).resolve().parent.parent
R3 = ROOT / "results" / "revision_round3"
DATASETS = (("holdout80", "dr_sl_holdout_v1.jsonl"),
            ("holdout80_v3", "dr_sl_holdout_v3.jsonl"),
            ("drift_p000", "dr_sl_drift_p000.jsonl"))

# Documented per-dataset omission sets of the round-4 frozen taxonomy
# (protocol v5 §1.1; pinned by sim/test_neural_taxonomy.py).
DOCUMENTED_OMISSIONS = {
    "holdout80": {"room_no", "marriage_years", "work_years"},
    "holdout80_v3": set(),
    "drift_p000": {"room_no", "marriage_years", "work_years"},
}


def sha(s):
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def load_items(fname):
    return {it["id"]: it for it in load_dataset(str(ROOT / "dataset/output" / fname))}


def gold_type_map(item):
    return {e["value"]: e["type"] for e in gold_entities(item)}


def merged_spans(ents):
    spans = sorted((e["span"][0], e["span"][1]) for e in ents)
    out = []
    for s, t in spans:
        if out and s <= out[-1][1]:
            out[-1] = (out[-1][0], max(out[-1][1], t))
        else:
            out.append((s, t))
    return out


def char_coverage(item, ents):
    """Fraction of gold-entity characters covered by the union of extracted spans."""
    gold = (item["annotations"]["explicit_identifiers"]
            + item["annotations"]["quasi_identifiers"])
    union = merged_spans(ents)
    total = covered = 0
    for e in gold:
        s, t = e["span"]
        total += t - s
        for a, b in union:
            covered += max(0, min(t, b) - max(s, a))
    return covered / total if total else 1.0


def partial_span_values(item, ents):
    """Gold values not extracted in full but with >=1 extracted proper substring."""
    gv = {e["value"] for e in gold_entities(item)}
    ev = {e["value"] for e in ents}
    return sorted(v for v in gv
                  if v not in ev and any(p in v and p != v for p in ev))


def fr_decomposition(cl_rows, items, types, proposals_by_id=None):
    """Instance-level FR split among releases: taxonomy-gap vs declared-type miss.

    A released instance with residue can contribute to BOTH components if its
    residual values span both categories.  Wilson intervals at the
    independent-instance level (denominator = number of releases).
    """
    rel = [r for r in cl_rows if r["release"]]
    n = len(rel)
    gap, decl, both = [], [], []
    residual_types = Counter()
    decl_detail = []
    for r in rel:
        if r["gold_literal_hits"] == 0:
            continue
        tm = gold_type_map(items[r["id"]])
        ts = {tm[v] for v in r["gold_literal_hit_values"]}
        residual_types.update(tm[v] for v in r["gold_literal_hit_values"])
        g = any(t not in types for t in ts)
        d = any(t in types for t in ts)
        if g:
            gap.append(r["id"])
        if d:
            decl.append(r["id"])
        if g and d:
            both.append(r["id"])
        if d and proposals_by_id is not None:
            props = proposals_by_id.get(r["id"], [])
            pvals = {v for _, v in props}
            for v in r["gold_literal_hit_values"]:
                if tm[v] in types:
                    if v in pvals:
                        kind = "proposed_but_residue"  # should not happen (scrub)
                    elif any(p in v and p != v for p in pvals):
                        kind = "partial_substring_proposed"
                    else:
                        kind = "never_proposed"
                    decl_detail.append({"id": r["id"], "value": v,
                                        "type": tm[v], "kind": kind})
    wr = sum(1 for r in rel if r["gold_literal_hits"] > 0)

    def block(ids):
        return {"k": len(ids), "n": n,
                "rate": len(ids) / n if n else None,
                "wilson95": list(wilson_interval(len(ids), n)) if n else None,
                "ids": sorted(ids)}

    return {"n_pass": n,
            "FalseRelease_gold": {"k": wr, "n": n, "rate": wr / n if n else None,
                                  "wilson95": list(wilson_interval(wr, n)) if n else None},
            "FR_taxonomy_gap": block(gap),
            "FR_declared_type_miss": block(decl),
            "both_sources": sorted(both),
            "residual_value_types": dict(residual_types),
            "declared_miss_detail": decl_detail}


def coverage_block(cl_rows, items):
    """Three coverage layers + partial-span counts, per dataset (closed loop)."""
    cc, exact, partial_counts = {}, {}, []
    n_gold_values = n_partial_values = 0
    for r in cl_rows:
        it = items[r["id"]]
        ents = r["runtime_entities"]
        cc[r["id"]] = char_coverage(it, ents)
        exact[r["id"]] = r["recall"]
        pv = partial_span_values(it, ents)
        partial_counts.append({"id": r["id"], "n_partial": len(pv), "values": pv})
        n_gold_values += len(gold_type_map(it))
        n_partial_values += len(pv)
    return {"exact_span_recall": cluster_bootstrap(exact),
            "sensitive_char_coverage": cluster_bootstrap(cc),
            "gold_L": cluster_bootstrap({r["id"]: r["gold_L"] for r in cl_rows}),
            "n_gold_values": n_gold_values,
            "n_partial_span_only_values": n_partial_values,
            "partial_span_detail": [p for p in partial_counts if p["n_partial"]]}


def analyze_round4():
    rows = [json.loads(l) for l in (R3 / "neural_extractor_rows.jsonl").open(encoding="utf-8")]
    cache = {}
    for l in (R3 / "neural_extraction_cache.jsonl").open(encoding="utf-8"):
        r = json.loads(l)
        cache[r["prompt_sha256"]] = r
    out = {"protocol": "revision_protocol_v5.md §1 (P0 re-analysis; no new calls)",
           "archive": "round-4 neural_extractor_* kept byte-intact",
           "taxonomy_declared_n": len(TYPES),
           "bound_scoping": ("exact-span recall is conservative under the current "
                             "prompt/taxonomy; FR is conditional on the incomplete "
                             "taxonomy with no general bound direction"),
           "datasets": {}}
    for ds, fname in DATASETS:
        items = load_items(fname)
        gold_types = {t for it in items.values() for t in gold_type_map(it).values()}
        omitted = gold_types - TYPES
        assert omitted == DOCUMENTED_OMISSIONS[ds], (ds, omitted)
        cl = [r for r in rows if r["dataset"] == ds and r["method"] == "closed_loop"]
        proposals_by_id = {}
        for r in cl:
            c = cache[sha(items[r["id"]]["prompt"])]
            proposals_by_id[r["id"]], _ = parse_proposals(c["raw"])
        dec = fr_decomposition(cl, items, TYPES, proposals_by_id)
        cov = coverage_block(cl, items)
        out["datasets"][ds] = {
            "gold_types_not_declared": sorted(omitted),
            "fr_decomposition": dec,
            "coverage_layers": cov,
            "n_unlocatable": sum(cache[sha(it["prompt"])]["n_unlocatable"] for it in items.values()),
            "n_unknown_type": sum(cache[sha(it["prompt"])]["n_unknown_type"] for it in items.values()),
        }
    (R3 / "neural_extractor_analysis.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=2))
    for ds, b in out["datasets"].items():
        d = b["fr_decomposition"]
        print(f"{ds}: FR {d['FalseRelease_gold']['k']}/{d['n_pass']} | "
              f"gap {d['FR_taxonomy_gap']['k']} | declared {d['FR_declared_type_miss']['k']} | "
              f"residual types {d['residual_value_types']}")
        c = b["coverage_layers"]
        print(f"   exact recall {c['exact_span_recall']['estimate']:.3f} | "
              f"char coverage {c['sensitive_char_coverage']['estimate']:.3f} | "
              f"partial-span-only values {c['n_partial_span_only_values']}/{c['n_gold_values']} | "
              f"unlocatable {b['n_unlocatable']}")
        for dd in d["declared_miss_detail"]:
            print("   declared miss:", dd)
    print("wrote", R3 / "neural_extractor_analysis.json")


if __name__ == "__main__":
    analyze_round4()
