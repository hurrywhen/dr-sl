import json
import os
import random
import sys
import time
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "dataset"))

import numpy as np

from pipeline import (attack_run_bundle, qa_probe_run, gen_probe_questions,
                      det_policy_entities, hard_line_scrub, GENERIC_TOKENS, ATTR_NAMES)
from backends import make_backend
from qi import load_dataset
import synth_values as sv

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "results" / os.environ.get("STAGE4_OUT", "stage4_20260907")
SMOKE_N = int(os.environ.get("STAGE4_SMOKE", "0"))


def resume(path, key_fn):
    done = {}
    if path.exists():
        for line in path.read_text().splitlines():
            rec = json.loads(line)
            if "error" in rec and rec.get("ok") is not True:
                continue
            done[key_fn(rec)] = rec
    return done


def append(path, rec):
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")


def placeholder_D(item):
    text = item["prompt"]
    for e in det_policy_entities(item):
        text = text.replace(e["value"], f"[{e['type'].upper()}]")
    return text


REPLACERS = {
    "name": lambda r: sv.person_name(r),
    "phone": lambda r: "190" + "".join(str(r.randint(0, 9)) for _ in range(8)),
    "city": lambda r: r.choice(sv.CITIES),
    "hospital": lambda r: r.choice(sv.HOSPITALS),
    "disease": lambda r: r.choice(sv.DISEASES_COMMON + sv.DISEASES_RARE),
    "drug": lambda r: r.choice(sv.DRUGS),
    "occupation": lambda r: r.choice(sv.OCCUPATIONS),
    "employer": lambda r: r.choice(sv.COMPANIES),
    "school": lambda r: r.choice(sv.SCHOOLS),
    "bank": lambda r: r.choice(sv.BANKS),
    "age": lambda r: f"{r.randint(20, 80)}岁",
    "gender": lambda r: r.choice(["男", "女"]),
    "income": lambda r: f"年收入约{r.choice([6, 12, 20, 40])}万元",
    "id_card": lambda r: "11010119900307" + "".join(str(r.randint(0, 9)) for _ in range(4)),
    "bank_card": lambda r: "6222 " + " ".join("".join(str(r.randint(0, 9)) for _ in range(4)) for _ in range(3)),
    "email": lambda r: f"user{r.randint(100,999)}@example.com",
}


def ldp_D(item, seed):
    r = random.Random(seed)
    text = item["prompt"]
    for e in det_policy_entities(item):
        fn = REPLACERS.get(e["type"])
        rep = fn(r) if fn else f"[{e['type'].upper()}{r.randint(10, 99)}]"
        text = text.replace(e["value"], rep, 1)
    return text


def p31():
    v2 = load_dataset(str(ROOT / "dataset" / "output" / "dr_sl_dataset_v2.jsonl"))
    rows = [r for r in v2 if r["split"] == "test"]
    if SMOKE_N:
        rows = rows[:SMOKE_N]
    flash = make_backend("online_fast")
    glm = make_backend("online_alt")
    path = OUT / "p31_baselines.jsonl"
    done = resume(path, lambda r: (r["id"], r["method"], r["role"]))
    for item in rows:
        for method, D in (("placeholder", placeholder_D(item)),
                          ("selective_ldp", ldp_D(item, seed=20260907))):
            for role, backend in (("flash", flash), ("glm", glm)):
                key = (item["id"], method, role)
                if key in done:
                    continue
                try:
                    res = attack_run_bundle(backend, D, item, min_questions=75, level="A_0")
                    rec = {"id": item["id"], "domain": item["domain"], "method": method,
                           "role": role, "L": res["L"], "hits": res["hits"], "n": res["n"], "ok": True}
                except Exception as e:
                    rec = {"id": item["id"], "method": method, "role": role, "error": str(e)[:200]}
                done[key] = rec
                append(path, rec)
                time.sleep(0.1)
            key = (item["id"], method, "U")
            if key not in done:
                try:
                    u = qa_probe_run(flash, D, item)
                    rec = {"id": item["id"], "domain": item["domain"], "method": method,
                           "role": "U", "U": u["U"], "ok": True}
                except Exception as e:
                    rec = {"id": item["id"], "method": method, "role": "U", "error": str(e)[:200]}
                done[key] = rec
                append(path, rec)
                time.sleep(0.1)
    agg = defaultdict(list)
    for r in done.values():
        if not r.get("ok"):
            continue
        if r["role"] == "U":
            if r.get("U") is not None:
                agg[(r["method"], "U")].append(r["U"])
        elif r.get("L") is not None:
            agg[(r["method"], r["role"])].append(r["L"])
    summary = {f"{m}/{k}": {"mean": round(float(np.mean(v)), 4), "n": len(v)}
               for (m, k), v in sorted(agg.items())}
    (OUT / "p31_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=1))
    print("P31:", json.dumps(summary, ensure_ascii=False))
    return summary


def p32():
    v2 = load_dataset(str(ROOT / "dataset" / "output" / "dr_sl_dataset_v2.jsonl"))
    rows = [r for r in v2 if r["split"] == "test"]
    sel = []
    for dom in ("medical", "banking", "travel", "legal"):
        sel.extend([r for r in rows if r["domain"] == dom][:15])
    if SMOKE_N:
        sel = sel[:SMOKE_N]
    backend = make_backend("local_main", model="qwen3.8-27b-mlx")
    path = OUT / "p32_size_gradient.jsonl"
    done = resume(path, lambda r: r["id"])
    for item in sel:
        if item["id"] in done:
            continue
        try:
            res = attack_run_bundle(backend, item["prompt"], item, min_questions=75, level="A_0")
            rec = {"id": item["id"], "domain": item["domain"], "role": "qwen27b",
                   "L": res["L"], "hits": res["hits"], "n": res["n"], "ok": True}
        except Exception as e:
            rec = {"id": item["id"], "role": "qwen27b", "error": str(e)[:200]}
        done[item["id"]] = rec
        append(path, rec)
        time.sleep(0.1)
    ok = [r for r in done.values() if r.get("ok")]
    summary = {"n": len(ok), "mean_L_qwen27b": round(float(np.mean([r["L"] for r in ok])), 4)} if ok else {}
    (OUT / "p32_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=1))
    print("P32:", json.dumps(summary, ensure_ascii=False))
    return summary


def p33():
    v2 = load_dataset(str(ROOT / "dataset" / "output" / "dr_sl_dataset_v2.jsonl"))
    exp = load_dataset(str(ROOT / "dataset" / "output" / "dr_sl_expansion_v1.jsonl"))
    rows = [r for r in v2 + exp if r["split"] in ("test", "test_ext", "adversarial")]
    if SMOKE_N:
        rows = rows[:SMOKE_N]
    glm = make_backend("online_alt")
    from extractor import cascade_extract, eval_extraction
    p11 = {json.loads(l)["id"]: json.loads(l)
           for l in open(ROOT / "results" / "stage2_20260902" / "p11_agreement.jsonl")}
    path = OUT / "p33_crossfamily.jsonl"
    done = resume(path, lambda r: r["id"])
    for item in rows:
        if item["id"] in done:
            continue
        rec = {"id": item["id"], "domain": item["domain"]}
        try:
            f_glm = cascade_extract(glm, item["prompt"])
            vg = {e["value"] for e in f_glm}
            rep = eval_extraction(f_glm, item)
            p = p11.get(item["id"], {})
            vs = set(p.get("vals_strong", []))
            vl = set(p.get("vals_local", []))
            rec.update({"vals_glm": sorted(vg), "recall_glm": rep["recall_overall"],
                        "jaccard_glm_strong": len(vg & vs) / len(vg | vs) if (vg | vs) else 1.0,
                        "jaccard_glm_local": len(vg & vl) / len(vg | vl) if (vg | vl) else 1.0,
                        "ok": True})
        except Exception as e:
            rec["error"] = str(e)[:200]
        done[item["id"]] = rec
        append(path, rec)
        time.sleep(0.1)
    ok = [r for r in done.values() if r.get("ok")]
    summary = {"n": len(ok),
               "mean_recall_glm": round(float(np.mean([r["recall_glm"] for r in ok])), 4),
               "jaccard_glm_vs_qwenmax": round(float(np.mean([r["jaccard_glm_strong"] for r in ok])), 4),
               "jaccard_glm_vs_ornith": round(float(np.mean([r["jaccard_glm_local"] for r in ok])), 4)} if ok else {}
    (OUT / "p33_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=1))
    print("P33:", json.dumps(summary, ensure_ascii=False))
    return summary


def p34():
    drecs = {json.loads(l)["id"]: json.loads(l)
             for l in open(ROOT / "results" / "stage2_20260902" / "p16_D.jsonl")}
    v2 = {r["id"]: r for r in load_dataset(str(ROOT / "dataset" / "output" / "dr_sl_dataset_v2.jsonl"))}
    ids = [i for i, r in drecs.items() if r.get("ok") and r.get("D_final")]
    if SMOKE_N:
        ids = ids[:SMOKE_N]
    flash = make_backend("online_fast")
    glm = make_backend("online_alt")
    path = OUT / "p34_hardline.jsonl"
    done = resume(path, lambda r: (r["id"], r["role"]))
    scrub_stats = []
    for rid in ids:
        item = v2[rid]
        scrub = hard_line_scrub(drecs[rid]["D_final"], item)
        scrub_stats.append({"id": rid, "status": drecs[rid]["status"], "n_removed": len(scrub["removed"])})
        for role, backend in (("flash", flash), ("glm", glm)):
            key = (rid, role)
            if key in done:
                continue
            try:
                res = attack_run_bundle(backend, scrub["D"], item, min_questions=75, level="A_0")
                rec = {"id": rid, "role": role, "L": res["L"], "hits": res["hits"],
                       "n": res["n"], "status": drecs[rid]["status"],
                       "n_scrubbed": len(scrub["removed"]), "ok": True}
            except Exception as e:
                rec = {"id": rid, "role": role, "error": str(e)[:200]}
            done[key] = rec
            append(path, rec)
            time.sleep(0.1)
    agg = defaultdict(list)
    for r in done.values():
        if r.get("ok") and r.get("L") is not None:
            agg[(r["role"], "all")].append(r["L"])
            agg[(r["role"], r.get("status", "?"))].append(r["L"])
    summary = {f"{a}/{b}": {"mean_L": round(float(np.mean(v)), 4), "n": len(v)}
               for (a, b), v in sorted(agg.items())}
    summary["scrub"] = {"instances_with_residual_literals": sum(1 for s in scrub_stats if s["n_removed"] > 0),
                        "total": len(scrub_stats),
                        "mean_removed": round(float(np.mean([s["n_removed"] for s in scrub_stats])), 2)} if scrub_stats else {}
    (OUT / "p34_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=1))
    print("P34:", json.dumps(summary, ensure_ascii=False))
    return summary


def p35():
    drecs = {json.loads(l)["id"]: json.loads(l)
             for l in open(ROOT / "results" / "stage2_20260902" / "p16_D.jsonl")}
    v2 = {r["id"]: r for r in load_dataset(str(ROOT / "dataset" / "output" / "dr_sl_dataset_v2.jsonl"))}
    ids = [i for i, r in drecs.items() if r.get("ok") and r.get("D_final")]
    if SMOKE_N:
        ids = ids[:SMOKE_N]
    flash = make_backend("online_fast")
    path = OUT / "p35_u_postscrub.jsonl"
    done = resume(path, lambda r: r["id"])
    for rid in ids:
        if rid in done:
            continue
        item = v2[rid]
        scrub = hard_line_scrub(drecs[rid]["D_final"], item)
        try:
            u = qa_probe_run(flash, scrub["D"], item)
            rec = {"id": rid, "status": drecs[rid]["status"], "U": u["U"], "ok": True}
        except Exception as e:
            rec = {"id": rid, "status": drecs[rid]["status"], "error": str(e)[:200]}
        done[rid] = rec
        append(path, rec)
        time.sleep(0.1)
    ok = [r for r in done.values() if r.get("ok") and r.get("U") is not None]
    summary = {"n": len(ok), "mean_U_postscrub": round(float(np.mean([r["U"] for r in ok])), 4),
               "by_status": {st: round(float(np.mean([r["U"] for r in ok if r["status"] == st])), 4)
                             for st in ("PASS", "INFEASIBLE")}}
    (OUT / "p35_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=1))
    print("P35:", json.dumps(summary, ensure_ascii=False))
    return summary


def p36():
    v2 = load_dataset(str(ROOT / "dataset" / "output" / "dr_sl_dataset_v2.jsonl"))
    rows = [r for r in v2 if r["split"] == "test"]
    if SMOKE_N:
        rows = rows[:SMOKE_N]
    from pipeline import det_dehydrate
    flash = make_backend("online_fast")
    glm = make_backend("online_alt")
    path = OUT / "p36_pareto.jsonl"
    done = resume(path, lambda r: (r["id"], r["role"]))
    for item in rows:
        D = det_dehydrate(item)["D"]
        for role, backend in (("flash_L", flash), ("glm_L", glm), ("U", flash)):
            key = (item["id"], role)
            if key in done:
                continue
            try:
                if role == "U":
                    u = qa_probe_run(backend, D, item)
                    rec = {"id": item["id"], "domain": item["domain"], "role": role,
                           "U": u["U"], "ok": True}
                else:
                    res = attack_run_bundle(backend, D, item, min_questions=75, level="A_0")
                    rec = {"id": item["id"], "domain": item["domain"], "role": role,
                           "L": res["L"], "hits": res["hits"], "n": res["n"], "ok": True}
            except Exception as e:
                rec = {"id": item["id"], "role": role, "error": str(e)[:200]}
            done[key] = rec
            append(path, rec)
            time.sleep(0.1)
    okL_f = [r["L"] for r in done.values() if r.get("ok") and r["role"] == "flash_L" and r.get("L") is not None]
    okL_g = [r["L"] for r in done.values() if r.get("ok") and r["role"] == "glm_L" and r.get("L") is not None]
    okU = [r["U"] for r in done.values() if r.get("ok") and r["role"] == "U" and r.get("U") is not None]
    summary = {"n": len(rows, ),
               "L_flash": round(float(np.mean(okL_f)), 4) if okL_f else None,
               "L_glm": round(float(np.mean(okL_g)), 4) if okL_g else None,
               "U_flash": round(float(np.mean(okU)), 4) if okU else None}
    (OUT / "p36_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=1))
    print("P36:", json.dumps(summary, ensure_ascii=False))
    return summary




PHASES = {"p31": p31, "p32": p32, "p33": p33, "p34": p34, "p35": p35, "p36": p36}

if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    which = sys.argv[1] if len(sys.argv) > 1 else "all"
    if which == "all":
        for name in ("p34", "p31", "p33", "p32"):
            PHASES[name]()
    else:
        PHASES[which]()
