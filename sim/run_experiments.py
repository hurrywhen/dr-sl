import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "dataset"))

from protocol import TAU_L, TAU_U, TAU_R, K_STAR
from pipeline import (attack_run, attack_run_bundle, qa_probe_run, dehydrate_run, strengthen_run,
                      loosen_run, extract_explicit, gen_probe_questions, ATTR_NAMES)
from backends import make_backend
from qi import load_dataset
from loop import lexicographic_loop
from shift import coverage, domain_auc, mmd_test
from synthpop import build_w1, run_k_experiment
from protocol import PRIMARY_DIMS

ROOT = Path(__file__).resolve().parent.parent
DATA_V2 = ROOT / "dataset" / "output" / "dr_sl_dataset_v2.jsonl"
DATA_EXP = ROOT / "dataset" / "output" / "dr_sl_expansion_v1.jsonl"
OUT = ROOT / "results" / __import__("os").environ.get("PILOT_OUT", "pilot_20260829")


def load_all():
    v2 = load_dataset(str(DATA_V2))
    exp = load_dataset(str(DATA_EXP))
    return v2, exp


def jdump(path, rows):
    with open(path, "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")


def p0_regex_recall():
    v2, exp = load_all()
    rows = [r for r in v2 + exp if r["split"] in ("test", "test_ext", "adversarial")]
    results, found_total, gold_total = [], 0, 0
    for item in rows:
        gold = item["annotations"]["explicit_identifiers"]
        found = extract_explicit(item["prompt"])
        gold_vals = {e["value"] for e in gold}
        found_vals = {e["value"] for e in found}
        tp = len(gold_vals & found_vals)
        found_total += tp
        gold_total += len(gold_vals)
        results.append({"id": item["id"], "domain": item["domain"],
                        "gold": len(gold_vals), "tp": tp,
                        "missed": sorted(gold_vals - found_vals)[:3]})
    regexable_types = {"phone", "email", "id_card", "bank_card", "passport", "plate",
                       "medical_record_no", "case_no", "deposit_no", "order_no",
                       "ticket_no", "insurance_id", "fund_account"}
    reg_gold = reg_tp = 0
    by_type = {}
    for item in rows:
        found_vals = {e["value"] for e in extract_explicit(item["prompt"])}
        for e in item["annotations"]["explicit_identifiers"]:
            t = by_type.setdefault(e["type"], [0, 0])
            if e["type"] in regexable_types:
                reg_gold += 1
                t[0] += 1
                if e["value"] in found_vals:
                    reg_tp += 1
                    t[1] += 1
    summary = {
        "n_instances": len(rows),
        "explicit_recall_overall": found_total / gold_total if gold_total else None,
        "explicit_recall_regexable": reg_tp / reg_gold if reg_gold else None,
        "per_type_regex": {k: {"gold": v[0], "tp": v[1]} for k, v in sorted(by_type.items()) if v[0]},
        "note": "name/address/card_tail 等需 LLM 层；此处仅正则层",
    }
    jdump(OUT / "p0_regex_recall.jsonl", results)
    (OUT / "p0_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=1))
    print("P0:", json.dumps(summary, ensure_ascii=False))
    return summary


def _cov_json(cov):
    return {"exact": cov["exact"], "subset": cov["subset"],
            "uncovered": {"、".join(k): v for k, v in cov["uncovered"].items()}}


def p1_shift_metrics():
    v2, exp = load_all()
    library = [r for r in v2 if r["split"] in ("calibration", "train")]
    test = [r for r in v2 if r["split"] == "test"]
    test_ext = [r for r in exp if r["split"] == "test_ext"]
    tnew = [r for r in exp if r["split"] == "tnew"]
    cov_test = coverage(test, library)
    cov_ext = coverage(test + test_ext, library)
    cov_new = coverage(tnew, library)
    auc_tfidf, ci = domain_auc([r["prompt"] for r in test], [r["prompt"] for r in tnew])
    summary = {"coverage_test": _cov_json(cov_test),
               "coverage_test_plus_ext": _cov_json(cov_ext),
               "coverage_tnew": _cov_json(cov_new),
               "auc_tfidf": auc_tfidf, "auc_ci": list(ci)}
    try:
        emb = make_backend("local_embed")
        es = emb.embed([r["prompt"][:2000] for r in test])
        en = emb.embed([r["prompt"][:2000] for r in tnew])
        import numpy as np
        mmd2, p = mmd_test(np.asarray(es), np.asarray(en), n_perm=500, seed=20260829)
        summary.update({"mmd2_embed": mmd2, "mmd_p": p})
    except Exception as e:
        summary["embed_error"] = str(e)[:200]
    (OUT / "p1_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=1))
    print("P1:", json.dumps(summary, ensure_ascii=False, indent=1)[:1200])
    return summary


def _attack_phase(tag, roles_levels, splits=("test",)):
    v2, exp = load_all()
    rows = [r for r in v2 + exp if r["split"] in splits]
    done_path = OUT / f"{tag}.jsonl"
    done = {}
    if done_path.exists():
        for line in done_path.read_text().splitlines():
            rec = json.loads(line)
            if rec.get("hits") is None and "error" in rec:
                continue
            done[(rec["id"], rec["role"], rec["level"])] = rec
    out = list(done.values())
    for item in rows:
        for role, levels in roles_levels.items():
            backend = make_backend(role)
            for level in levels:
                key = (item["id"], role, level)
                if key in done:
                    continue
                try:
                    res = attack_run(backend, item["prompt"], item, level=level)
                except Exception as e:
                    res = {"error": str(e)[:200], "hits": None, "n": None}
                rec = {"id": item["id"], "domain": item["domain"], "role": role,
                       "level": level, **(res or {})}
                rec.pop("answers", None)
                out.append(rec)
                done[key] = rec
                with open(done_path, "a", encoding="utf-8") as f:
                    f.write(json.dumps(rec, ensure_ascii=False) + "\n")
                time.sleep(0.2)
    return out


def p2_direct_forward_leakage():
    out = _attack_phase("p2_leakage", {"online_fast": ["A_0", "A_1"], "online_alt": ["A_0"]})
    agg = {}
    for rec in out:
        if rec.get("hits") is None:
            continue
        k = (rec["role"], rec["level"])
        agg.setdefault(k, []).append(rec["L"])
    summary = {f"{r}/{l}": {"mean_L": sum(v) / len(v), "n": len(v)}
               for (r, l), v in sorted(agg.items())}
    (OUT / "p2_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=1))
    print("P2:", json.dumps(summary, ensure_ascii=False))
    return summary


def p3_qa_probe_direct():
    v2, _ = load_all()
    rows = [r for r in v2 if r["split"] == "test"]
    done_path = OUT / "p3_qa_direct.jsonl"
    done = {}
    if done_path.exists():
        for line in done_path.read_text().splitlines():
            rec = json.loads(line)
            done[rec["id"]] = rec
    backend = make_backend("online_fast")
    for item in rows:
        if item["id"] in done:
            continue
        try:
            res = qa_probe_run(backend, item["prompt"], item)
            rec = {"id": item["id"], "domain": item["domain"], "U": res["U"], "n": res["n"]}
        except Exception as e:
            rec = {"id": item["id"], "domain": item["domain"], "error": str(e)[:200]}
        done[item["id"]] = rec
        with open(done_path, "a", encoding="utf-8") as f:
            f.write(json.dumps({k: v for k, v in rec.items()}, ensure_ascii=False) + "\n")
        time.sleep(0.2)
    us = [r["U"] for r in done.values() if r.get("U") is not None]
    summary = {"mean_U_direct": sum(us) / len(us) if us else None, "n": len(us)}
    (OUT / "p3_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=1))
    print("P3:", json.dumps(summary, ensure_ascii=False))
    return summary


def _task_retention(D, item):
    vals = [e["value"] for e in item["annotations"]["quasi_identifiers"] if e.get("task_relevant")]
    if not vals:
        return 1.0
    return sum(1 for v in vals if v in D) / len(vals)


def p4_local_loop_pilot():
    import os
    from pipeline import det_dehydrate, det_strengthen, det_loosen
    pilot_tau_l = float(os.environ.get("PILOT_TAU_L", "0.20"))
    v2, _ = load_all()
    selected = []
    for dom in ("medical", "banking", "travel", "legal"):
        cands = [r for r in v2 if r["split"] == "test" and r["domain"] == dom
                 and r["annotations"]["quasi_identifiers"]]
        selected.extend(cands[:2])
    backend = make_backend("local_main")
    results = []
    for item in selected:
        sens = item["annotations"]["explicit_identifiers"] + item["annotations"]["quasi_identifiers"]
        S = [f"{ATTR_NAMES.get(e['type'], e['type'])}={e['value']}" for e in sens]
        from pipeline import gen_probe_questions, grade as _grade
        d0 = det_dehydrate(item)
        qs = gen_probe_questions(item)
        state = {"contrib": {s: 0.0 for s in S}}

        def evaluate_fn(D, Q, S_, X):
            res = attack_run(backend, D, item, level="A_0")
            u = qa_probe_run(backend, D, item)
            u_val = u["U"] if u["U"] is not None else 1.0
            for i, s in enumerate(S_):
                if i < len(res.get("answers", [])) and i < len(qs):
                    state["contrib"][s] = float(_grade(res["answers"][i], qs[i][1], qs[i][2], tolerant=False))
            return {"hits": res["hits"], "n_probes": res["n"], "U": u_val, "R": u_val}

        def leak_contrib_fn(D, S_):
            return dict(state["contrib"])

        before = attack_run(backend, item["prompt"], item, level="A_0")
        u_before = qa_probe_run(backend, item["prompt"], item)
        t0 = time.time()
        res = lexicographic_loop(
            item["prompt"], S, None, None,
            dehydrate_fn=lambda X, S_, P: d0["D"],
            strengthen_fn=lambda D, s, X, S_, P: (
                lambda r: r["D"] if r.get("changed") else None)(det_strengthen(D, item, s, {})),
            loosen_fn=lambda D, X, S_, P: det_loosen(item)["D"],
            evaluate_fn=evaluate_fn, leak_contrib_fn=leak_contrib_fn,
            tau_l=pilot_tau_l, tau_u=TAU_U, tau_r=TAU_U, n_stable=1)
        rec = {"id": item["id"], "domain": item["domain"], "status": res.status,
               "rounds": res.rounds, "L_before": before["L"], "L_after": res.L_upper,
               "L_point_after": None, "U_before": u_before["U"], "U_after": res.U,
               "R_after": res.R, "pilot_tau_l": pilot_tau_l,
               "seconds": round(time.time() - t0, 1),
               "n_attrs": len(S),
               "residual": [r_["s"] for r_ in res.residual_leak_report][:5]}
        results.append(rec)
        jdump(OUT / "p4_loop_pilot.jsonl", results)
        print("P4 done:", rec["id"], rec["status"], "rounds=", rec["rounds"])
    (OUT / "p4_summary.json").write_text(json.dumps(results, ensure_ascii=False, indent=1))
    return results


def p5_calibration_delta():
    v2, _ = load_all()
    cands = [r for r in v2 if r["split"] == "calibration" and r["annotations"]["quasi_identifiers"]][:12]
    rows = []
    local_b = make_backend("local_main")
    strong_b = make_backend("online_strong")
    for item in cands:
        try:
            r_local = attack_run(local_b, item["prompt"], item, level="A_0")
            r_strong = attack_run(strong_b, item["prompt"], item, level="A_0")
        except Exception as e:
            rows.append({"id": item["id"], "error": str(e)[:200]})
            continue
        rows.append({"id": item["id"], "domain": item["domain"],
                     "L_local": r_local["L"], "L_strong": r_strong["L"],
                     "delta": r_strong["L"] - r_local["L"]})
        jdump(OUT / "p5_calibration.jsonl", rows)
        time.sleep(0.2)
    ds = [r["delta"] for r in rows if "delta" in r]
    summary = {"n": len(ds), "mean_delta": sum(ds) / len(ds) if ds else None,
               "mean_L_local": sum(r["L_local"] for r in rows if "delta" in r) / len(ds) if ds else None,
               "mean_L_strong": sum(r["L_strong"] for r in rows if "delta" in r) / len(ds) if ds else None}
    (OUT / "p5_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=1))
    print("P5:", json.dumps(summary, ensure_ascii=False))
    return summary


def p6_extractor():
    from extractor import cascade_extract, eval_extraction
    v2, exp = load_all()
    rows = [r for r in v2 + exp if r["split"] in ("test", "test_ext", "adversarial")]
    backend = make_backend("local_main", model="ornith-1.5-35b")
    done_path = OUT / "p6_extractor.jsonl"
    done = {}
    if done_path.exists():
        for line in done_path.read_text().splitlines():
            rec = json.loads(line)
            done[rec["id"]] = rec
    for item in rows:
        if item["id"] in done:
            continue
        try:
            found = cascade_extract(backend, item["prompt"])
            rep = eval_extraction(found, item)
            rec = {"id": item["id"], "domain": item["domain"], "split": item["split"],
                   "n_found": len(found), **rep}
        except Exception as e:
            rec = {"id": item["id"], "error": str(e)[:200]}
        done[item["id"]] = rec
        with open(done_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
        time.sleep(0.1)
    ok = [r for r in done.values() if "recall_overall" in r]
    import statistics as st
    summary = {
        "n": len(ok),
        "mean_recall_overall": st.mean(r["recall_overall"] for r in ok),
        "mean_recall_explicit": st.mean(r["recall_explicit"] for r in ok),
        "mean_recall_quasi": st.mean(r["recall_quasi"] for r in ok),
        "mean_precision_extra": st.mean(r["precision_extra"] for r in ok),
    }
    (OUT / "p6_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=1))
    print("P6:", json.dumps(summary, ensure_ascii=False))
    return summary


def p5_full():
    v2, _ = load_all()
    rows = [r for r in v2 if r["split"] == "calibration"]
    local_b = make_backend("local_main", model="ornith-1.5-35b")
    strong_b = make_backend("online_strong")
    done_path = OUT / "p5_full.jsonl"
    done = {}
    if done_path.exists():
        for line in done_path.read_text().splitlines():
            rec = json.loads(line)
            done[rec["id"]] = rec
    for item in rows:
        if item["id"] in done:
            continue
        rec = {"id": item["id"], "domain": item["domain"]}
        try:
            r_local = attack_run_bundle(local_b, item["prompt"], item, level="A_0")
            rec["L_local"] = r_local["L"]
        except Exception as e:
            rec["error_local"] = str(e)[:200]
        try:
            r_strong = attack_run_bundle(strong_b, item["prompt"], item, level="A_0")
            rec["L_strong"] = r_strong["L"]
        except Exception as e:
            rec["error_strong"] = str(e)[:200]
        if "L_local" in rec and "L_strong" in rec:
            rec["delta"] = rec["L_strong"] - rec["L_local"]
        done[item["id"]] = rec
        with open(done_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
        time.sleep(0.1)
    ds = [r["delta"] for r in done.values() if "delta" in r]
    summary = {"n": len(ds),
               "mean_delta": sum(ds) / len(ds) if ds else None,
               "mean_L_local": sum(r["L_local"] for r in done.values() if "delta" in r) / len(ds) if ds else None,
               "mean_L_strong": sum(r["L_strong"] for r in done.values() if "delta" in r) / len(ds) if ds else None}
    (OUT / "p5_full_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=1))
    print("P5_full:", json.dumps(summary, ensure_ascii=False))
    return summary


def p2_local():
    v2, exp = load_all()
    rows = [r for r in v2 + exp if r["split"] in ("test", "test_ext")]
    backend = make_backend("local_main", model="ornith-1.5-35b")
    done_path = OUT / "p2_local.jsonl"
    done = {}
    if done_path.exists():
        for line in done_path.read_text().splitlines():
            rec = json.loads(line)
            done[(rec["id"], rec["level"])] = rec
    for item in rows:
        for level in ("A_0", "A_1"):
            if (item["id"], level) in done:
                continue
            try:
                res = attack_run_bundle(backend, item["prompt"], item, level=level)
                rec = {"id": item["id"], "domain": item["domain"], "split": item["split"],
                       "role": "local_ornith", "level": level, **res}
                rec.pop("answers", None)
            except Exception as e:
                rec = {"id": item["id"], "level": level, "error": str(e)[:200]}
            done[(item["id"], level)] = rec
            with open(done_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(rec, ensure_ascii=False) + "\n")
            time.sleep(0.1)
    agg = {}
    for rec in done.values():
        if rec.get("L") is None:
            continue
        agg.setdefault((rec["role"], rec["level"]), []).append(rec["L"])
    summary = {f"{a}/{b}": {"mean_L": round(sum(v) / len(v), 4), "n": len(v)}
               for (a, b), v in sorted(agg.items())}
    (OUT / "p2_local_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=1))
    print("P2_local:", json.dumps(summary, ensure_ascii=False))
    return summary


def p7_train_loop():
    from pipeline import det_dehydrate, det_strengthen, det_loosen, gen_probe_questions, grade as _grade
    v2, _ = load_all()
    rows = [r for r in v2 if r["split"] == "train"]
    backend = make_backend("local_main", model="ornith-1.5-35b")
    done_path = OUT / "p7_train_loop.jsonl"
    exp_path = OUT / "p7_experience.jsonl"
    done = set()
    if done_path.exists():
        for line in done_path.read_text().splitlines():
            done.add(json.loads(line)["id"])
    for idx, item in enumerate(rows):
        if item["id"] in done:
            continue
        sens = item["annotations"]["explicit_identifiers"] + item["annotations"]["quasi_identifiers"]
        S = [f"{ATTR_NAMES.get(e['type'], e['type'])}={e['value']}" for e in sens]
        qs = gen_probe_questions(item)
        d0 = det_dehydrate(item)
        state = {"contrib": {s: 0.0 for s in S}}

        def evaluate_fn(D, Q, S_, X):
            res = attack_run_bundle(backend, D, item, min_questions=75, level="A_0")
            u = qa_probe_run(backend, D, item)
            u_val = u["U"] if u["U"] is not None else 1.0
            for j, s in enumerate(S_):
                if j < len(res.get("answers", [])) and j < len(qs):
                    state["contrib"][s] = float(_grade(res["answers"][j], qs[j][1], qs[j][2], tolerant=False))
            return {"hits": res["hits"], "n_probes": res["n"], "U": u_val, "R": u_val}

        def leak_contrib_fn(D, S_):
            return dict(state["contrib"]) if any(state["contrib"].values()) else {s: 1.0 for s in S_}

        before = attack_run_bundle(backend, item["prompt"], item, min_questions=75, level="A_0")
        u_before = qa_probe_run(backend, item["prompt"], item)
        t0 = time.time()
        try:
            res = lexicographic_loop(
                item["prompt"], S, None, None,
                dehydrate_fn=lambda X, S_, P: d0["D"],
                strengthen_fn=lambda D, s, X, S_, P: (
                    lambda r: r["D"] if r.get("changed") else None)(det_strengthen(D, item, s, {})),
                loosen_fn=lambda D, X, S_, P: det_loosen(item)["D"],
                evaluate_fn=evaluate_fn, leak_contrib_fn=leak_contrib_fn,
                tau_l=TAU_L, tau_u=TAU_U, tau_r=TAU_U, n_stable=1)
            after = attack_run_bundle(backend, res.D, item, min_questions=75, level="A_0")
            rec = {"id": item["id"], "domain": item["domain"], "idx": idx,
                   "status": res.status, "rounds": res.rounds,
                   "L_before": before["L"], "L_after": after["L"],
                   "L_wilson_after": res.L_upper,
                   "U_before": u_before["U"], "U_after": res.U,
                   "n_attrs": len(S), "seconds": round(time.time() - t0, 1)}
            if res.status == "INFEASIBLE":
                with open(exp_path, "a", encoding="utf-8") as f:
                    for r_ in res.residual_leak_report:
                        f.write(json.dumps({"id": item["id"], "domain": item["domain"],
                                            "cause": "gate_infeasible", "attr": r_["s"]},
                                           ensure_ascii=False) + "\n")
        except Exception as e:
            rec = {"id": item["id"], "domain": item["domain"], "idx": idx,
                   "error": str(e)[:200], "seconds": round(time.time() - t0, 1)}
        with open(done_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
        print(f"P7 {idx+1}/{len(rows)}:", rec.get("id"), rec.get("status"),
              "rounds=", rec.get("rounds"), "L:", rec.get("L_before"), "->", rec.get("L_after"))


def p2_strong():
    out = _attack_phase("p2_strong", {"online_strong": ["A_0"]})
    agg = []
    for rec in out:
        if rec.get("L") is not None:
            agg.append(rec["L"])
    summary = {"online_strong/A_0": {"mean_L": round(sum(agg) / len(agg), 4), "n": len(agg)}} if agg else {}
    (OUT / "p2_strong_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=1))
    print("P2_strong:", json.dumps(summary, ensure_ascii=False))
    return summary


PHASES = {"p0": p0_regex_recall, "p1": p1_shift_metrics, "p2": p2_direct_forward_leakage,
          "p3": p3_qa_probe_direct, "p4": p4_local_loop_pilot, "p5": p5_calibration_delta,
          "p6": p6_extractor, "p5_full": p5_full, "p2_local": p2_local, "p7": p7_train_loop,
          "p2_strong": p2_strong}

if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    which = sys.argv[1] if len(sys.argv) > 1 else "all"
    if which == "all":
        for name in ("p0", "p1", "p2", "p3", "p5", "p4"):
            PHASES[name]()
    else:
        PHASES[which]()
