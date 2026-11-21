#!/usr/bin/env python3
"""Release-stratified risk, calibration and residual-report analyses (round 2).

Core Route-A analyses.  Reads the frozen offline rows and (when present) the
controlled-disclosure online raw outputs.  Everything is stratified by the local
decision (ALL / PASS / INFEASIBLE) and by domain; whole-set means are never the
only report.  No new model calls are made here.
"""
import json
import math
import os
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "dataset"))

from revision_stats import cluster_bootstrap, wilson_interval

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "results" / os.environ.get("REVISION_OUT", "revision_20261121")
SEED = 20261121
N_BOOT = 2000


def _mean(xs):
    xs = [x for x in xs if x is not None]
    return sum(xs) / len(xs) if xs else None


def average_ranks(xs):
    """1-based average ranks for tied values (standard Spearman convention).

    Double argsort assigns distinct ranks to equal values and is NOT valid when
    ties exist (round-2 bug; see revision_protocol_v3.md §1).
    """
    xs = list(xs)
    order = sorted(range(len(xs)), key=lambda i: xs[i])
    ranks = [0.0] * len(xs)
    i = 0
    while i < len(order):
        j = i
        while j + 1 < len(order) and xs[order[j + 1]] == xs[order[i]]:
            j += 1
        avg = (i + j) / 2.0 + 1.0  # mean of 1-based positions i+1 .. j+1
        for k in range(i, j + 1):
            ranks[order[k]] = avg
        i = j + 1
    return ranks


def spearman(x, y):
    x = np.asarray(x, float); y = np.asarray(y, float)
    if len(x) < 3 or x.std() == 0 or y.std() == 0:
        return None
    rx = np.asarray(average_ranks(x.tolist()))
    ry = np.asarray(average_ranks(y.tolist()))
    return float(np.corrcoef(rx, ry)[0, 1])


def cluster_stat(groups, stat_fn, n_boot=N_BOOT, seed=SEED):
    """Instance-cluster percentile bootstrap of an arbitrary row statistic.

    groups maps instance id -> list of rows.  Instances (with all their nested
    rows) are resampled; stat_fn is recomputed on the pooled resampled rows.
    """
    ids = sorted(groups)
    if not ids:
        return None
    point = stat_fn([r for i in ids for r in groups[i]])
    if len(ids) == 1:
        return {"estimate": point, "ci95": [point, point], "n_instances": 1,
                "n_boot": n_boot, "unit": "instance_cluster"}
    rng = np.random.default_rng(seed)
    boots = []
    for _ in range(n_boot):
        sampled = rng.integers(0, len(ids), size=len(ids))
        rows = [r for j in sampled for r in groups[ids[j]]]
        v = stat_fn(rows)
        if v is not None and not (isinstance(v, float) and math.isnan(v)):
            boots.append(v)
    if not boots:
        return {"estimate": point, "ci95": [None, None], "n_instances": len(ids),
                "n_boot": n_boot, "unit": "instance_cluster"}
    lo, hi = np.quantile(boots, [0.025, 0.975])
    return {"estimate": point, "ci95": [float(lo), float(hi)],
            "n_instances": len(ids), "n_boot": n_boot, "unit": "instance_cluster"}


def gold_stratum(rows):
    n = len(rows)
    if n == 0:
        return {"n": 0}
    with_res = sum(1 for r in rows if r["gold_literal_hits"] > 0)
    return {
        "n": n,
        "gold_residue_instances": with_res,
        "gold_residue_fraction": with_res / n,
        "gold_residue_fraction_wilson95": list(wilson_interval(with_res, n)),
        "mean_gold_L": _mean([r["gold_L"] for r in rows]),
        "mean_gold_L_ci": cluster_bootstrap({r["id"]: r["gold_L"] for r in rows}),
        "mean_recall": _mean([r["recall"] for r in rows]),
        "mean_U_local": _mean([r["U_local"] for r in rows]),
    }


def stratify_offline(rows, method):
    rs = [r for r in rows if r["method"] == method]
    out = {}
    for label, sub in (("ALL", rs),
                       ("PASS", [r for r in rs if r["release"]]),
                       ("INFEASIBLE", [r for r in rs if not r["release"]])):
        out[label] = gold_stratum(sub)
    # FalseRelease (gold-literal analogue): Pr(gold residue | local PASS)
    p = out["PASS"]
    out["FalseRelease_gold"] = p.get("gold_residue_fraction")
    out["by_domain"] = {}
    for d in sorted({r["domain"] for r in rs}):
        dr = [r for r in rs if r["domain"] == d]
        dp = [r for r in dr if r["release"]]
        out["by_domain"][d] = {
            "ALL": gold_stratum(dr), "PASS": gold_stratum(dp),
            "release_rate": len(dp) / len(dr) if dr else None,
            "FalseRelease_gold": (sum(1 for r in dp if r["gold_literal_hits"] > 0) / len(dp)) if dp else None,
        }
    return out


def per_type_recall(items, extract_fn, gold_fn):
    found = defaultdict(int); total = defaultdict(int)
    for it in items:
        ents = extract_fn(it["prompt"])
        rv = {e["value"] for e in ents}
        for g in gold_fn(it):
            total[g["type"]] += 1
            if g["value"] in rv:
                found[g["type"]] += 1
    return {t: {"recall": found[t] / total[t], "n": total[t]} for t in sorted(total)}


def residual_report_recall(rows):
    """How much of the true gold residue is named in runtime-S residual reports.

    Extractor-missed gold attributes are absent from runtime-S by construction,
    so they cannot appear in the report.  PASS instances have no residual report.
    """
    by = {"PASS": [], "INFEASIBLE": []}
    for r in rows:
        if r["method"] != "closed_loop":
            continue
        hits = set(r.get("gold_literal_hit_values", []))
        if not hits:
            continue
        rep = r.get("residual_report") or []
        rep_vals = {s["s"].split("=", 1)[1] for s in rep if "=" in s.get("s", "")}
        covered = len(hits & rep_vals)
        label = "PASS" if r["release"] else "INFEASIBLE"
        by[label].append({"id": r["id"], "n_gold_hit": len(hits),
                          "n_covered": covered, "recall": covered / len(hits)})
    out = {}
    for label, xs in by.items():
        if not xs:
            out[label] = {"n_instances_with_residue": 0}
            continue
        out[label] = {
            "n_instances_with_residue": len(xs),
            "mean_report_recall_of_gold_residue": _mean([x["recall"] for x in xs]),
            "total_gold_hit_values": sum(x["n_gold_hit"] for x in xs),
            "total_covered_by_report": sum(x["n_covered"] for x in xs),
            "instances_with_zero_report_coverage": sum(1 for x in xs if x["n_covered"] == 0),
        }
    return out


def audit_coverage(atk, jud, items, subset):
    from pipeline import gen_probe_questions
    evals = sum(r["n"] for r in atk)
    hits = sum(r["hits"] for r in atk)
    pairs = set(); texts = set()
    for iid in subset:
        for q, t, k in gen_probe_questions(items[iid]):
            if k == "value":
                pairs.add((iid, q)); texts.add(q)
    combos = {(r["attacker"], r["strategy"]) for r in atk}
    return {
        "n_instances": len({r["id"] for r in atk}),
        "n_attackers": len({r["attacker"] for r in atk}),
        "n_strategies": len({r["strategy"] for r in atk}),
        "n_attacker_strategy_combos": len(combos),
        "n_attack_calls": len(atk),
        "n_judge_calls": len(jud),
        "n_total_records": len(atk) + len(jud),
        "n_question_evaluations": evals,
        "n_unique_instance_question_pairs": len(pairs),
        "n_unique_question_texts": len(texts),
        "total_hit_evaluations": hits,
        "note": "hits are counted across repeated attack evaluations, not distinct leaked values",
    }


def online_stratified(atk, jud, local_rows, method):
    rows = [r for r in atk if r["method"] == method]
    byid = defaultdict(list)
    for r in rows:
        byid[r["id"]].append(r["L"])
    lmax = {i: max(v) for i, v in byid.items()}
    jby = {r["id"]: r["score"] for r in jud if r["method"] == method and r.get("score") is not None}

    def stratum(ids):
        ids = [i for i in ids if i in lmax]
        if not ids:
            return {"n": 0}
        hit = sum(1 for i in ids if lmax[i] > 0)
        return {"n": len(ids),
                "external_hit_instances": hit,
                "FalseRelease_external": hit / len(ids),
                "mean_external_L_max": _mean([lmax[i] for i in ids]),
                "mean_external_L_max_ci": cluster_bootstrap({i: lmax[i] for i in ids}),
                "mean_judge_U": _mean([jby.get(i) for i in ids]),
                "mean_judge_U_ci": cluster_bootstrap({i: jby[i] for i in ids if i in jby})}
    allids = sorted(lmax)
    passids = [i for i in allids if local_rows.get((i, method), {}).get("release")]
    infids = [i for i in allids if not local_rows.get((i, method), {}).get("release")]
    return {"ALL": stratum(allids), "PASS": stratum(passids), "INFEASIBLE": stratum(infids)}


def calibration(jud, local_rows):
    pairs = []
    for r in jud:
        lr = local_rows.get((r["id"], r["method"]))
        if not lr or r.get("score") is None:
            continue
        pairs.append({"id": r["id"], "method": r["method"], "local_U": lr["U_local"],
                      "judge_U": r["score"], "local_release": bool(lr["release"]),
                      "judge_release": r["score"] >= 0.5})

    def stats(rows):
        if not rows:
            return None
        lu = [r["local_U"] for r in rows]; ju = [r["judge_U"] for r in rows]
        return {"rho": spearman(lu, ju),
                "mae": _mean([abs(a - b) for a, b in zip(lu, ju)]),
                "threshold_agreement": _mean([float(r["local_release"] == r["judge_release"]) for r in rows])}

    def group(rows):
        g = defaultdict(list)
        for r in rows:
            g[r["id"]].append(r)
        return g

    out = {"overall": {}}
    for key, fn in (("rho", lambda rs: stats(rs)["rho"]),
                    ("mae", lambda rs: stats(rs)["mae"]),
                    ("threshold_agreement", lambda rs: stats(rs)["threshold_agreement"])):
        out["overall"][key] = cluster_stat(group(pairs), fn)
    out["by_method"] = {}
    for m in sorted({r["method"] for r in pairs}):
        mr = [r for r in pairs if r["method"] == m]
        conf = defaultdict(int)
        for r in mr:
            conf[f"local_{int(r['local_release'])}_judge_{int(r['judge_release'])}"] += 1
        out["by_method"][m] = {
            "n": len(mr), "point": stats(mr),
            "rho_ci": cluster_stat(group(mr), lambda rs: stats(rs)["rho"]),
            "mae_ci": cluster_stat(group(mr), lambda rs: stats(rs)["mae"]),
            "agreement_ci": cluster_stat(group(mr), lambda rs: stats(rs)["threshold_agreement"]),
            "threshold_confusion": dict(conf),
        }
    pooled = defaultdict(int)
    for r in pairs:
        pooled[f"local_{int(r['local_release'])}_judge_{int(r['judge_release'])}"] += 1
    out["pooled_threshold_confusion"] = dict(pooled)
    out["judge_pairs"] = pairs
    return out


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    offline = [json.loads(l) for l in (OUT / "offline_runtime.jsonl").open(encoding="utf-8")]
    from qi import load_dataset
    from runtime import gold_entities
    from runtime_extractor import runtime_extract
    items1 = {r["id"]: r for r in load_dataset(str(ROOT / "dataset/output/dr_sl_holdout_v1.jsonl"))}
    items2 = {r["id"]: r for r in load_dataset(str(ROOT / "dataset/output/dr_sl_holdout_v2.jsonl"))}

    result = {"seed": SEED, "n_boot": N_BOOT, "offline": {}}
    for ds in ("holdout80", "holdout80_v2"):
        rows = [r for r in offline if r["dataset"] == ds and r["sensitive_set"] == "runtime"]
        result["offline"][ds] = {
            "closed_loop": stratify_offline(rows, "closed_loop"),
            "generalization_only": stratify_offline(rows, "generalization_only"),
            "residual_report_recall_closed_loop": residual_report_recall(rows),
        }
    result["per_type_recall"] = {
        "holdout80": per_type_recall(list(items1.values()), runtime_extract, gold_entities),
        "holdout80_v2": per_type_recall(list(items2.values()), runtime_extract, gold_entities),
    }

    raw_path = OUT / "online_audit_raw.jsonl"
    if raw_path.exists():
        raw = [json.loads(l) for l in raw_path.open(encoding="utf-8")]
        atk = [r for r in raw if r["kind"] == "attack" and not r.get("error")]
        jud = [r for r in raw if r["kind"] == "judge" and not r.get("error")]
        subset = json.loads((OUT / "audit_subset.json").read_text())
        # Holdout-1 online analysis must exclude holdout-2 instances.
        atk1 = [r for r in atk if r["id"] in items1]
        jud1 = [r for r in jud if r["id"] in items1]
        local_rows = {(r["id"], r["method"]): r for r in offline
                      if r["dataset"] == "holdout80" and r["sensitive_set"] == "runtime"}
        result["audit_coverage"] = audit_coverage(atk1, jud1, items1, subset)
        result["online_stratified"] = {m: online_stratified(atk1, jud1, local_rows, m)
                                       for m in sorted({r["method"] for r in atk1})}
        result["calibration"] = calibration(jud1, local_rows)
        # holdout-2 online subset (if present)
        h2atk = [r for r in atk if r["id"] in items2]
        if h2atk:
            h2jud = [r for r in jud if r["id"] in items2]
            h2local = {(r["id"], r["method"]): r for r in offline
                       if r["dataset"] == "holdout80_v2" and r["sensitive_set"] == "runtime"}
            h2subset = sorted({r["id"] for r in h2atk})
            result["holdout2_online"] = {
                "coverage": audit_coverage(h2atk, h2jud, items2, h2subset),
                "stratified": {m: online_stratified(h2atk, h2jud, h2local, m)
                               for m in sorted({r["method"] for r in h2atk})},
            }
    (OUT / "stratified_summary.json").write_text(json.dumps(result, ensure_ascii=False, indent=2))
    # console digest
    for ds in ("holdout80", "holdout80_v2"):
        cl = result["offline"][ds]["closed_loop"]
        print(f"{ds} closed_loop: ALL n={cl['ALL']['n']} goldL={cl['ALL']['mean_gold_L']:.3f} | "
              f"PASS n={cl['PASS']['n']} FalseRelease_gold={cl['FalseRelease_gold']:.3f} "
              f"goldL={cl['PASS']['mean_gold_L']:.3f} | INFEAS n={cl['INFEASIBLE']['n']} "
              f"goldL={cl['INFEASIBLE']['mean_gold_L']:.3f}")
    if "calibration" in result:
        o = result["calibration"]["overall"]
        print("calibration overall rho", o["rho"]["estimate"], o["rho"]["ci95"],
              "mae", o["mae"]["estimate"], "agree", o["threshold_agreement"]["estimate"])
    print("wrote", OUT / "stratified_summary.json")


if __name__ == "__main__":
    main()
