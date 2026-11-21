#!/usr/bin/env python3
"""Round-3 offline experiments (protocol v3 §3-§5).  No LLM calls.

- holdout-3 (natural vocab mix): original AND fixed extractor x 5 methods,
  plus coverage-gate variants (UNSCORABLE when no task attribute extracted).
- holdout-1/2 with the fixed extractor: DIAGNOSTIC only (defects discovered
  there; confirmatory contrast is holdout-3).
- drift series (5 overlap levels): original extractor, closed_loop.

Enriched fields: extractor variant, utility basis (task attributes vs context
fallback), task-relevant gold recall, artifact hash.  Gold annotations are read
only by external scoring after artifacts/decisions are frozen.
"""
import hashlib
import json
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "dataset"))

from qi import load_dataset
from revision_stats import cluster_bootstrap, paired_cluster_delta, wilson_interval
from runtime import (MIXED_TASK_TYPES, build_artifact, external_gold_audit,
                     gold_entities, local_utility, runtime_view,
                     run_runtime_item, stable_decision)
from runtime_extractor import runtime_extract
from runtime_extractor_fixed import runtime_extract_fixed

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "results" / "revision_round3"
METHODS = ("hardline_only", "generalization_only", "closed_loop",
           "intact_style", "prism_random")
EXTRACTORS = {"original": runtime_extract, "fixed": runtime_extract_fixed}


def sha(s):
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def audit_with_task(item, D, ents):
    a = external_gold_audit(item, D, ents)
    gold = gold_entities(item)
    gt = [e for e in gold if e.get("task_relevant")]
    rv = {e["value"] for e in ents}
    found = sum(1 for e in gt if e["value"] in rv)
    a["n_gold_task"] = len(gt)
    a["task_recall"] = found / len(gt) if gt else None
    return a


def run_row(item, method, extract_fn, extractor_name, dataset):
    ents = extract_fn(item["prompt"])
    r = run_runtime_item(item, method=method, task_profile="mixed", entities=ents)
    view = runtime_view(item, ents, task_profile="mixed")
    util = local_utility(view, r["D"])
    audit = audit_with_task(item, r["D"], ents)
    row = {"dataset": dataset, "extractor": extractor_name, "sensitive_set": "runtime",
           **r, **audit,
           "U_basis": util["basis"],
           "utility_fallback": util["basis"] == "non_sensitive_context",
           "artifact_sha256": sha(r["D"])}
    # Coverage-gate variant: declared task profile expects attributes, but none
    # extracted -> UNSCORABLE, no automatic release (human routing).
    if method in ("closed_loop", "generalization_only"):
        has_task = any(e["type"] in MIXED_TASK_TYPES.get(item["domain"], set())
                       for e in ents)
        gated = dict(row)
        gated["method"] = method + "_covgate"
        if not has_task:
            gated.update({"status": "UNSCORABLE", "release": False,
                          "coverage_gate": "no_task_attributes_extracted"})
        else:
            gated["coverage_gate"] = "ok"
        return [row, gated]
    return [row]


def summarize(rows):
    out = {}
    groups = defaultdict(list)
    for r in rows:
        groups[(r["dataset"], r["extractor"], r["method"])].append(r)
    for (ds, ex, m), rs in sorted(groups.items()):
        n = len(rs)
        rel = [r for r in rs if r["release"]]
        with_res_pass = sum(1 for r in rel if r["gold_literal_hits"] > 0)
        tr = [r["task_recall"] for r in rs if r["task_recall"] is not None]
        out[f"{ds}/{ex}/{m}"] = {
            "n": n,
            "release_rate": len(rel) / n,
            "release_rate_wilson95": list(wilson_interval(len(rel), n)),
            "gold_L": cluster_bootstrap({r["id"]: r["gold_L"] for r in rs}),
            "recall": cluster_bootstrap({r["id"]: r["recall"] for r in rs}),
            "task_recall": cluster_bootstrap({r["id"]: r["task_recall"]
                                              for r in rs if r["task_recall"] is not None}) if tr else None,
            "U_local": cluster_bootstrap({r["id"]: r["U_local"] for r in rs}),
            "utility_fallback_fraction": sum(1 for r in rs if r["utility_fallback"]) / n,
            "n_pass": len(rel),
            "pass_with_gold_residue": with_res_pass,
            "FalseRelease_gold": with_res_pass / len(rel) if rel else None,
            "FalseRelease_gold_wilson95": list(wilson_interval(with_res_pass, len(rel))) if rel else None,
        }
    return out


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    rows = []
    h3 = load_dataset(str(ROOT / "dataset/output/dr_sl_holdout_v3.jsonl"))
    for item in h3:
        for ex_name, fn in EXTRACTORS.items():
            for m in METHODS:
                rows.extend(run_row(item, m, fn, ex_name, "holdout80_v3"))
    # Diagnostic fixed-extractor runs on holdout-1/2 (not confirmatory).
    for ds, fname in (("holdout80", "dr_sl_holdout_v1.jsonl"),
                      ("holdout80_v2", "dr_sl_holdout_v2.jsonl")):
        for item in load_dataset(str(ROOT / "dataset/output" / fname)):
            for m in ("closed_loop", "generalization_only"):
                rows.extend(run_row(item, m, runtime_extract_fixed, "fixed",
                                    ds + "_diag_fixed"))
    # Dose-response drift series: original extractor, closed_loop.
    drift = {}
    for tag in ("p000", "p025", "p050", "p075", "p100"):
        items = load_dataset(str(ROOT / f"dataset/output/dr_sl_drift_{tag}.jsonl"))
        ds = f"drift_{tag}"
        for item in items:
            rows.extend(run_row(item, "closed_loop", runtime_extract, "original", ds))
        rs = [r for r in rows if r["dataset"] == ds and r["method"] == "closed_loop"]
        rel = [r for r in rs if r["release"]]
        wr = sum(1 for r in rel if r["gold_literal_hits"] > 0)
        drift[tag] = {
            "n": len(rs),
            "nominal_p_old": items[0]["nominal_old_vocab_prob"],
            "realized_old_vocab_fraction": sum(
                it["realized_old_vocab_fraction"] for it in items) / len(items),
            "recall": sum(r["recall"] for r in rs) / len(rs),
            "task_recall": sum(r["task_recall"] for r in rs if r["task_recall"] is not None)
                           / max(1, sum(1 for r in rs if r["task_recall"] is not None)),
            "release_rate": len(rel) / len(rs),
            "FalseRelease_gold": wr / len(rel) if rel else None,
            "FalseRelease_gold_wilson95": list(wilson_interval(wr, len(rel))) if rel else None,
            "gold_L": sum(r["gold_L"] for r in rs) / len(rs),
            "utility_fallback_fraction": sum(1 for r in rs if r["utility_fallback"]) / len(rs),
        }
    with (OUT / "offline_h3.jsonl").open("w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    summary = {"methods": summarize(rows), "dose_response": drift,
               "scope": "round-3 offline; deterministic track; original extractor frozen, "
                        "fixed variant fixes clear defects only (no lexicon additions)"}
    # Paired closed-generalization on holdout-3 per extractor.
    paired = {}
    for ex in EXTRACTORS:
        for m_pair in (("closed_loop", "generalization_only"),):
            a = {r["id"]: r for r in rows if r["dataset"] == "holdout80_v3"
                 and r["extractor"] == ex and r["method"] == m_pair[0]}
            b = {r["id"]: r for r in rows if r["dataset"] == "holdout80_v3"
                 and r["extractor"] == ex and r["method"] == m_pair[1]}
            ids = sorted(set(a) & set(b))
            paired[f"holdout80_v3/{ex}"] = {
                "release_delta": paired_cluster_delta({i: float(a[i]["release"]) for i in ids},
                                                      {i: float(b[i]["release"]) for i in ids}),
                "gold_L_delta": paired_cluster_delta({i: a[i]["gold_L"] for i in ids},
                                                     {i: b[i]["gold_L"] for i in ids}),
                "U_delta": paired_cluster_delta({i: a[i]["U_local"] for i in ids},
                                                {i: b[i]["U_local"] for i in ids}),
            }
    summary["paired"] = paired
    (OUT / "offline_h3_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2))
    for k in ("holdout80_v3/original/closed_loop", "holdout80_v3/fixed/closed_loop",
              "holdout80_v3/original/closed_loop_covgate", "holdout80_v3/fixed/closed_loop_covgate",
              "holdout80_diag_fixed/fixed/closed_loop",
              "holdout80_v2_diag_fixed/fixed/closed_loop"):
        v = summary["methods"][k]
        print(f"{k}: release={v['release_rate']:.3f} FR_gold={v['FalseRelease_gold']} "
              f"recall={v['recall']['estimate']:.3f} task_recall="
              f"{v['task_recall']['estimate'] if v['task_recall'] else None} "
              f"fallback={v['utility_fallback_fraction']:.3f}")
    print("dose-response:", json.dumps({k: {kk: round(vv, 3) if isinstance(vv, float) else vv
                                           for kk, vv in v.items() if kk in
                                           ('realized_old_vocab_fraction', 'recall', 'release_rate',
                                            'FalseRelease_gold', 'utility_fallback_fraction')}
                                       for k, v in drift.items()}, ensure_ascii=False))
    print("wrote", OUT / "offline_h3.jsonl", "rows:", len(rows))


if __name__ == "__main__":
    main()
