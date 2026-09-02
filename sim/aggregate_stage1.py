import json
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import numpy as np

OUT = Path(__file__).resolve().parent.parent / "results" / "pilot_20260829"
KDIR = Path(__file__).resolve().parent.parent / "results" / "kanonymity"


def load_jsonl(p):
    return [json.loads(l) for l in open(p)] if Path(p).exists() else []


def mean_ci(vals):
    vals = np.asarray(vals, dtype=float)
    if vals.size == 0:
        return None, (None, None)
    rng = np.random.default_rng(20260831)
    boots = vals[rng.integers(0, vals.size, (1000, vals.size))].mean(axis=1)
    return float(vals.mean()), (float(np.quantile(boots, 0.025)), float(np.quantile(boots, 0.975)))


def sign_test_paired(before, after, n_perm=2000):
    d = np.asarray(after) - np.asarray(before)
    d = d[np.abs(d) > 1e-12]
    if len(d) < 5:
        return None
    obs = d.mean()
    rng = np.random.default_rng(0)
    cnt = 0
    for _ in range(n_perm):
        signs = rng.choice([-1, 1], size=len(d))
        if (d * signs).mean() <= obs:
            cnt += 1
    return cnt / n_perm


def main():
    report = {}

    p6 = [r for r in load_jsonl(OUT / "p6_extractor.jsonl") if "recall_overall" in r]
    if p6:
        rep = {}
        for key in ("recall_overall", "recall_explicit", "recall_quasi", "precision_extra"):
            m, ci = mean_ci([r[key] for r in p6])
            rep[key] = {"mean": round(m, 4), "ci95": [round(x, 4) for x in ci]}
        by_dom = defaultdict(list)
        for r in p6:
            by_dom[r["domain"]].append(r["recall_overall"])
        rep["by_domain"] = {d: round(float(np.mean(v)), 4) for d, v in sorted(by_dom.items())}
        report["extractor"] = rep

    p5 = [r for r in load_jsonl(OUT / "p5_full.jsonl") if "delta" in r]
    if p5:
        m, ci = mean_ci([r["delta"] for r in p5])
        by_dom = defaultdict(list)
        for r in p5:
            by_dom[r["domain"]].append(r["delta"])
        report["calibration_delta"] = {
            "n": len(p5), "mean": round(m, 4), "ci95": [round(x, 4) for x in ci],
            "mean_L_local": round(float(np.mean([r["L_local"] for r in p5])), 4),
            "mean_L_strong": round(float(np.mean([r["L_strong"] for r in p5])), 4),
            "by_domain": {d: round(float(np.mean(v)), 4) for d, v in sorted(by_dom.items())},
        }

    att = defaultdict(list)
    for role_file in ("p2_leakage.jsonl", "p2_local.jsonl", "p2_strong.jsonl"):
        for r in load_jsonl(OUT / role_file):
            if r.get("L") is None:
                continue
            role = r.get("role", "local_ornith")
            att[(role, r["level"])].append(r["L"])
            att[(role, r["level"], r["domain"])].append(r["L"])
    curve = {}
    for k, v in att.items():
        if len(k) == 2:
            m, ci = mean_ci(v)
            curve[f"{k[0]}/{k[1]}"] = {"mean_L": round(m, 4), "ci95": [round(x, 4) for x in ci], "n": len(v)}
        else:
            curve[f"{k[0]}/{k[1]}/{k[2]}"] = {"mean_L": round(float(np.mean(v)), 4), "n": len(v)}
    ksum = json.load(open(KDIR / "summary.json")) if (KDIR / "summary.json").exists() else {}
    if ksum and "skewed@100000" in ksum.get("runs", {}):
        run = ksum["runs"]["skewed@100000"]
        curve["synthpop_A3/skewed@100000"] = {
            "hit_rate_with_qi": run["p_k_lt_kstar"],
            "hit_rate_all_instances": round(run["p_k_lt_kstar"] * run["n_instances_with_qi"] / run["n_instances_total"], 4),
            "note": "conservative convention k_tilde<=5"}
    report["attacker_curve"] = curve

    p7 = [r for r in load_jsonl(OUT / "p7_train_loop.jsonl") if "status" in r]
    if p7:
        ok = [r for r in p7 if r["status"] in ("PASS", "INFEASIBLE")]
        rep = {
            "n": len(ok),
            "pass_rate": round(sum(1 for r in ok if r["status"] == "PASS") / len(ok), 4) if ok else None,
            "mean_rounds": round(float(np.mean([r["rounds"] for r in ok])), 2),
        }
        lb = [r["L_before"] for r in ok]
        la = [r["L_after"] for r in ok]
        rep["L_before_mean"] = round(float(np.mean(lb)), 4)
        rep["L_after_mean"] = round(float(np.mean(la)), 4)
        pval = sign_test_paired(lb, la)
        rep["L_reduction_perm_p"] = pval
        ub = [r["U_before"] for r in ok if r["U_before"] is not None]
        ua = [r["U_after"] for r in ok if r["U_after"] is not None]
        rep["U_before_mean"] = round(float(np.mean(ub)), 4)
        rep["U_after_mean"] = round(float(np.mean(ua)), 4)
        rep["U_drop_gt_0.1"] = sum(1 for r in ok if (r["U_before"] or 1) - (r["U_after"] or 0) > 0.1)
        by_dom = defaultdict(lambda: [0, 0])
        for r in ok:
            by_dom[r["domain"]][1] += 1
            if r["status"] == "PASS":
                by_dom[r["domain"]][0] += 1
        rep["pass_by_domain"] = {d: f"{a}/{b}" for d, (a, b) in sorted(by_dom.items())}
        idxs = np.argsort([r["idx"] for r in ok])
        rounds_sorted = np.asarray([r["rounds"] for r in ok])[idxs]
        if len(rounds_sorted) >= 20:
            first = rounds_sorted[:len(rounds_sorted) // 2].mean()
            second = rounds_sorted[len(rounds_sorted) // 2:].mean()
            rep["rounds_first_half"] = round(float(first), 2)
            rep["rounds_second_half"] = round(float(second), 2)
        report["train_loop"] = rep

    (OUT / "stage1_summary.json").write_text(json.dumps(report, ensure_ascii=False, indent=1))
    print(json.dumps(report, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
