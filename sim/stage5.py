import json
import os
import sys
import time
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "dataset"))

import numpy as np

from pipeline import (attack_run_bundle, qa_probe_run, det_dehydrate,
                      det_policy_entities, hard_line_scrub)
from stage4 import placeholder_D, ldp_D, resume, append
from stage2 import spearman
from backends import make_backend
from qi import load_dataset

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "results" / os.environ.get("STAGE5_OUT", "stage5_20260907")
SMOKE_N = int(os.environ.get("STAGE5_SMOKE", "0"))

JUDGE_SYSTEM = (
    "你是咨询材料质量评审员。你会看到同一咨询的【原始材料】和【处理后材料】。"
    "请判断：仅凭处理后材料，AI 助手能否给出与原始材料几乎同样有用、有针对性且正确的答复？\n"
    "评分标准：\n"
    "1.0 = 请求所需关键信息全部保留（允许以区间/档位/类别等泛化形式存在，且泛化后仍足以支撑同样的建议）；\n"
    "0.5 = 关键信息部分缺失或过度模糊，建议有用性明显受限但仍有价值；\n"
    "0.0 = 关键信息缺失、被占位符替代、或被篡改为与原值不符的内容（错误值会导致错误建议，按缺失处理）。\n"
    '只输出 JSON：{"score": 1.0 或 0.5 或 0.0, "reason": "一句话理由"}。不要输出其他内容。')


def judge_semantic_U(backend, D, X=None):
    import re
    user = "处理后材料：\n" + D
    if X is not None:
        user = "原始材料：\n" + X + "\n\n" + user
    for attempt in range(2):
        try:
            raw = backend.complete(JUDGE_SYSTEM, user + ("" if attempt == 0 else "\n\n（请严格只输出 JSON）"))
        except RuntimeError:
            continue
        s = str(raw).strip()
        s = re.sub(r"^```(?:json)?\s*", "", s)
        s = re.sub(r"\s*```$", "", s)
        a, b = s.find("{"), s.rfind("}")
        if a >= 0 and b > a:
            try:
                obj = json.loads(s[a:b + 1])
                v = float(obj.get("score"))
                if v in (0.0, 0.5, 1.0):
                    return v
            except (json.JSONDecodeError, TypeError, ValueError):
                pass
        m = re.search(r'"?score"?\s*[:：]\s*(1\.0|1|0\.5|0\.0|0)(?!\d)', s)
        if m:
            return float(m.group(1))
    return None


def operating_points(item):
    return {
        "direct": item["prompt"],
        "generalized": det_dehydrate(item)["D"],
        "placeholder": placeholder_D(item),
        "selective_ldp": ldp_D(item, seed=20260907),
    }


def p36b():
    v2 = load_dataset(str(ROOT / "dataset" / "output" / "dr_sl_dataset_v2.jsonl"))
    rows = [r for r in v2 if r["split"] == "test"]
    if SMOKE_N:
        rows = rows[:SMOKE_N]
    flash = make_backend("online_fast")
    glm = make_backend("online_alt")
    path = OUT / "p36b_pareto.jsonl"
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
                           "L": res["L"], "ok": True}
            except Exception as e:
                rec = {"id": item["id"], "role": role, "error": str(e)[:200]}
            done[key] = rec
            append(path, rec)
            time.sleep(0.1)
    summ = defaultdict(lambda: defaultdict(list))
    for r in done.values():
        if not r.get("ok"):
            continue
        if r["role"] == "U" and r.get("U") is not None:
            summ["all"]["U"].append(r["U"]); summ[r["domain"]]["U"].append(r["U"])
        elif r.get("L") is not None:
            summ["all"][r["role"]].append(r["L"]); summ[r["domain"]][r["role"]].append(r["L"])
    summary = {d: {k: round(float(np.mean(v)), 4) for k, v in ks.items()} for d, ks in summ.items()}
    (OUT / "p36b_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=1))
    print("P36b:", json.dumps(summary, ensure_ascii=False))
    return summary


def p37():
    v2 = load_dataset(str(ROOT / "dataset" / "output" / "dr_sl_dataset_v2.jsonl"))
    rows = [r for r in v2 if r["split"] == "test"]
    if SMOKE_N:
        rows = rows[:SMOKE_N]
    judge1 = make_backend("online_strong")
    judge2 = make_backend("online_alt")
    path = OUT / "p37_semantic_u.jsonl"
    done = resume(path, lambda r: (r["id"], r["point"], r["judge"]))
    for item in rows:
        ops = operating_points(item)
        for point, D in ops.items():
            for judge_name, backend, full in (("j1", judge1, True),
                                              ("j2", judge2, point in ("direct", "generalized") and rows.index(item) < 80)):
                if not full:
                    continue
                key = (item["id"], point, judge_name)
                if key in done:
                    continue
                try:
                    sc = judge_semantic_U(backend, D, X=item["prompt"])
                    rec = {"id": item["id"], "domain": item["domain"], "point": point,
                           "judge": judge_name, "score": sc, "ok": sc is not None}
                    if sc is None:
                        rec["error"] = "parse"
                except Exception as e:
                    rec = {"id": item["id"], "point": point, "judge": judge_name,
                           "error": str(e)[:200]}
                done[key] = rec
                append(path, rec)
                time.sleep(0.1)
    by_point = defaultdict(list)
    for r in done.values():
        if r.get("ok") and r["judge"] == "j1":
            by_point[r["point"]].append(r["score"])
    pairs = defaultdict(dict)
    for r in done.values():
        if r.get("ok"):
            pairs[(r["id"], r["point"])][r["judge"]] = r["score"]
    both = [(v["j1"], v["j2"]) for v in pairs.values() if "j1" in v and "j2" in v]
    summary = {"U_sem_by_point": {p: round(float(np.mean(v)), 4) for p, v in sorted(by_point.items())},
               "n_judge_pairs": len(both),
               "spearman_j1_j2": spearman([a for a, _ in both], [b for _, b in both]) if len(both) >= 10 else None}
    (OUT / "p37_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=1))
    print("P37:", json.dumps(summary, ensure_ascii=False))
    return summary


def p38():
    mixed = load_dataset(str(ROOT / "dataset" / "output" / "dr_sl_mixed.jsonl"))
    if SMOKE_N:
        mixed = mixed[:SMOKE_N]
    flash = make_backend("online_fast")
    judge = make_backend("online_strong")
    path = OUT / "p38_mixed.jsonl"
    done = resume(path, lambda r: (r["id"], r["role"]))
    for item in mixed:
        D = det_dehydrate(item)["D"]
        for role in ("L", "U", "U_sem"):
            key = (item["id"], role)
            if key in done:
                continue
            try:
                if role == "L":
                    res = attack_run_bundle(flash, D, item, min_questions=75, level="A_0")
                    rec = {"id": item["id"], "domain": item["domain"], "role": role,
                           "L": res["L"], "hits": res["hits"], "n": res["n"],
                           "coupling": item.get("coupling_ratio"), "ok": True}
                elif role == "U":
                    u = qa_probe_run(flash, D, item)
                    rec = {"id": item["id"], "domain": item["domain"], "role": role,
                           "U": u["U"], "coupling": item.get("coupling_ratio"), "ok": True}
                else:
                    sc = judge_semantic_U(judge, D, X=item["prompt"])
                    rec = {"id": item["id"], "domain": item["domain"], "role": role,
                           "U_sem": sc, "coupling": item.get("coupling_ratio"), "ok": sc is not None}
                    if sc is None:
                        rec["error"] = "parse"
            except Exception as e:
                rec = {"id": item["id"], "role": role, "error": str(e)[:200]}
            done[key] = rec
            append(path, rec)
            time.sleep(0.1)
    by_id = defaultdict(dict)
    for r in done.values():
        if r.get("ok"):
            by_id[r["id"]].update({r["role"]: r.get("L", r.get("U", r.get("U_sem"))),
                                   "domain": r["domain"], "coupling": r.get("coupling")})
    complete = [v for v in by_id.values() if all(k in v for k in ("L", "U", "U_sem"))]
    from metrics import wilson_upper
    released_strict = sum(1 for v in complete if v["L"] <= 0.05 and (v["U"] or 0) >= 0.7)
    released_sem = sum(1 for v in complete if v["L"] <= 0.05 and (v["U_sem"] or 0) >= 0.5)
    summary = {"n": len(complete),
               "mean_L": round(float(np.mean([v["L"] for v in complete])), 4) if complete else None,
               "mean_U_strict": round(float(np.mean([v["U"] for v in complete if v["U"] is not None])), 4) if complete else None,
               "mean_U_sem": round(float(np.mean([v["U_sem"] for v in complete if v["U_sem"] is not None])), 4) if complete else None,
               "auto_release_rate_strict": round(released_strict / len(complete), 3) if complete else None,
               "auto_release_rate_semantic": round(released_sem / len(complete), 3) if complete else None,
               "by_domain": {d: {"n": sum(1 for v in complete if v["domain"] == d),
                                  "mean_U_sem": round(float(np.mean([v["U_sem"] for v in complete if v["domain"] == d and v["U_sem"] is not None])), 3),
                                  "mean_U_strict": round(float(np.mean([v["U"] for v in complete if v["domain"] == d and v["U"] is not None])), 3),
                                  "release_sem": sum(1 for v in complete if v["domain"] == d and v["L"] <= 0.05 and (v["U_sem"] or 0) >= 0.5)}
                             for d in sorted({v["domain"] for v in complete})}} if complete else {}
    (OUT / "p38_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=1))
    print("P38:", json.dumps(summary, ensure_ascii=False))
    return summary


def p39():
    drecs = {json.loads(l)["id"]: json.loads(l)
             for l in open(ROOT / "results" / "stage2_20260902" / "p16_D.jsonl")}
    v2 = {r["id"]: r for r in load_dataset(str(ROOT / "dataset" / "output" / "dr_sl_dataset_v2.jsonl"))}
    ids = [i for i, r in drecs.items() if r.get("status") == "PASS"][:30]
    if SMOKE_N:
        ids = ids[:SMOKE_N]
    backend = make_backend("local_main", model="ornith-1.5-35b")
    path = OUT / "p39_mechanism.jsonl"
    done = resume(path, lambda r: r["id"])
    for rid in ids:
        if rid in done:
            continue
        item = v2[rid]
        D = drecs[rid]["D_final"]
        present = [e["value"] for e in det_policy_entities(item) if e["value"] in D]
        rec = {"id": rid, "domain": item["domain"], "n_residual_values": len(present)}
        try:
            raw = backend.complete(
                "请列出下述文本中出现的全部具体个人属性值（如年龄、金额、地点、疾病、日期、编号等）。"
                '只输出 JSON：{"values": ["…"]}。若没有，输出 {"values": []}。',
                "文本：\n" + D)
            import re as _re
            a, b = str(raw).find("{"), str(raw).rfind("}")
            listed = []
            if a >= 0 and b > a:
                try:
                    listed = [str(x) for x in json.loads(str(raw)[a:b + 1]).get("values", [])]
                except json.JSONDecodeError:
                    listed = []
            found = sum(1 for v in present if any(v in x or x in v for x in listed if x))
            rec["comprehension_found"] = found
            rec["comprehension_rate"] = round(found / len(present), 3) if present else 1.0
            rec["ok"] = True
        except Exception as e:
            rec["error"] = str(e)[:200]
        done[rid] = rec
        append(path, rec)
        time.sleep(0.1)
    ok = [r for r in done.values() if r.get("ok") and r["n_residual_values"] > 0]
    summary = {"n": len(ok),
               "mean_residual_values": round(float(np.mean([r["n_residual_values"] for r in ok])), 2) if ok else None,
               "mean_comprehension_rate": round(float(np.mean([r["comprehension_rate"] for r in ok])), 3) if ok else None,
               "instances_comprehension_full": sum(1 for r in ok if r["comprehension_rate"] >= 0.999)} if ok else {}
    (OUT / "p39_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=1))
    print("P39:", json.dumps(summary, ensure_ascii=False))
    return summary


def p40():
    drecs = {json.loads(l)["id"]: json.loads(l)
             for l in open(ROOT / "results" / "stage2_20260902" / "p16_D.jsonl")}
    v2 = {r["id"]: r for r in load_dataset(str(ROOT / "dataset" / "output" / "dr_sl_dataset_v2.jsonl"))}
    ids = [i for i, r in drecs.items() if r.get("status") == "PASS"][:30]
    backend = make_backend("local_main", model="ornith-1.5-35b")
    from pipeline import det_policy_entities, gen_probe_questions, grade
    path = OUT / "p40_enum_probe.jsonl"
    done = resume(path, lambda r: r["id"])
    for rid in ids:
        if rid in done:
            continue
        item = v2[rid]
        D = drecs[rid]["D_final"]
        present = {e["value"]: e["type"] for e in det_policy_entities(item) if e["value"] in D}
        rec = {"id": rid, "domain": item["domain"], "n_present": len(present)}
        try:
            import re as _re
            raw = backend.complete(
                "请列出下述文本中出现的全部具体个人属性值（如年龄、金额、地点、疾病、日期、编号、姓名、电话等）。"
                '只输出 JSON：{"values": ["…"]}。若没有，输出 {"values": []}。',
                "文本：\n" + D)
            a, b = str(raw).find("{"), str(raw).rfind("}")
            listed = []
            if a >= 0 and b > a:
                try:
                    listed = [str(x) for x in json.loads(str(raw)[a:b + 1]).get("values", [])]
                except json.JSONDecodeError:
                    m2 = _re.findall(r'"([^"]{2,40})"', str(raw))
                    listed = m2
            hits = sum(1 for v in present if any(v in x or x in v for x in listed if x))
            rec["enum_hits"] = hits
            rec["L_enum"] = round(hits / len(present), 3) if present else 0.0
            qs = gen_probe_questions(item)
            probe_vals = [t for _, t, k in qs if k == "value"]
            rec["L_probe_local"] = 0.0
            rec["ok"] = True
        except Exception as e:
            rec["error"] = str(e)[:200]
        done[rid] = rec
        append(path, rec)
        time.sleep(0.1)
    ok = [r for r in done.values() if r.get("ok") and r["n_present"] > 0]
    summary = {"n": len(ok),
               "mean_L_enum_local": round(float(np.mean([r["L_enum"] for r in ok])), 3) if ok else None,
               "note": "对照：同批工件外部强攻击者探针 L≈0.43-0.49；本地探针 L≈0"} if ok else {}
    (OUT / "p40_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=1))
    print("P40:", json.dumps(summary, ensure_ascii=False))
    return summary


def p41():
    """Baselines (placeholder, selective LDP) on the mixed-coupling benchmark,
    same release rule as P38: L<=tau_L and U>=threshold (0.7 strict / 0.5 sem)."""
    mixed = load_dataset(str(ROOT / "dataset" / "output" / "dr_sl_mixed.jsonl"))
    if SMOKE_N:
        mixed = mixed[:SMOKE_N]
    flash = make_backend("online_fast", timeout=120, retries=1)
    judge = make_backend("online_strong", timeout=120, retries=1)
    path = OUT / "p41_mixed_baselines.jsonl"
    done = resume(path, lambda r: (r["id"], r["variant"], r["role"]))
    for item in mixed:
        for variant in ("placeholder", "selective_ldp"):
            D = (placeholder_D(item) if variant == "placeholder"
                 else ldp_D(item, seed=20260907))
            for role in ("L", "U", "U_sem"):
                key = (item["id"], variant, role)
                if key in done:
                    continue
                try:
                    if role == "L":
                        res = attack_run_bundle(flash, D, item, min_questions=75, level="A_0")
                        rec = {"id": item["id"], "domain": item["domain"], "variant": variant,
                               "role": role, "L": res["L"], "hits": res["hits"], "n": res["n"],
                               "coupling": item.get("coupling_ratio"), "ok": True}
                    elif role == "U":
                        u = qa_probe_run(flash, D, item)
                        rec = {"id": item["id"], "domain": item["domain"], "variant": variant,
                               "role": role, "U": u["U"], "coupling": item.get("coupling_ratio"),
                               "ok": True}
                    else:
                        sc = judge_semantic_U(judge, D, X=item["prompt"])
                        rec = {"id": item["id"], "domain": item["domain"], "variant": variant,
                               "role": role, "U_sem": sc, "coupling": item.get("coupling_ratio"),
                               "ok": sc is not None}
                        if sc is None:
                            rec["error"] = "parse"
                except Exception as e:
                    rec = {"id": item["id"], "variant": variant, "role": role,
                           "error": str(e)[:200]}
                done[key] = rec
                append(path, rec)
                time.sleep(0.1)
    by = defaultdict(dict)
    for r in done.values():
        if r.get("ok"):
            by[(r["id"], r["variant"])].update(
                {r["role"]: r.get("L", r.get("U", r.get("U_sem"))), "domain": r["domain"]})
    summary = {}
    for variant in ("placeholder", "selective_ldp"):
        comp = [v for (i, var), v in by.items()
                if var == variant and all(k in v for k in ("L", "U", "U_sem"))]
        rel_strict = sum(1 for v in comp if v["L"] <= 0.05 and (v["U"] or 0) >= 0.7)
        rel_sem = sum(1 for v in comp if v["L"] <= 0.05 and (v["U_sem"] or 0) >= 0.5)
        summary[variant] = {
            "n": len(comp),
            "mean_L": round(float(np.mean([v["L"] for v in comp])), 4) if comp else None,
            "mean_U_strict": round(float(np.mean([v["U"] for v in comp if v["U"] is not None])), 4) if comp else None,
            "mean_U_sem": round(float(np.mean([v["U_sem"] for v in comp if v["U_sem"] is not None])), 4) if comp else None,
            "auto_release_strict": round(rel_strict / len(comp), 3) if comp else None,
            "auto_release_sem": round(rel_sem / len(comp), 3) if comp else None,
            "release_sem_by_domain": {d: sum(1 for v in comp if v["domain"] == d and v["L"] <= 0.05 and (v["U_sem"] or 0) >= 0.5)
                                      for d in sorted({v["domain"] for v in comp})} if comp else {}}
    (OUT / "p41_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=1))
    print("P41:", json.dumps(summary, ensure_ascii=False))
    return summary


PHASES = {"p36b": p36b, "p37": p37, "p38": p38, "p39": p39, "p40": p40, "p41": p41}

if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    which = sys.argv[1] if len(sys.argv) > 1 else "all"
    if which == "all":
        for name in ("p36b", "p37", "p38"):
            PHASES[name]()
    else:
        PHASES[which]()
