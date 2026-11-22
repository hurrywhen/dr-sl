#!/usr/bin/env python3
"""Pooled 60-instance subset metrics for the round-5 stability/family conditions
(protocol v5 §2–§3), including the round-4 run restricted to the same subset as
the reference.  Recomputation from archived rows only; no API calls.  Writes
neural_round5_subset.json (embedded by the stratified summary; used by the
stability table).  Descriptive subset estimates, NOT population CIs for the
full contrast.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "dataset"))

from revision_neural_extractor import TYPES
from revision_neural_analysis import (char_coverage, fr_decomposition,
                                      load_items, gold_type_map)
from revision_neural_round5 import select_subset
from revision_stats import cluster_bootstrap, wilson_interval

ROOT = Path(__file__).resolve().parent.parent
R3 = ROOT / "results" / "revision_round3"
FILES = {"holdout80": "dr_sl_holdout_v1.jsonl",
         "holdout80_v3": "dr_sl_holdout_v3.jsonl",
         "drift_p000": "dr_sl_drift_p000.jsonl"}


def pooled(cl_rows, items, types):
    n = len(cl_rows)
    rel = [r for r in cl_rows if r["release"]]
    wr = sum(1 for r in rel if r["gold_literal_hits"] > 0)
    dec = fr_decomposition(cl_rows, items, types)
    return {"n": n,
            "recall": cluster_bootstrap({r["id"]: r["recall"] for r in cl_rows}),
            "char_coverage": cluster_bootstrap(
                {r["id"]: char_coverage(items[r["id"]], r["runtime_entities"]) for r in cl_rows}),
            "release_rate": len(rel) / n,
            "FalseRelease_gold": {"k": wr, "n": len(rel),
                                  "rate": wr / len(rel) if rel else None,
                                  "wilson95": list(wilson_interval(wr, len(rel))) if rel else None},
            "FR_taxonomy_gap_k": dec["FR_taxonomy_gap"]["k"],
            "FR_declared_type_miss_k": dec["FR_declared_type_miss"]["k"],
            "residual_value_types": dec["residual_value_types"],
            "fr_ids": sorted(r["id"] for r in rel if r["gold_literal_hits"] > 0)}


def main():
    subset = select_subset()
    items = {}
    for ds, fname in FILES.items():
        items.update(load_items(fname))
    sub_ids = {it["id"] for _, it in subset}

    r4 = [json.loads(l) for l in (R3 / "neural_extractor_rows.jsonl").open(encoding="utf-8")]
    r5 = [json.loads(l) for l in (R3 / "neural_round5_rows.jsonl").open(encoding="utf-8")]
    out = {"subset_rule": "first 5 per domain in sorted-id order, 20/dataset, 60 total",
           "note": "descriptive subset estimates; instance-level intervals; not population CIs",
           "conditions": {}}
    cl4 = [r for r in r4 if r["method"] == "closed_loop" and r["id"] in sub_ids]
    assert len(cl4) == 60
    out["conditions"]["round4_ref"] = pooled(cl4, items, TYPES)
    out["conditions"]["round4_ref"]["model"] = "qwen3.8-max"
    out["conditions"]["round4_ref"]["seed_submitted"] = 20261124
    for cond in ("stability_r1", "stability_r2", "family_glm"):
        cl = [r for r in r5 if r["condition"] == cond and r["method"] == "closed_loop"]
        assert len(cl) == 60, (cond, len(cl))
        out["conditions"][cond] = pooled(cl, items, TYPES)
    s5 = json.loads((R3 / "neural_round5_summary.json").read_text())
    for cond in ("stability_r1", "stability_r2", "family_glm"):
        out["conditions"][cond]["model"] = s5["conditions"][cond]["model"]
        out["conditions"][cond]["seed_submitted"] = s5["conditions"][cond]["seed_submitted"]
        out["conditions"][cond]["stability_vs_round4"] = \
            s5["stability"][cond]["vs_round4_seed20261124"]
    out["r1_vs_r2"] = s5["stability"]["r1_vs_r2"]
    (R3 / "neural_round5_subset.json").write_text(json.dumps(out, ensure_ascii=False, indent=2))
    for cond, b in out["conditions"].items():
        print(f"{cond}: recall={b['recall']['estimate']:.3f} charcov={b['char_coverage']['estimate']:.3f} "
              f"rel={b['release_rate']:.3f} FR={b['FalseRelease_gold']['k']}/{b['FalseRelease_gold']['n']} "
              f"(gap {b['FR_taxonomy_gap_k']}/decl {b['FR_declared_type_miss_k']}) ids={b['fr_ids']}")
    print("wrote", R3 / "neural_round5_subset.json")


if __name__ == "__main__":
    main()
