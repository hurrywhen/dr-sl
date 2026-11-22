#!/usr/bin/env python3
"""Round-3 stratified / calibration / mechanism analyses (protocol v3).

Composes the corrected tied-rank calibration, Wilson intervals for every
FalseRelease, the utility-fallback mechanism analysis, post-hoc coverage-gate
evaluation, and the round-3 experiment summaries into one audit file.
No new model calls are made here.
"""
import hashlib
import json
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "dataset"))

from qi import load_dataset
from revision_stats import wilson_interval
from revision_stratified import (audit_coverage, calibration, gold_stratum,
                                 online_stratified, per_type_recall,
                                 stratify_offline)
from runtime import MIXED_TASK_TYPES, gold_entities
from runtime_extractor import runtime_extract
from runtime_extractor_fixed import runtime_extract_fixed

ROOT = Path(__file__).resolve().parent.parent
R2 = ROOT / "results" / "revision_20261121"
OUT = ROOT / "results" / "revision_round3"
SEED = 20261121


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def add_wilson(strat):
    """Attach Wilson CIs to FalseRelease fields of a stratified block."""
    for label in ("ALL", "PASS", "INFEASIBLE"):
        d = strat.get(label, {})
        if d.get("n") and "gold_residue_instances" in d:
            d["gold_residue_fraction_wilson95"] = list(
                wilson_interval(d["gold_residue_instances"], d["n"]))
    for dom, d in strat.get("by_domain", {}).items():
        p = d.get("PASS", {})
        if p.get("n"):
            d["FalseRelease_gold_wilson95"] = list(
                wilson_interval(p.get("gold_residue_instances", 0), p["n"]))
    return strat


def fallback_analysis(rows, items):
    """Utility-gate fallback mechanism (protocol v3 §5).

    harmful fallback: gold task-relevant attributes exist but NONE extracted,
    so local utility falls back to context retention.  benign fallback: the
    instance has no gold task-relevant attributes at all.
    """
    out = {}
    for method in ("closed_loop", "generalization_only"):
        rs = [r for r in rows if r["method"] == method]
        n = len(rs)
        recs = []
        for r in rs:
            it = items[r["id"]]
            gold = gold_entities(it)
            gt = [e for e in gold if e.get("task_relevant")]
            rv = {e["value"] for e in r["runtime_entities"]}
            has_task = any(e["type"] in MIXED_TASK_TYPES.get(r["domain"], set())
                           for e in r["runtime_entities"])
            task_found = sum(1 for e in gt if e["value"] in rv)
            recs.append({
                "id": r["id"], "domain": r["domain"], "release": r["release"],
                "residue": r["gold_literal_hits"] > 0,
                "recall": r["recall"],
                "task_recall": task_found / len(gt) if gt else None,
                "n_gold_task": len(gt),
                "fallback": not has_task,
                "harmful_fallback": (not has_task) and len(gt) > 0,
                "benign_fallback": (not has_task) and len(gt) == 0,
            })
        rel = [x for x in recs if x["release"]]
        hf = [x for x in recs if x["harmful_fallback"]]
        hf_rel = [x for x in hf if x["release"]]
        non_hf_rel = [x for x in rel if not x["harmful_fallback"]]
        tr = [x["task_recall"] for x in recs if x["task_recall"] is not None]
        out[method] = {
            "n": n,
            "mean_attribute_recall": sum(x["recall"] for x in recs) / n,
            "mean_task_relevant_recall": sum(tr) / len(tr) if tr else None,
            "fallback_fraction": sum(x["fallback"] for x in recs) / n,
            "harmful_fallback_fraction": sum(x["harmful_fallback"] for x in recs) / n,
            "benign_fallback_fraction": sum(x["benign_fallback"] for x in recs) / n,
            "n_released": len(rel),
            "released_via_harmful_fallback": len(hf_rel),
            "released_via_harmful_fallback_fraction_of_released": len(hf_rel) / len(rel) if rel else None,
            "FalseRelease_gold_harmful_fallback_released": (
                sum(x["residue"] for x in hf_rel) / len(hf_rel)) if hf_rel else None,
            "FalseRelease_gold_other_released": (
                sum(x["residue"] for x in non_hf_rel) / len(non_hf_rel)) if non_hf_rel else None,
            "by_domain_harmful_fallback": {
                d: {"n": sum(1 for x in recs if x["domain"] == d),
                    "harmful_fallback": sum(1 for x in recs if x["domain"] == d and x["harmful_fallback"]),
                    "released": sum(1 for x in recs if x["domain"] == d and x["release"])}
                for d in sorted({x["domain"] for x in recs})},
        }
    return out


def coverage_gate_posthoc(rows):
    """UNSCORABLE when no runtime task attribute extracted (human routing)."""
    out = {}
    for method in ("closed_loop", "generalization_only"):
        rs = [r for r in rows if r["method"] == method]
        gated_rel, base_rel = [], []
        for r in rs:
            has_task = any(e["type"] in MIXED_TASK_TYPES.get(r["domain"], set())
                           for e in r["runtime_entities"])
            if r["release"]:
                base_rel.append(r)
                if has_task:
                    gated_rel.append(r)
        n = len(rs)
        fr = lambda xs: (sum(1 for r in xs if r["gold_literal_hits"] > 0) / len(xs)) if xs else None
        out[method] = {
            "n": n,
            "release_rate_base": len(base_rel) / n,
            "release_rate_covgate": len(gated_rel) / n,
            "n_unscorable": len(base_rel) - len(gated_rel),
            "FalseRelease_gold_base": fr(base_rel),
            "FalseRelease_gold_base_wilson95": list(wilson_interval(
                sum(1 for r in base_rel if r["gold_literal_hits"] > 0), len(base_rel))) if base_rel else None,
            "FalseRelease_gold_covgate": fr(gated_rel),
            "FalseRelease_gold_covgate_wilson95": list(wilson_interval(
                sum(1 for r in gated_rel if r["gold_literal_hits"] > 0), len(gated_rel))) if gated_rel else None,
        }
    return out


def online_wilson(strat):
    for label in ("ALL", "PASS", "INFEASIBLE"):
        d = strat.get(label, {})
        if d.get("n") and "external_hit_instances" in d:
            d["FalseRelease_external_wilson95"] = list(
                wilson_interval(d["external_hit_instances"], d["n"]))
    return strat


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    offline2 = [json.loads(l) for l in (R2 / "offline_runtime.jsonl").open(encoding="utf-8")]
    items1 = {r["id"]: r for r in load_dataset(str(ROOT / "dataset/output/dr_sl_holdout_v1.jsonl"))}
    items2 = {r["id"]: r for r in load_dataset(str(ROOT / "dataset/output/dr_sl_holdout_v2.jsonl"))}
    result = {"seed": SEED, "spearman": "average_tied_ranks (round-3 correction)",
              "offline": {}, "mechanism": {}, "coverage_gate_posthoc": {}}

    for ds, items in (("holdout80", items1), ("holdout80_v2", items2)):
        rows = [r for r in offline2 if r["dataset"] == ds and r["sensitive_set"] == "runtime"]
        result["offline"][ds] = {
            "closed_loop": add_wilson(stratify_offline(rows, "closed_loop")),
            "generalization_only": add_wilson(stratify_offline(rows, "generalization_only")),
        }
        result["mechanism"][ds] = fallback_analysis(rows, items)
        result["coverage_gate_posthoc"][ds] = coverage_gate_posthoc(rows)

    result["per_type_recall"] = {
        "holdout80_original": per_type_recall(list(items1.values()), runtime_extract, gold_entities),
        "holdout80_v2_original": per_type_recall(list(items2.values()), runtime_extract, gold_entities),
        "holdout80_fixed_diagnostic": per_type_recall(list(items1.values()), runtime_extract_fixed, gold_entities),
        "holdout80_v2_fixed_diagnostic": per_type_recall(list(items2.values()), runtime_extract_fixed, gold_entities),
    }

    # Corrected calibration on round-2 holdout-1 online judge pairs.
    raw = [json.loads(l) for l in (R2 / "online_audit_raw.jsonl").open(encoding="utf-8")]
    atk = [r for r in raw if r["kind"] == "attack" and not r.get("error") and r["id"] in items1]
    jud = [r for r in raw if r["kind"] == "judge" and not r.get("error") and r["id"] in items1]
    local_rows = {(r["id"], r["method"]): r for r in offline2
                  if r["dataset"] == "holdout80" and r["sensitive_set"] == "runtime"}
    subset = json.loads((R2 / "audit_subset.json").read_text())
    result["audit_coverage"] = audit_coverage(atk, jud, items1, subset)
    result["online_stratified"] = {m: online_wilson(online_stratified(atk, jud, local_rows, m))
                                   for m in sorted({r["method"] for r in atk})}
    result["calibration"] = calibration(jud, local_rows)

    # holdout-2 online subset (small n; Wilson intervals mandatory).
    atk2 = [r for r in raw if r["kind"] == "attack" and not r.get("error") and r["id"] in items2]
    jud2 = [r for r in raw if r["kind"] == "judge" and not r.get("error") and r["id"] in items2]
    if atk2:
        local2 = {(r["id"], r["method"]): r for r in offline2
                  if r["dataset"] == "holdout80_v2" and r["sensitive_set"] == "runtime"}
        sub2 = sorted({r["id"] for r in atk2})
        result["holdout2_online"] = {
            "coverage": audit_coverage(atk2, jud2, items2, sub2),
            "stratified": {m: online_wilson(online_stratified(atk2, jud2, local2, m))
                           for m in sorted({r["method"] for r in atk2})},
            "caution": "20-instance subset; point estimates carry wide Wilson intervals",
        }

    # Round-3/4 experiment outputs (embedded when present).
    for name in ("offline_h3_summary.json", "downstream_summary.json",
                 "online_open_summary.json", "residual_probe.json",
                 "neural_extractor_summary.json"):
        p = OUT / name
        if p.exists():
            key = name.replace(".json", "")
            data = json.loads(p.read_text())
            if key == "residual_probe":
                data = {k: v for k, v in data.items() if k != "probes"}
            if key == "downstream_summary":
                data = {k: v for k, v in data.items() if k != "errors"}
            if key == "online_open_summary":
                data = {k: v for k, v in data.items() if k != "errors"}
            if key == "neural_extractor_summary":
                data = {k: v for k, v in data.items() if k != "errors"}
            result[key] = data

    # Open-ended attack stratified by local decision (FR_open-ended | PASS).
    openp = OUT / "online_open_raw.jsonl"
    if openp.exists():
        oraw = [json.loads(l) for l in openp.open(encoding="utf-8") if l.strip()]
        oraw = [r for r in oraw if not r.get("error")]
        ostrat = {}
        for m in sorted({r["method"] for r in oraw}):
            rs = [r for r in oraw if r["method"] == m]
            block = {}
            for label, sub in (("ALL", rs),
                               ("PASS", [r for r in rs if local_rows.get((r["id"], m), {}).get("release")]),
                               ("INFEASIBLE", [r for r in rs if not local_rows.get((r["id"], m), {}).get("release")])):
                if not sub:
                    block[label] = {"n": 0}
                    continue
                hit = sum(1 for r in sub if r["hits"] > 0)
                block[label] = {"n": len(sub), "instances_with_hit": hit,
                                "FR_open_ended": hit / len(sub),
                                "FR_open_ended_wilson95": list(wilson_interval(hit, len(sub))),
                                "mean_L": sum(r["L"] for r in sub) / len(sub)}
            ostrat[m] = block
        result["open_attack_stratified"] = ostrat

    # Freeze manifest for round-3 code/data.
    files = [
        "revision_protocol_v3.md", "revision_protocol_v4.md",
        "dataset/generate_holdout.py", "dataset/generate_holdout2.py",
        "dataset/generate_holdout3.py", "dataset/generate_drift_series.py",
        "dataset/vocab_mix.py", "dataset/synth_values.py", "dataset/synth_values_v2.py",
        "dataset/output/dr_sl_holdout_v1.jsonl", "dataset/output/dr_sl_holdout_v2.jsonl",
        "dataset/output/dr_sl_holdout_v3.jsonl",
        "dataset/output/dr_sl_drift_p000.jsonl", "dataset/output/dr_sl_drift_p025.jsonl",
        "dataset/output/dr_sl_drift_p050.jsonl", "dataset/output/dr_sl_drift_p075.jsonl",
        "dataset/output/dr_sl_drift_p100.jsonl",
        "sim/runtime.py", "sim/runtime_extractor.py", "sim/runtime_extractor_fixed.py",
        "sim/loop.py", "sim/pipeline.py", "sim/revision_stats.py",
        "sim/revision_stratified.py", "sim/revision_stratified_v3.py",
        "sim/revision_experiment.py",
        "sim/revision_h3_experiment.py", "sim/revision_downstream.py",
        "sim/revision_open_attack.py", "sim/revision_residual_probe.py",
        "sim/revision_neural_extractor.py",
        "sim/make_revision_tables.py", "sim/make_journal_version.py",
        "sim/test_spearman_ties.py", "sim/test_task_fields.py",
        "sim/test_extractor_fixed.py", "sim/test_revision_stats.py",
        "sim/test_neural_parser.py",
    ]
    result["freeze_manifest"] = {f: sha(ROOT / f) for f in files}
    (OUT / "stratified_summary.json").write_text(json.dumps(result, ensure_ascii=False, indent=2))

    # Console digest.
    o = result["calibration"]["overall"]
    print("corrected calibration rho", round(o["rho"]["estimate"], 3), o["rho"]["ci95"],
          "mae", round(o["mae"]["estimate"], 3), "agree", round(o["threshold_agreement"]["estimate"], 3))
    for m, v in result["calibration"]["by_method"].items():
        print(f"  {m}: rho={v['point']['rho']:.3f}")
    for ds in ("holdout80", "holdout80_v2"):
        fb = result["mechanism"][ds]["closed_loop"]
        print(ds, "closed_loop fallback:", round(fb["fallback_fraction"], 3),
              "harmful:", round(fb["harmful_fallback_fraction"], 3),
              "task_recall:", round(fb["mean_task_relevant_recall"], 3),
              "released_via_harmful:", fb["released_via_harmful_fallback"], "/", fb["n_released"])
        cg = result["coverage_gate_posthoc"][ds]["closed_loop"]
        print("  covgate release", round(cg["release_rate_base"], 3), "->",
              round(cg["release_rate_covgate"], 3), "FR", cg["FalseRelease_gold_base"], "->",
              cg["FalseRelease_gold_covgate"])
    print("wrote", OUT / "stratified_summary.json")


if __name__ == "__main__":
    main()
