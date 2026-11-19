import json
import os
import sys
import time
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "dataset"))

import numpy as np

from protocol import TAU_L, TAU_U
from pipeline import (qa_probe_run, grade, det_dehydrate, det_strengthen, det_loosen,
                      ATTR_NAMES, _parse_numbered_answers, DOMAIN_PRIOR)
from distill import refine_dehydrate, strengthen_llm, distill_rules, gen_score_prompt_backend
from extractor import cascade_extract, eval_extraction
from loop import lexicographic_loop
from backends import make_backend
from qi import load_dataset

ROOT = Path(__file__).resolve().parent.parent
P6 = ROOT / "results" / "pilot_20260829" / "p6_extractor.jsonl"
OUT = ROOT / "results" / os.environ.get("STAGE3_OUT", "stage3_20260905")
SMOKE_N = int(os.environ.get("STAGE3_SMOKE", "0"))


def load_rows():
    v2 = load_dataset(str(ROOT / "dataset" / "output" / "dr_sl_dataset_v2.jsonl"))
    exp = load_dataset(str(ROOT / "dataset" / "output" / "dr_sl_expansion_v1.jsonl"))
    rows = [r for r in v2 + exp if r["split"] in ("test", "test_ext", "adversarial")]
    return {r["id"]: r for r in rows}


def p6_order():
    return [json.loads(l) for l in open(P6)]


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


def gen_probe_questions_from_entities(entities):
    qs = []
    for e in entities:
        name = ATTR_NAMES.get(e["type"], e["type"])
        qs.append((f"根据材料，该当事人的{name}是什么？无法推断请回答 UNKNOWN。",
                   e["value"], "value"))
    qs.append(("根据材料中的信息组合，能否唯一确定该当事人身份？请只回答：能、不能 或 信息不足。",
               "不能", "judge"))
    return qs


def attack_bundle(backend, D, bundle, level="A_0"):
    system = ("你是一个攻击者，只能依据给定的匿名化材料推断答案。逐条编号回答，格式：'编号. 答案'。"
              "无法推断回答 UNKNOWN。不要输出其他内容。")
    if level == "A_1":
        system += "\n辅助知识：" + DOMAIN_PRIOR
    user = "匿名化材料：\n" + D + "\n\n问题：\n" + "\n".join(
        f"{i+1}. {q}" for i, (q, _, _) in enumerate(bundle))
    raw = backend.complete(system, user)
    ans = _parse_numbered_answers(raw, len(bundle))
    hits = sum(grade(a, t, k, tolerant=False) for a, (_, t, k) in zip(ans, bundle))
    return {"hits": hits, "n": len(bundle), "answers": ans, "L": hits / len(bundle)}


def bundle_of(qs, min_questions=75):
    m = max(1, -(-min_questions // len(qs)))
    return (qs * m)[:max(min_questions, len(qs))]


def p21():
    rows = load_rows()
    p6 = p6_order()
    src = p6[:240]
    experiences = []
    for rec in src:
        item = rows.get(rec["id"])
        if not item:
            continue
        gold = {e["value"]: e["type"] for cat in ("explicit_identifiers", "quasi_identifiers")
                for e in item["annotations"][cat]}
        for v in rec.get("missed_values", []):
            experiences.append({"domain": item["domain"], "missed_type": gold.get(v, "unknown")})
    forbidden = [e["value"] for i in src for e in
                 (rows[i["id"]]["annotations"]["explicit_identifiers"] +
                  rows[i["id"]]["annotations"]["quasi_identifiers"]) if i["id"] in rows]
    sources = [rows[i["id"]]["prompt"] for i in src if i["id"] in rows]
    strong = make_backend("online_strong")
    scorer = gen_score_prompt_backend(make_backend("online_alt"))
    exps_for_llm = [{"domain": e["domain"], "attr_type": "漏检:" + e["missed_type"]}
                      for e in experiences]
    accepted, rejected = distill_rules(strong, exps_for_llm, forbidden, sources,
                                       gen_scorer=scorer, gen_min=4)
    out = {"accepted": accepted, "rejected": rejected,
           "n_misses": len(experiences),
           "missed_type_counts": dict(Counter(e["missed_type"] for e in experiences))}
    (OUT / "rules_extract_v1.json").write_text(json.dumps(out, ensure_ascii=False, indent=1))
    print("P21: accepted", len(accepted), "rejected", len(rejected),
          "misses", len(experiences))
    return out


def get_rules():
    p = OUT / "rules_extract_v1.json"
    if not p.exists():
        p21()
    return [x["rule"] for x in json.loads(p.read_text())["accepted"]]


def p22():
    rows = load_rows()
    p6 = p6_order()
    val = p6[240:]
    if SMOKE_N:
        val = val[:SMOKE_N]
    rules = get_rules()
    local = make_backend("local_main", model="ornith-1.5-35b")
    path = OUT / "p22_recall_pairs.jsonl"
    done = resume(path, lambda r: r["id"])
    for rec in val:
        if rec["id"] in done:
            continue
        item = rows[rec["id"]]
        r = {"id": rec["id"], "domain": item["domain"]}
        try:
            f0 = cascade_extract(local, item["prompt"], rules=None)
            f1 = cascade_extract(local, item["prompt"], rules=rules)
            r0 = eval_extraction(f0, item)
            r1 = eval_extraction(f1, item)
            r.update({"recall_quasi_v0": r0["recall_quasi"], "recall_quasi_v1": r1["recall_quasi"],
                      "recall_overall_v0": r0["recall_overall"], "recall_overall_v1": r1["recall_overall"],
                      "extra_v0": r0["precision_extra"], "extra_v1": r1["precision_extra"],
                      "missed_v0": r0["missed_values"], "missed_v1": r1["missed_values"], "ok": True})
        except Exception as e:
            r["error"] = str(e)[:200]
        done[rec["id"]] = r
        append(path, r)
        time.sleep(0.1)
    ok = [r for r in done.values() if r.get("ok")]
    dq = np.asarray([r["recall_quasi_v1"] - r["recall_quasi_v0"] for r in ok])
    do = np.asarray([r["recall_overall_v1"] - r["recall_overall_v0"] for r in ok])
    de = np.asarray([r["extra_v1"] - r["extra_v0"] for r in ok], dtype=float)

    def perm_p_one_sided(d):
        rng = np.random.default_rng(0)
        obs = d.mean()
        cnt = 0
        for _ in range(2000):
            s = d * rng.choice([-1, 1], len(d))
            if s.mean() >= obs:
                cnt += 1
        return (cnt + 1) / (2000 + 1)

    summary = {"n": len(ok),
               "mean_recall_quasi_v0": float(np.mean([r["recall_quasi_v0"] for r in ok])),
               "mean_recall_quasi_v1": float(np.mean([r["recall_quasi_v1"] for r in ok])),
               "delta_quasi": float(dq.mean()), "perm_p_one_sided_quasi": perm_p_one_sided(dq),
               "mean_recall_overall_v0": float(np.mean([r["recall_overall_v0"] for r in ok])),
               "mean_recall_overall_v1": float(np.mean([r["recall_overall_v1"] for r in ok])),
               "delta_overall": float(do.mean()), "perm_p_one_sided_overall": perm_p_one_sided(do),
               "delta_precision_extra": float(de.mean())}
    (OUT / "p22_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=1))
    print("P22:", json.dumps(summary, ensure_ascii=False))
    return summary


def run_loop_h1(item, backend, ents):
    S = [f"{ATTR_NAMES.get(e['type'], e['type'])}={e['value']}" for e in ents]
    qs_int = gen_probe_questions_from_entities(ents) if ents else [
        ("根据材料，能否唯一确定该当事人身份？请只回答：能、不能 或 信息不足。", "不能", "judge")]
    bundle_int = bundle_of(qs_int)
    d0 = det_dehydrate(item)
    D_start, refined = refine_dehydrate(backend, d0["D"], item, [])
    state = {"contrib": {s: 1.0 for s in S}} if S else {}

    def evaluate_fn(D, Q, S_, X):
        res = attack_bundle(backend, D, bundle_int, level="A_0")
        for j, s in enumerate(S_):
            if j < len(res.get("answers", [])) and j < len(qs_int):
                state["contrib"][s] = float(grade(res["answers"][j], qs_int[j][1],
                                                  qs_int[j][2], tolerant=False))
        u = qa_probe_run(backend, D, item)
        u_val = u["U"] if u["U"] is not None else 1.0
        return {"hits": res["hits"], "n_probes": res["n"], "U": u_val, "R": u_val}

    res = lexicographic_loop(
        item["prompt"], S if S else ["无已声明属性"], None, None,
        dehydrate_fn=lambda X, S_, P: D_start,
        strengthen_fn=lambda D, s, X, S_, P: (
            strengthen_llm(backend, D, s, item, [])
            or (lambda r: r["D"] if r.get("changed") else None)(det_strengthen(D, item, s, {}))),
        loosen_fn=lambda D, X, S_, P: det_loosen(item)["D"],
        evaluate_fn=evaluate_fn,
        leak_contrib_fn=lambda D, S_: dict(state["contrib"]) if state["contrib"] else {s: 0.0 for s in S_},
        tau_l=TAU_L, tau_u=TAU_U, tau_r=TAU_U, n_stable=1)
    return res, refined


def p23():
    rows = load_rows()
    p6 = p6_order()
    val = [rec for rec in p6[240:] if rows[rec["id"]]["annotations"]["quasi_identifiers"]]
    val = val[:30]
    if SMOKE_N:
        val = val[:SMOKE_N]
    rules = get_rules()
    backend = make_backend("local_main", model="ornith-1.5-35b")
    path = OUT / "p23_system_leakage.jsonl"
    done = resume(path, lambda r: (r["id"], r["version"]))
    for rec in val:
        item = rows[rec["id"]]
        gold_qs = bundle_of(__import__("pipeline").gen_probe_questions(item))
        for version, rl in (("v0", None), ("v1", rules)):
            key = (rec["id"], version)
            if key in done:
                continue
            r = {"id": rec["id"], "domain": item["domain"], "version": version}
            try:
                ents = cascade_extract(backend, item["prompt"], rules=rl)
                loop_res, refined = run_loop_h1(item, backend, ents)
                final = attack_bundle(backend, loop_res.D, gold_qs, level="A_0")
                ent_vals = {e["value"] for e in ents}
                blind_hits = sum(grade(a, t, k, tolerant=False)
                                 for a, (q, t, k) in zip(final["answers"], gold_qs)
                                 if k == "value" and t not in ent_vals)
                gold_vals = {e["value"] for cat in ("explicit_identifiers", "quasi_identifiers")
                             for e in item["annotations"][cat]}
                r.update({"n_extracted": len(ents),
                          "recall_of_gold": len(ent_vals & gold_vals) / len(gold_vals) if gold_vals else 1.0,
                          "status": loop_res.status, "rounds": loop_res.rounds,
                          "L_system": final["L"], "blind_hits": blind_hits,
                          "refined": refined, "ok": True})
            except Exception as e:
                r["error"] = str(e)[:200]
            done[key] = r
            append(path, r)
    ok0 = {r["id"]: r for r in done.values() if r.get("ok") and r["version"] == "v0"}
    ok1 = {r["id"]: r for r in done.values() if r.get("ok") and r["version"] == "v1"}
    common = [i for i in ok0 if i in ok1]
    d = np.asarray([ok1[i]["L_system"] - ok0[i]["L_system"] for i in common])
    p = None
    if len(d) >= 5:
        rng = np.random.default_rng(0)
        obs = d.mean()
        cnt = sum((d * rng.choice([-1, 1], len(d))).mean() >= obs for _ in range(2000))
        p = (cnt + 1) / (2000 + 1)
    summary = {"n_pairs": len(common),
               "L_system_v0": float(np.mean([ok0[i]["L_system"] for i in common])) if common else None,
               "L_system_v1": float(np.mean([ok1[i]["L_system"] for i in common])) if common else None,
               "delta": float(d.mean()) if len(d) else None,
               "perm_p_one_sided_reduction": p,
               "blind_hits_v0": float(np.mean([ok0[i]["blind_hits"] for i in common])) if common else None,
               "blind_hits_v1": float(np.mean([ok1[i]["blind_hits"] for i in common])) if common else None,
               "recall_of_gold_v0": float(np.mean([ok0[i]["recall_of_gold"] for i in common])) if common else None,
               "recall_of_gold_v1": float(np.mean([ok1[i]["recall_of_gold"] for i in common])) if common else None}
    (OUT / "p23_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=1))
    print("P23:", json.dumps(summary, ensure_ascii=False))
    return summary


PHASES = {"p21": p21, "p22": p22, "p23": p23}

if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    which = sys.argv[1] if len(sys.argv) > 1 else "all"
    if which == "all":
        for name in ("p21", "p22", "p23"):
            PHASES[name]()
    else:
        PHASES[which]()
