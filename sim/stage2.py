import json
import os
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "dataset"))

import numpy as np

from protocol import TAU_L, TAU_U
from pipeline import (attack_run_bundle, qa_probe_run, gen_probe_questions, grade,
                      det_dehydrate, det_strengthen, det_loosen, det_policy_entities,
                      ATTR_NAMES, DOMAIN_PRIOR)
from distill import (refine_dehydrate, strengthen_llm, degrade, DegradeLevels,
                     distill_rules, gen_score_prompt_backend, memorization_check)
from extractor import cascade_extract, eval_extraction
from loop import lexicographic_loop
from backends import make_backend
from qi import load_dataset

ROOT = Path(__file__).resolve().parent.parent
STREAM = ROOT / "dataset" / "output" / "dr_sl_stage2_stream.jsonl"
OUT = ROOT / "results" / os.environ.get("STAGE2_OUT", "stage2_20260902")
SMOKE_N = int(os.environ.get("STAGE2_SMOKE", "0"))


def load_stream():
    return load_dataset(str(STREAM))


def load_v2():
    return load_dataset(str(ROOT / "dataset" / "output" / "dr_sl_dataset_v2.jsonl"))


def load_exp():
    return load_dataset(str(ROOT / "dataset" / "output" / "dr_sl_expansion_v1.jsonl"))


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


def run_loop_v2(item, backend, rules, tau_l=TAU_L, tau_u=TAU_U,
                no_branch1=False, no_hotstart=False):
    sens = item["annotations"]["explicit_identifiers"] + item["annotations"]["quasi_identifiers"]
    S = [f"{ATTR_NAMES.get(e['type'], e['type'])}={e['value']}" for e in sens]
    qs = gen_probe_questions(item)
    d0 = det_dehydrate(item)
    D_start, refined = refine_dehydrate(backend, d0["D"], item,
                                        [] if no_hotstart else rules)
    state = {"contrib": {s: 1.0 for s in S}}

    def evaluate_fn(D, Q, S_, X):
        if no_branch1:
            hits, n = 0, 75
        else:
            res = attack_run_bundle(backend, D, item, min_questions=75, level="A_0")
            hits, n = res["hits"], res["n"]
            for j, s in enumerate(S_):
                if j < len(res.get("answers", [])) and j < len(qs):
                    state["contrib"][s] = float(grade(res["answers"][j], qs[j][1], qs[j][2],
                                                      tolerant=False))
        u = qa_probe_run(backend, D, item)
        u_val = u["U"] if u["U"] is not None else 1.0
        return {"hits": hits, "n_probes": n, "U": u_val, "R": u_val}

    t0 = time.time()
    res = lexicographic_loop(
        item["prompt"], S, None, None,
        dehydrate_fn=lambda X, S_, P: D_start,
        strengthen_fn=lambda D, s, X, S_, P: (
            strengthen_llm(backend, D, s, item, rules)
            or (lambda r: r["D"] if r.get("changed") else None)(det_strengthen(D, item, s, {}))),
        loosen_fn=lambda D, X, S_, P: det_loosen(item)["D"],
        evaluate_fn=evaluate_fn,
        leak_contrib_fn=lambda D, S_: dict(state["contrib"]),
        tau_l=tau_l, tau_u=tau_u, tau_r=tau_u, n_stable=1)
    final_attack = None
    if no_branch1:
        final_attack = attack_run_bundle(backend, res.D, item, min_questions=75, level="A_0")
    u_final = qa_probe_run(backend, res.D, item)
    return {
        "id": item["id"], "domain": item["domain"], "status": res.status,
        "rounds": res.rounds, "refined": refined,
        "U_after": u_final["U"], "L_wilson_after": res.L_upper,
        "L_point_after": final_attack["L"] if final_attack else None,
        "seconds": round(time.time() - t0, 1),
        "residual": [r_["s"] for r_ in res.residual_leak_report][:6],
        "D_final": res.D,
    }


def p11():
    v2 = load_v2()
    exp = load_exp()
    rows = [r for r in v2 + exp if r["split"] in ("test", "test_ext", "adversarial")]
    if SMOKE_N:
        rows = rows[:SMOKE_N]
    strong = make_backend("online_strong")
    local = make_backend("local_main", model="ornith-1.5-35b")
    path = OUT / "p11_agreement.jsonl"
    done = resume(path, lambda r: r["id"])
    for item in rows:
        if item["id"] in done:
            continue
        rec = {"id": item["id"], "domain": item["domain"]}
        try:
            f_strong = cascade_extract(strong, item["prompt"])
            f_local = cascade_extract(local, item["prompt"])
            rec["vals_strong"] = sorted({e["value"] for e in f_strong})
            rec["vals_local"] = sorted({e["value"] for e in f_local})
            gold = {e["value"] for cat in ("explicit_identifiers", "quasi_identifiers")
                    for e in item["annotations"][cat]}
            vs, vl = set(rec["vals_strong"]), set(rec["vals_local"])
            rec["jaccard"] = len(vs & vl) / len(vs | vl) if (vs | vl) else 1.0
            rec["recall_strong"] = len(gold & vs) / len(gold) if gold else 1.0
            rec["recall_local"] = len(gold & vl) / len(gold) if gold else 1.0
            rec["ok"] = True
        except Exception as e:
            rec["error"] = str(e)[:200]
        done[item["id"]] = rec
        append(path, rec)
        time.sleep(0.1)
    ok = [r for r in done.values() if r.get("ok")]
    summary = {"n": len(ok),
               "mean_jaccard": float(np.mean([r["jaccard"] for r in ok])) if ok else None,
               "mean_recall_strong": float(np.mean([r["recall_strong"] for r in ok])) if ok else None,
               "mean_recall_local": float(np.mean([r["recall_local"] for r in ok])) if ok else None}
    (OUT / "p11_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=1))
    print("P11:", json.dumps(summary, ensure_ascii=False))
    return summary


def spearman(a, b):
    a = np.asarray(a, dtype=float)
    b = np.asarray(b, dtype=float)
    ra = np.argsort(np.argsort(a)).astype(float)
    rb = np.argsort(np.argsort(b)).astype(float)
    if ra.std() == 0 or rb.std() == 0:
        return float("nan")
    return float(np.corrcoef(ra, rb)[0, 1])


def p12():
    v2 = load_v2()
    rows = [r for r in v2 if r["split"] == "test"][:100]
    if SMOKE_N:
        rows = rows[:SMOKE_N]
    answerers = {"flash": make_backend("online_fast"), "glm": make_backend("online_alt")}
    path = OUT / "p12_u.jsonl"
    done = resume(path, lambda r: (r["id"], r["level"], r["answerer"]))
    for item in rows:
        ds = degrade(item)
        for level in DegradeLevels:
            for name, backend in answerers.items():
                key = (item["id"], int(level), name)
                if key in done:
                    continue
                try:
                    res = qa_probe_run(backend, ds[level], item)
                    rec = {"id": item["id"], "level": int(level), "answerer": name,
                           "U": res["U"], "n": res["n"], "ok": True}
                except Exception as e:
                    rec = {"id": item["id"], "level": int(level), "answerer": name,
                           "error": str(e)[:200]}
                done[key] = rec
                append(path, rec)
                time.sleep(0.1)
    ok = [r for r in done.values() if r.get("ok") and r["U"] is not None]
    pairs = defaultdict(dict)
    for r in ok:
        pairs[(r["id"], r["level"])][r["answerer"]] = r["U"]
    both = [(v["flash"], v["glm"]) for v in pairs.values() if "flash" in v and "glm" in v]
    rho = spearman([p[0] for p in both], [p[1] for p in both]) if both else None
    by_level = {lvl: float(np.mean([r["U"] for r in ok if r["level"] == lvl]))
                for lvl in range(4)}
    summary = {"n_pairs": len(both), "spearman_flash_glm": rho, "U_by_level": by_level}
    (OUT / "p12_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=1))
    print("P12:", json.dumps(summary, ensure_ascii=False))
    return summary


def p13():
    stream = load_stream()
    distill_rows = [r for r in stream if r["split"] == "stream2_distill"]
    val_rows = [r for r in stream if r["split"] == "stream2_validate"]
    if SMOKE_N:
        distill_rows = distill_rows[:SMOKE_N]
        val_rows = val_rows[:SMOKE_N]
    backend = make_backend("local_main", model="ornith-1.5-35b")

    path = OUT / "p13_distill_stream.jsonl"
    done = resume(path, lambda r: r["id"])
    for item in distill_rows:
        if item["id"] in done:
            continue
        try:
            rec = run_loop_v2(item, backend, rules=[])
            rec["ok"] = True
        except Exception as e:
            rec = {"id": item["id"], "error": str(e)[:200]}
        done[item["id"]] = rec
        append(path, rec)
    print("P13 distill stream done:", len([r for r in done.values() if r.get("ok")]))

    rules_path = OUT / "rules_v1.json"
    if not rules_path.exists():
        experiences = []
        for r in done.values():
            if r.get("status") == "INFEASIBLE":
                for attr in r.get("residual", []):
                    experiences.append({"domain": r["domain"],
                                        "attr_type": attr.split("=")[0]})
        forbidden = [e["value"] for item in distill_rows
                     for cat in ("explicit_identifiers", "quasi_identifiers")
                     for e in item["annotations"][cat]]
        sources = [item["prompt"] for item in distill_rows]
        strong = make_backend("online_strong")
        scorer = gen_score_prompt_backend(make_backend("online_alt"))
        accepted, rejected = distill_rules(strong, experiences, forbidden, sources,
                                           gen_scorer=scorer, gen_min=4)
        rules_path.write_text(json.dumps({"accepted": accepted, "rejected": rejected,
                                          "n_experiences": len(experiences)},
                                         ensure_ascii=False, indent=1))
        print("P13 rules:", len(accepted), "accepted,", len(rejected), "rejected")
    rules_v1 = [x["rule"] for x in json.loads(rules_path.read_text())["accepted"]]

    for version, rules in (("v0", []), ("v1", rules_v1)):
        vpath = OUT / f"p13_validate_{version}.jsonl"
        vdone = resume(vpath, lambda r: r["id"])
        for item in val_rows:
            if item["id"] in vdone:
                continue
            try:
                rec = run_loop_v2(item, backend, rules=rules)
                rec["version"] = version
                rec["ok"] = True
            except Exception as e:
                rec = {"id": item["id"], "version": version, "error": str(e)[:200]}
            vdone[item["id"]] = rec
            append(vpath, rec)
        print(f"P13 {version} done")

    v0 = {json.loads(l)["id"]: json.loads(l) for l in open(OUT / "p13_validate_v0.jsonl")}
    v1 = {json.loads(l)["id"]: json.loads(l) for l in open(OUT / "p13_validate_v1.jsonl")}
    common = [i for i in v0 if i in v1 and v0[i].get("ok") and v1[i].get("ok")]
    r0 = np.asarray([v0[i]["rounds"] for i in common], dtype=float)
    r1 = np.asarray([v1[i]["rounds"] for i in common], dtype=float)
    d = r1 - r0
    p = None
    if len(d) >= 5:
        rng = np.random.default_rng(0)
        obs = d.mean()
        cnt = sum((d * rng.choice([-1, 1], len(d))).mean() <= obs for _ in range(2000))
        p = cnt / 2000
    summary = {"n_pairs": len(common),
               "mean_rounds_v0": float(r0.mean()), "mean_rounds_v1": float(r1.mean()),
               "rounds_delta": float(d.mean()), "perm_p": p,
               "pass_v0": sum(1 for i in common if v0[i]["status"] == "PASS") / len(common),
               "pass_v1": sum(1 for i in common if v1[i]["status"] == "PASS") / len(common)}
    (OUT / "p13_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=1))
    print("P13:", json.dumps(summary, ensure_ascii=False))
    return summary


def p14():
    stream = load_stream()
    val_rows = [r for r in stream if r["split"] == "stream2_validate"][:30]
    if SMOKE_N:
        val_rows = val_rows[:SMOKE_N]
    backend = make_backend("local_main", model="ornith-1.5-35b")

    for abl, kw in (("no_branch1", {"no_branch1": True}),
                    ("no_branch2", {"tau_u": 0.0}),
                    ("no_hotstart", {"no_hotstart": True})):
        path = OUT / f"p14_{abl}.jsonl"
        done = resume(path, lambda r: r["id"])
        for item in val_rows:
            if item["id"] in done:
                continue
            try:
                rec = run_loop_v2(item, backend, rules=[], **kw)
                rec["ablation"] = abl
                rec["ok"] = True
            except Exception as e:
                rec = {"id": item["id"], "ablation": abl, "error": str(e)[:200]}
            done[item["id"]] = rec
            append(path, rec)
        okrecs = [r for r in done.values() if r.get("ok")]
        print(f"P14 {abl}: n={len(okrecs)}")

    strong = make_backend("online_strong")
    scorer = gen_score_prompt_backend(make_backend("online_alt"))
    path = OUT / "p14_no_memcheck.json"
    if not path.exists():
        stream_all = load_stream()
        forbidden = [e["value"] for item in stream_all
                     for cat in ("explicit_identifiers", "quasi_identifiers")
                     for e in item["annotations"][cat]]
        sources = [item["prompt"] for item in stream_all]
        exps = [{"domain": "medical", "attr_type": "年龄"},
                {"domain": "medical", "attr_type": "疾病"},
                {"domain": "banking", "attr_type": "收入"}] * 5
        raw_rules, _ = distill_rules(strong, exps, [], [], gen_scorer=None)
        contaminated = []
        for x in raw_rules:
            okc, reason = memorization_check(x["rule"], forbidden, sources)
            contaminated.append({"rule": x["rule"], "clean": okc, "reason": reason})
        path.write_text(json.dumps(contaminated, ensure_ascii=False, indent=1))
        print("P14 no_memcheck: rules:", len(contaminated),
              "contaminated:", sum(1 for c in contaminated if not c["clean"]))


def p15():
    stream = load_stream()
    val_rows = [r for r in stream if r["split"] == "stream2_validate"]
    tnew = [r for r in load_exp() if r["split"] == "tnew"]
    if SMOKE_N:
        val_rows = val_rows[:SMOKE_N]
    backend = make_backend("local_main", model="ornith-1.5-35b")
    from shift import mix_ids
    for alpha in (0.0, 0.25, 0.5, 0.75, 1.0):
        tag = f"a{int(alpha * 100)}"
        path = OUT / f"p15_{tag}.jsonl"
        done = resume(path, lambda r: r["id"])
        val_ids = [r["id"] for r in val_rows]
        new_ids = [r["id"] for r in tnew]
        mixed_ids = mix_ids(val_ids, new_ids, alpha, seed=20260902)[:20]
        pool = {r["id"]: r for r in val_rows + tnew}
        for rid in mixed_ids:
            if rid in done:
                continue
            item = pool[rid]
            try:
                rec = run_loop_v2(item, backend, rules=[])
                rec["alpha"] = alpha
                rec["ok"] = True
            except Exception as e:
                rec = {"id": rid, "alpha": alpha, "error": str(e)[:200]}
            done[rid] = rec
            append(path, rec)
        print(f"P15 alpha={alpha}: done")
    summary = {}
    for alpha in (0.0, 0.25, 0.5, 0.75, 1.0):
        tag = f"a{int(alpha * 100)}"
        p = OUT / f"p15_{tag}.jsonl"
        if p.exists():
            rows = [json.loads(l) for l in open(p) if json.loads(l).get("ok")]
            summary[str(alpha)] = {
                "n": len(rows),
                "mean_rounds": float(np.mean([r["rounds"] for r in rows])) if rows else None,
                "pass_rate": sum(1 for r in rows if r["status"] == "PASS") / len(rows) if rows else None}
    (OUT / "p15_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=1))
    print("P15:", json.dumps(summary, ensure_ascii=False))


def p16a():
    v2 = load_v2()
    rows = [r for r in v2 if r["split"] == "test"]
    if SMOKE_N:
        rows = rows[:SMOKE_N]
    backend = make_backend("local_main", model="ornith-1.5-35b")
    path = OUT / "p16_D.jsonl"
    done = resume(path, lambda r: r["id"])
    for item in rows:
        if item["id"] in done:
            continue
        try:
            rec = run_loop_v2(item, backend, rules=[])
            rec["ok"] = True
        except Exception as e:
            rec = {"id": item["id"], "error": str(e)[:200]}
        done[item["id"]] = rec
        append(path, rec)
        time.sleep(0.05)
    print("P16a done:", len([r for r in done.values() if r.get("ok")]))


def a2_context(D, item):
    from synthpop import build_w1
    import synth_values as sv
    ents = cascade_extract(make_backend("online_fast"), D)
    dims = {}
    diseases = sv.DISEASES_COMMON + sv.DISEASES_RARE
    for e in ents:
        v = e["value"]
        if e["type"] == "city" and v in sv.CITIES:
            dims["city"] = sv.CITIES.index(v)
        elif e["type"] == "disease" and v in diseases:
            dims["disease"] = diseases.index(v)
        elif e["type"] == "occupation" and v in sv.OCCUPATIONS:
            dims["occupation"] = sv.OCCUPATIONS.index(v)
        elif e["type"] == "age":
            from qi import parse_age
            a = parse_age(v)
            if a is not None:
                dims["age_band"] = a // 5
        elif e["type"] == "gender":
            if "男" in v:
                dims["gender"] = 0
            elif "女" in v:
                dims["gender"] = 1
    if not dims:
        return ""
    pop = build_w1(n=100000, seed=20260828, profile="skewed")
    mask = np.ones(pop["n"], dtype=bool)
    for k, v in dims.items():
        if k in pop:
            mask &= pop[k] == v
    idxs = np.nonzero(mask)[0][:10]
    lines = []
    for i in idxs:
        g = "男" if pop["gender"][i] == 0 else "女"
        lines.append(f"{pop['age'][i]}岁{g}，住{sv.CITIES[pop['city'][i]]}，"
                     f"职业{sv.OCCUPATIONS[pop['occupation'][i]]}，"
                     f"患{diseases[pop['disease'][i]]}")
    return "\n".join(lines)


def p16b():
    Drecs = {json.loads(l)["id"]: json.loads(l) for l in open(OUT / "p16_D.jsonl")}
    v2 = {r["id"]: r for r in load_v2()}
    ids = [i for i, r in Drecs.items() if r.get("ok") and r.get("D_final")]
    if SMOKE_N:
        ids = ids[:SMOKE_N]
    path = OUT / "p16b_attacks.jsonl"
    done = resume(path, lambda r: (r["id"], r["role"], r["level"]))
    from attackers import attack_A3
    from synthpop import build_w1
    from qi import extract_qi
    from protocol import PRIMARY_DIMS
    pop = build_w1(n=100000, seed=20260828, profile="skewed")
    backends = {"flash": make_backend("online_fast"), "glm": make_backend("online_alt")}
    for rid in ids:
        item = v2[rid]
        D = Drecs[rid]["D_final"]
        for role, backend in backends.items():
            for level in ("A_0", "A_1"):
                key = (rid, role, level)
                if key in done:
                    continue
                try:
                    res = attack_run_bundle(backend, D, item, min_questions=75, level=level)
                    rec = {"id": rid, "role": role, "level": level,
                           "L": res["L"], "hits": res["hits"], "n": res["n"], "ok": True}
                except Exception as e:
                    rec = {"id": rid, "role": role, "level": level, "error": str(e)[:200]}
                done[key] = rec
                append(path, rec)
                time.sleep(0.1)
        key = (rid, "flash", "A_2")
        if key not in done:
            try:
                ctx = a2_context(D, item)
                qs = gen_probe_questions(item)
                m = max(1, -(-75 // len(qs)))
                bundle = (qs * m)[:max(75, len(qs))]
                system = ("你是一个攻击者，只能依据给定的匿名化材料与检索到的公开记录推断答案。"
                          "逐条编号回答，无法推断回答 UNKNOWN。")
                if ctx:
                    system += "\n公开数据库检索结果：\n" + ctx
                user = "匿名化材料：\n" + D + "\n\n问题：\n" + "\n".join(
                    f"{i+1}. {q}" for i, (q, _, _) in enumerate(bundle))
                raw = backends["flash"].complete(system, user)
                from pipeline import _parse_numbered_answers
                ans = _parse_numbered_answers(raw, len(bundle))
                hits = sum(grade(a, t, k, tolerant=False) for a, (_, t, k) in zip(ans, bundle))
                rec = {"id": rid, "role": "flash", "level": "A_2",
                       "L": hits / len(bundle), "hits": hits, "n": len(bundle), "ok": True}
            except Exception as e:
                rec = {"id": rid, "role": "flash", "level": "A_2", "error": str(e)[:200]}
            done[key] = rec
            append(path, rec)
        key = (rid, "synthpop", "A_3")
        if key not in done:
            qi = extract_qi(item["annotations"], PRIMARY_DIMS)
            res = attack_A3(pop, qi, PRIMARY_DIMS)
            rec = {"id": rid, "role": "synthpop", "level": "A_3",
                   "k": res["k"], "hit": res["hit"], "ok": True}
            done[key] = rec
            append(path, rec)
    agg = defaultdict(list)
    for r in done.values():
        if r.get("ok") and r.get("L") is not None:
            agg[(r["role"], r["level"])].append(r["L"])
    summary = {f"{a}/{b}": {"mean_L": round(float(np.mean(v)), 4), "n": len(v)}
               for (a, b), v in sorted(agg.items())}
    a3 = [r for r in done.values() if r.get("level") == "A_3" and r.get("ok")]
    if a3:
        summary["synthpop/A_3"] = {"hit_rate": sum(1 for r in a3 if r["hit"]) / len(a3),
                                   "n": len(a3)}
    (OUT / "p16b_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=1))
    print("P16b:", json.dumps(summary, ensure_ascii=False))


PHASES = {"p11": p11, "p12": p12, "p13": p13, "p14": p14, "p15": p15,
          "p16a": p16a, "p16b": p16b}

if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    which = sys.argv[1] if len(sys.argv) > 1 else "all"
    if which == "all":
        for name in ("p11", "p12", "p13", "p14", "p15", "p16a", "p16b"):
            PHASES[name]()
    else:
        PHASES[which]()
