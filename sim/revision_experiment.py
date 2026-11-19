#!/usr/bin/env python3
"""Offline revised runtime-S evaluation (no LLM calls).

Runs the frozen deterministic local track on development test-160, mixed-120,
and the untouched holdout.  Gold annotations are used only by
``external_gold_audit`` after artifacts and local decisions are frozen.
"""
import hashlib
import json
import os
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "dataset"))

from qi import load_dataset
from runtime import (build_artifact, external_gold_audit, gold_entities,
                     run_runtime_item, stable_decision)
from runtime_extractor import runtime_extract
from revision_stats import cluster_bootstrap, paired_cluster_delta, wilson_interval

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "results" / os.environ.get("REVISION_OUT", "revision_20261118")
METHODS = ("hardline_only", "generalization_only", "closed_loop",
           "intact_style", "prism_random")


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def freeze_manifest():
    files = [
        ROOT / "revision_protocol.md",
        ROOT / "dataset" / "generate_holdout.py",
        ROOT / "sim" / "runtime.py",
        ROOT / "sim" / "runtime_extractor.py",
        ROOT / "sim" / "revision_stats.py",
        ROOT / "sim" / "revision_experiment.py",
        ROOT / "sim" / "loop.py",
        ROOT / "sim" / "pipeline.py",
    ]
    return {str(p.relative_to(ROOT)): sha256(p) for p in files if p.exists()}


def oracle_view(item):
    ents = gold_entities(item)
    return {"prompt": item["prompt"], "domain": item["domain"],
            "annotations": item["annotations"], "runtime_entities": ents}


def run_oracle(item, method):
    view = oracle_view(item)
    art = build_artifact(method, view)
    decision = art.get("final_stable") or stable_decision(view, art["D"])
    if art.get("status_override"):
        decision = {**decision, "status": art["status_override"],
                    "release": art["status_override"] == "PASS"}
    return {"id": item["id"], "domain": item["domain"], "method": method,
            "sensitive_set": "oracle_gold", "D": art["D"],
            "status": decision["status"], "release": decision["release"],
            "L_local": decision["L"], "U_local": decision["U"],
            "hits_local": decision["hits"], "n_probes_local": decision["n_probes"],
            "stable": decision["stable"], "method_detail": art["method_detail"],
            "loop_rounds": art.get("loop_rounds"),
            "n_runtime_entities": len(view["runtime_entities"])}


def summarize(rows):
    by = defaultdict(list)
    for r in rows:
        by[(r["dataset"], r["sensitive_set"], r["method"])].append(r)
    summary = {}
    for (dataset, sset, method), rs in sorted(by.items()):
        n = len(rs)
        rel = sum(1 for r in rs if r["release"])
        rel_ci = wilson_interval(rel, n)
        key = f"{dataset}/{sset}/{method}"
        summary[key] = {
            "n": n, "release_rate": rel / n if n else None,
            "release_wilson95": list(rel_ci),
            "L_local": cluster_bootstrap({r["id"]: r["L_local"] for r in rs}),
            "U_local": cluster_bootstrap({r["id"]: r["U_local"] for r in rs if r["U_local"] is not None}),
            "gold_L": cluster_bootstrap({r["id"]: r["gold_L"] for r in rs}),
            "recall": cluster_bootstrap({r["id"]: r["recall"] for r in rs}),
            "over_extraction": cluster_bootstrap({r["id"]: r["over_extraction"] for r in rs}),
            "missed_gold_instances": sum(1 for r in rs if r["missed_gold_values"]),
            "gold_literal_hit_instances": sum(1 for r in rs if r["gold_literal_hits"] > 0),
        }
    # Paired release/utility deltas: closed_loop vs generalization_only.
    paired = {}
    for dataset in {r["dataset"] for r in rows}:
        for sset in {r["sensitive_set"] for r in rows if r["dataset"] == dataset}:
            a = {r["id"]: r for r in rows if r["dataset"] == dataset and r["sensitive_set"] == sset and r["method"] == "generalization_only"}
            b = {r["id"]: r for r in rows if r["dataset"] == dataset and r["sensitive_set"] == sset and r["method"] == "closed_loop"}
            common = sorted(set(a) & set(b))
            if common:
                paired[f"{dataset}/{sset}/closed_loop_minus_generalization"] = {
                    "release_delta": paired_cluster_delta({i: int(a[i]["release"]) for i in common},
                                                          {i: int(b[i]["release"]) for i in common}),
                    "U_delta": paired_cluster_delta({i: a[i]["U_local"] for i in common},
                                                    {i: b[i]["U_local"] for i in common}),
                    "gold_L_delta": paired_cluster_delta({i: a[i]["gold_L"] for i in common},
                                                         {i: b[i]["gold_L"] for i in common}),
                }
    return {"methods": summary, "paired": paired}


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    manifest = freeze_manifest()
    (OUT / "freeze_manifest.json").write_text(json.dumps(manifest, indent=2))

    datasets = [
        ("test160", ROOT / "dataset" / "output" / "dr_sl_dataset_v2.jsonl", "test", "all_quasi"),
        ("mixed120", ROOT / "dataset" / "output" / "dr_sl_mixed.jsonl", None, "mixed"),
        ("holdout80", ROOT / "dataset" / "output" / "dr_sl_holdout_v1.jsonl", None, "mixed"),
    ]
    rows = []
    for name, path, split, profile in datasets:
        if not path.exists():
            print(f"skip missing {path}")
            continue
        items = load_dataset(str(path))
        if split:
            items = [r for r in items if r["split"] == split]
        for item in items:
            ents = runtime_extract(item["prompt"])
            for method in METHODS:
                r = run_runtime_item(item, method=method, task_profile=profile, entities=ents)
                audit = external_gold_audit(item, r["D"], ents)
                rows.append({"dataset": name, "sensitive_set": "runtime", **r, **audit})
            # Oracle-S upper-bound track on development sets only.
            if name != "holdout80":
                for method in METHODS:
                    r = run_oracle(item, method)
                    audit = external_gold_audit(item, r["D"], gold_entities(item))
                    rows.append({"dataset": name, "sensitive_set": "oracle", **r, **audit})
    with (OUT / "offline_runtime.jsonl").open("w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    summary = summarize(rows)
    summary["freeze_manifest"] = manifest
    summary["scope"] = "deterministic local runtime-S track; no neural local-LLM rerun"
    (OUT / "offline_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2))
    print(json.dumps({k: {"n": v["n"], "release": v["release_rate"],
                           "gold_L": v["gold_L"]["estimate"] if v["gold_L"] else None,
                           "recall": v["recall"]["estimate"] if v["recall"] else None}
                      for k, v in summary["methods"].items()}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
