"""Runtime-S end-to-end deterministic track.

The functions in this module are the revised local release path.  They receive
only the original prompt, domain, a declared task-relevance profile, and
extractor output.  Gold annotations are never read here.  External scoring is
implemented separately in ``external_gold_audit`` and must be called only after
the artifact and local decision are frozen.
"""
import hashlib
import random
import re
import sys
import unicodedata
import zlib
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "dataset"))

import synth_values as sv
from pipeline import (ATTR_NAMES, GENERALIZE_RULES, GENERIC_TOKENS, _norm,
                      det_dehydrate, det_loosen, det_strengthen,
                      deterministic_dehydrate, hard_line_scrub)
from loop import lexicographic_loop
from protocol import DELTA, N_STABLE, TAU_L
from runtime_extractor import runtime_extract

TAU_U_LOCAL = 0.50

MIXED_TASK_TYPES = {
    "medical": {"age", "disease", "drug", "allergy"},
    "banking": {"amount", "charge"},
    "travel": {"date", "visit_date", "city"},
    "legal": {"case_type", "amount", "date"},
}

_NUMERIC_BAND_TYPES = {"age", "amount", "charge", "income", "work_years",
                       "marriage_years", "duration", "children_count",
                       "date", "visit_date"}


def runtime_view(source, entities, task_profile="mixed"):
    """Construct a policy view without touching source annotations."""
    prompt = source["prompt"]
    domain = source.get("domain", "")
    ents = []
    for e in entities:
        typ = e["type"]
        if task_profile == "all_quasi":
            rel = e.get("category") == "quasi"
        else:
            rel = typ in MIXED_TASK_TYPES.get(domain, set())
        ents.append({**e, "task_relevant": bool(rel)})
    return {
        "prompt": prompt,
        "domain": domain,
        "annotations": {
            "explicit_identifiers": [e for e in ents if e.get("category") == "explicit"],
            "quasi_identifiers": [e for e in ents if e.get("category") == "quasi"],
            "combos": [],
        },
        "runtime_entities": ents,
    }


def _nfkc_norm(s):
    s = unicodedata.normalize("NFKC", str(s)).casefold()
    return re.sub(r"[\s\-—–_·.,，。；;:：!！?？\"'“”‘’()（）\[\]【】]", "", s)


def local_literal_attack(view, D):
    """Three deterministic local audit strategies; no independence claim."""
    entities = view["runtime_entities"]
    n = len(entities)
    strategies = {}
    hit_sets = {}
    for name, transform in (("verbatim", lambda x: x),
                            ("punct_norm", _norm),
                            ("nfkc_norm", _nfkc_norm)):
        text = transform(D)
        hits = []
        for e in entities:
            v = transform(e["value"])
            if v and v in text:
                hits.append(e["value"])
        hit_sets[name] = set(hits)
        strategies[name] = {"hits": len(hits), "n": n,
                            "L": len(hits) / n if n else 1.0}
    union = set().union(*hit_sets.values()) if hit_sets else set()
    max_hits = max((s["hits"] for s in strategies.values()), default=0)
    return {"n_probes": n, "hits": max_hits,
            "L": max_hits / n if n else 1.0,
            "strategies": strategies, "hit_values": sorted(union),
            "gate_type": "heuristic_point_rate",
            "statistical_unit": "instance_cluster"}


def _context_retention(view, D):
    spans = sorted(e["span"] for e in view["runtime_entities"])
    text = view["prompt"]
    segments, cur = [], 0
    for s, t in spans:
        if s > cur:
            segments.append(text[cur:s])
        cur = max(cur, t)
    if cur < len(text):
        segments.append(text[cur:])
    total = sum(len(x) for x in segments)
    if total == 0:
        return 1.0
    kept = sum(len(x) for x in segments if x and x in D)
    return kept / total


def local_utility(view, D):
    """Fully local reference-based utility surrogate (not a semantic judge)."""
    task = [e for e in view["runtime_entities"] if e.get("task_relevant")]
    detail = []
    if not task:
        u = _context_retention(view, D)
        return {"U": u, "n": 0, "detail": [], "basis": "non_sensitive_context"}
    for e in task:
        typ, val = e["type"], e["value"]
        if val and val in D:
            score = 1.0
        else:
            rule = GENERALIZE_RULES.get(typ)
            rep = rule(val) if rule else GENERIC_TOKENS.get(typ, "〔敏感信息〕")
            if rep and rep in D and typ in _NUMERIC_BAND_TYPES:
                score = 0.5
            else:
                score = 0.0
        detail.append({"type": typ, "value": val, "score": score})
    return {"U": sum(d["score"] for d in detail) / len(detail),
            "n": len(detail), "detail": detail, "basis": "runtime_task_attributes"}


def stable_decision(view, D, n_stable=N_STABLE, delta=DELTA,
                    tau_l=TAU_L, tau_u=TAU_U_LOCAL):
    window = []
    for _ in range(n_stable):
        attack = local_literal_attack(view, D)
        util = local_utility(view, D)
        window.append({"L": attack["L"], "U": util["U"],
                       "hits": attack["hits"], "n": attack["n_probes"]})
    passed = all(w["n"] > 0 and w["L"] <= tau_l and w["U"] >= tau_u for w in window)
    fluct = max(w["L"] for w in window) - min(w["L"] for w in window)
    fluct_u = max(w["U"] for w in window) - min(w["U"] for w in window)
    stable = passed and fluct <= delta and fluct_u <= delta
    return {"status": "PASS" if stable else "INFEASIBLE",
            "release": stable, "L": window[-1]["L"], "U": window[-1]["U"],
            "hits": window[-1]["hits"], "n_probes": window[-1]["n"],
            "stable": stable, "n_stable": n_stable, "delta": delta,
            "window": window}


def _random_replacer(typ, rng):
    if typ == "name":
        return sv.person_name(rng)
    if typ == "phone":
        return "190" + "".join(str(rng.randint(0, 9)) for _ in range(8))
    if typ == "city":
        return rng.choice(sv.CITIES)
    if typ == "hospital":
        return rng.choice(sv.HOSPITALS)
    if typ == "disease":
        return rng.choice(sv.DISEASES_COMMON + sv.DISEASES_RARE)
    if typ == "drug":
        return rng.choice(sv.DRUGS)
    if typ == "occupation":
        return rng.choice(sv.OCCUPATIONS)
    if typ == "employer":
        return rng.choice(sv.COMPANIES)
    if typ == "school":
        return rng.choice(sv.SCHOOLS)
    if typ == "bank":
        return rng.choice(sv.BANKS)
    if typ == "age":
        return f"{rng.randint(20, 80)}岁"
    if typ == "gender":
        return rng.choice(["男", "女"])
    if typ == "income":
        return f"年收入约{rng.choice([6, 12, 20, 40])}万元"
    if typ == "id_card":
        return "11010119900307" + "".join(str(rng.randint(0, 9)) for _ in range(4))
    if typ == "bank_card":
        return "6222 " + " ".join("".join(str(rng.randint(0, 9)) for _ in range(4)) for _ in range(3))
    if typ == "email":
        return f"user{rng.randint(100, 999)}@example.com"
    if typ == "amount":
        return sv.money(rng, 1000, 500000)
    return None


def prism_random_artifact(view, seed=20261118):
    """Consistent random same-type replacement for every occurrence.

    This is a PRISM-style perturbation baseline, not a formal LDP mechanism.
    """
    text = view["prompt"]
    entities = sorted(view["runtime_entities"],
                      key=lambda e: len(e["value"]), reverse=True)
    mapping, applied = {}, []
    for e in entities:
        key = (e["type"], e["value"])
        if key not in mapping:
            h = zlib.crc32(f"{seed}|{e['type']}|{e['value']}".encode())
            rng = random.Random(h)
            rep = _random_replacer(e["type"], rng)
            if rep is None:
                rep = f"[{e['type'].upper()}_{h % 100:02d}]"
            mapping[key] = rep
        rep = mapping[key]
        if e["value"] in text:
            text = text.replace(e["value"], rep)
            applied.append({"type": e["type"], "from": e["value"], "to": rep,
                            "task_relevant": bool(e.get("task_relevant"))})
    return {"D": text, "applied": applied, "method_detail": "prism_random"}


def build_artifact(method, view, seed=20261118):
    entities = view["runtime_entities"]
    if method == "hardline_only":
        out = deterministic_dehydrate(view, entities=entities)
        return {"D": out["D"], "applied": [], "method_detail": "typed_placeholders"}
    if method == "generalization_only":
        out = det_dehydrate(view, entities=entities)
        return {"D": out["D"], "applied": out["applied"], "method_detail": "det_generalization"}
    if method == "prism_random":
        return prism_random_artifact(view, seed=seed)
    if method == "intact_style":
        candidates = [
            ("placeholder", deterministic_dehydrate(view, entities=entities)["D"]),
            ("generalized", det_dehydrate(view, entities=entities)["D"]),
            ("loosen", det_loosen(view, entities=entities)["D"]),
        ]
        best = None
        for name, D in candidates:
            attack = local_literal_attack(view, D)
            util = local_utility(view, D)
            if attack["n_probes"] > 0 and attack["L"] <= TAU_L:
                score = util["U"]
                if best is None or score > best[0]:
                    best = (score, name, D)
        if best is None:
            return {"D": candidates[0][1], "applied": [],
                    "method_detail": "intact_style_no_private_candidate"}
        return {"D": best[2], "applied": [], "method_detail": f"intact_style_{best[1]}"}
    if method == "closed_loop":
        S = [f"{ATTR_NAMES.get(e['type'], e['type'])}={e['value']}" for e in entities]
        state = {"contrib": {s: 0.0 for s in S}}

        def evaluate_fn(D, Q, S_, X):
            attack = local_literal_attack(view, D)
            util = local_utility(view, D)
            for e, s in zip(entities, S):
                state["contrib"][s] = 1.0 if e["value"] in attack["hit_values"] else 0.0
            return {"hits": attack["hits"], "n_probes": attack["n_probes"],
                    "L": attack["L"], "U": util["U"], "R": util["U"]}

        def leak_contrib_fn(D, S_):
            return dict(state["contrib"])

        res = lexicographic_loop(
            view["prompt"], S, None, None,
            dehydrate_fn=lambda X, S_, P: det_dehydrate(view, entities=entities)["D"],
            strengthen_fn=lambda D, s, X, S_, P: (
                lambda r: r["D"] if r.get("changed") else None)(
                    det_strengthen(D, view, s, {}, entities=entities)),
            loosen_fn=lambda D, X, S_, P: det_loosen(view, entities=entities)["D"],
            evaluate_fn=evaluate_fn, leak_contrib_fn=leak_contrib_fn,
            tau_l=TAU_L, tau_u=TAU_U_LOCAL, tau_r=TAU_U_LOCAL,
            n_stable=N_STABLE, delta=DELTA)
        scrub = hard_line_scrub(res.D, view, entities=entities)
        final = stable_decision(view, scrub["D"])
        status = "PASS" if res.status == "PASS" and final["release"] else "INFEASIBLE"
        return {"D": scrub["D"], "applied": [], "method_detail": "closed_loop_stable_hardline",
                "loop_status": res.status, "loop_rounds": res.rounds,
                "loop_evaluations": res.n_evaluations,
                "final_stable": final, "status_override": status,
                "scrub_removed": scrub["removed"]}
    raise ValueError(method)


def run_runtime_item(source, method="closed_loop", task_profile="mixed",
                     entities=None, seed=20261118):
    if entities is None:
        entities = runtime_extract(source["prompt"])
    view = runtime_view(source, entities, task_profile=task_profile)
    art = build_artifact(method, view, seed=seed)
    decision = art.get("final_stable") or stable_decision(view, art["D"])
    if art.get("status_override"):
        decision = {**decision, "status": art["status_override"],
                    "release": art["status_override"] == "PASS"}
    return {"id": source.get("id"), "domain": source.get("domain"),
            "method": method, "task_profile": task_profile,
            "D": art["D"], "n_runtime_entities": len(entities),
            "status": decision["status"], "release": decision["release"],
            "L_local": decision["L"], "U_local": decision["U"],
            "hits_local": decision["hits"], "n_probes_local": decision["n_probes"],
            "stable": decision["stable"], "method_detail": art["method_detail"],
            "loop_rounds": art.get("loop_rounds"),
            "loop_evaluations": art.get("loop_evaluations"),
            "runtime_entities": entities}


def gold_entities(item):
    ann = item["annotations"]
    return ann["explicit_identifiers"] + ann["quasi_identifiers"]


def external_gold_audit(item, D, runtime_entities):
    """External scoring only.  Call after local artifact/decision are frozen."""
    gold = gold_entities(item)
    runtime_vals = {e["value"] for e in runtime_entities}
    gold_vals = {e["value"] for e in gold}
    text = _nfkc_norm(D)
    hits = [e["value"] for e in gold if _nfkc_norm(e["value"]) in text]
    missed = sorted(gold_vals - runtime_vals)
    extra = sorted(runtime_vals - gold_vals)
    return {"n_gold": len(gold_vals), "gold_literal_hits": len(hits),
            "gold_literal_hit_values": hits,
            "gold_L": len(hits) / len(gold_vals) if gold_vals else 0.0,
            "missed_gold_values": missed, "extra_runtime_values": extra,
            "recall": len(gold_vals & runtime_vals) / len(gold_vals) if gold_vals else 1.0,
            "over_extraction": len(extra)}
