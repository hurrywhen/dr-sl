#!/usr/bin/env python3
"""Two-type residual-report mechanism probe (round 3, protocol v3 §0).

The round-2 finding "residual-report recall of gold residue = 0" is scoped:
all observed gold residue came from NEVER-EXTRACTED attributes (type b), which
cannot appear in runtime-S reports by construction, and PASS instances have no
report at all.  This constructed probe tests the report mechanism under BOTH
residue types:

  type a: an EXTRACTED attribute value re-inserted into the frozen artifact
          (simulating a failed scrub of a known attribute);
  type b: the never-extracted gold residue already present.

For each probe instance the real loop machinery is run on the injected
artifact (same parameters as the frozen closed loop), followed by the same
all-occurrence scrub and stable decision.  We measure: first-evaluation
detectability of type a, residual-report coverage of type a (INFEASIBLE exits),
scrub removal of type a, and persistence/report coverage of type b.

This is a constructed mechanism test, not a deployment failure-rate estimate.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "dataset"))

from pipeline import ATTR_NAMES, det_dehydrate, det_loosen, det_strengthen, hard_line_scrub
from loop import lexicographic_loop
from protocol import DELTA, TAU_L
from qi import load_dataset
from runtime import (DET_N_STABLE, TAU_U_LOCAL, local_literal_attack,
                     local_utility, runtime_view, stable_decision)
from runtime_extractor import runtime_extract

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "results" / "revision_round3"
R2 = ROOT / "results" / "revision_20261121"


def _evasion_variant(value):
    """A normalized-equivalent variant that exact substring replacement misses.

    ASCII digits/letters -> fullwidth (NFKC-normalizes back); pure-CJK values
    get interpuncts inserted (punct-normalization strips them).  The local
    attack's normalized strategies detect these, but det_strengthen and
    hard_line_scrub use exact replacement, so the residue persists at loop
    exit -- the 'extracted but not successfully scrubbed' condition.
    """
    if any(c.isascii() and c.isalnum() for c in value):
        return "".join(chr(ord(c) + 0xFEE0) if c.isascii() and c.isalnum() else c
                       for c in value)
    return "·".join(value)


def run_probe(item, frozen_row, mode):
    ents = runtime_extract(item["prompt"])
    view = runtime_view(item, ents, task_profile="mixed")
    D0 = frozen_row["D"]
    # type a: re-insert one extracted value (simulated scrub failure).  Choose
    # an entity whose value is not already present (normalized) in D0, so the
    # probe measures the injected residue, not pre-existing residue.
    from runtime import _nfkc_norm
    d0n = _nfkc_norm(D0)
    candidates = [e for e in ents if _nfkc_norm(e["value"]) not in d0n]
    if not candidates:
        return None
    injected = candidates[0]
    inj_text = injected["value"] if mode == "exact" else _evasion_variant(injected["value"])
    D_inj = D0 + "〔复核残留〕" + inj_text
    # type b: never-extracted gold values still present in D0.
    type_b = list(frozen_row.get("gold_literal_hit_values", []))

    S = [f"{ATTR_NAMES.get(e['type'], e['type'])}={e['value']}" for e in ents]
    state = {"contrib": {s: 0.0 for s in S}, "first_hits": None}

    def evaluate_fn(D, Q, S_, X):
        attack = local_literal_attack(view, D)
        util = local_utility(view, D)
        if state["first_hits"] is None:
            state["first_hits"] = list(attack["hit_values"])
        for e, s in zip(ents, S):
            state["contrib"][s] = 1.0 if e["value"] in attack["hit_values"] else 0.0
        return {"hits": attack["hits"], "n_probes": attack["n_probes"],
                "L": attack["L"], "U": util["U"], "R": util["U"]}

    res = lexicographic_loop(
        view["prompt"], S, None, None,
        dehydrate_fn=lambda X, S_, P: D_inj,
        strengthen_fn=lambda D, s, X, S_, P: (
            lambda r: r["D"] if r.get("changed") else None)(
                det_strengthen(D, view, s, {}, entities=ents)),
        loosen_fn=lambda D, X, S_, P: det_loosen(view, entities=ents)["D"],
        evaluate_fn=evaluate_fn, leak_contrib_fn=lambda D, S_: dict(state["contrib"]),
        tau_l=TAU_L, tau_u=TAU_U_LOCAL, tau_r=TAU_U_LOCAL,
        n_stable=DET_N_STABLE, delta=DELTA)
    scrub = hard_line_scrub(res.D, view, entities=ents)
    final = stable_decision(view, scrub["D"], n_stable=DET_N_STABLE)
    status = "PASS" if res.status == "PASS" and final["release"] else "INFEASIBLE"

    inj_s = f"{ATTR_NAMES.get(injected['type'], injected['type'])}={injected['value']}"
    report = res.residual_leak_report or []
    report_pos = {r["s"] for r in report if (r.get("contrib") or 0) > 0}
    from runtime import _nfkc_norm
    final_text = _nfkc_norm(scrub["D"])
    b_persist = [v for v in type_b if _nfkc_norm(v) in final_text]
    return {
        "id": item["id"], "domain": item["domain"], "mode": mode,
        "injected_type": injected["type"], "injected_value": injected["value"],
        "type_a_detected_first_eval": injected["value"] in (state["first_hits"] or []),
        "loop_status": res.status, "final_status": status,
        "type_a_present_at_loop_exit": _nfkc_norm(injected["value"]) in _nfkc_norm(res.D),
        "type_a_in_report_positive": inj_s in report_pos,
        "type_a_removed_by_scrub": _nfkc_norm(injected["value"]) not in final_text,
        "type_b_values": type_b,
        "type_b_persist_after_scrub": b_persist,
        "type_b_in_report_positive": any(
            r["s"].split("=", 1)[-1] in type_b and (r.get("contrib") or 0) > 0
            for r in report),
        "report_size": len(report),
    }


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    items = {r["id"]: r for r in load_dataset(str(ROOT / "dataset/output/dr_sl_holdout_v1.jsonl"))}
    rows = [json.loads(l) for l in (R2 / "offline_runtime.jsonl").open(encoding="utf-8")]
    cl = [r for r in rows if r["dataset"] == "holdout80"
          and r["sensitive_set"] == "runtime" and r["method"] == "closed_loop"]
    probes = []
    n_skipped = 0
    for r in cl:
        if r["gold_literal_hits"] > 0 and r["n_runtime_entities"] > 0:
            for mode in ("exact", "evasion"):
                p = run_probe(items[r["id"]], r, mode)
                if p is None:
                    n_skipped += 1
                else:
                    probes.append(p)
    out = {"n_skipped_no_clean_injection_site": n_skipped,
           "design": "constructed two-type residue probe; type a = extracted value re-inserted "
                     "(simulated scrub failure), type b = never-extracted gold residue; "
                     "mode exact = verbatim re-insertion, mode evasion = normalized-equivalent "
                     "variant that exact replacement misses",
           "note_pass": "PASS instances have no residual report by construction; the round-2 "
                        "PASS-stratum recall of 0 is definitional, not evidence about report quality"}
    for mode in ("exact", "evasion"):
        ps = [p for p in probes if p["mode"] == mode]
        n = len(ps)
        n_inf = sum(1 for p in ps if p["loop_status"] == "INFEASIBLE")
        out[mode] = {
            "n_probes": n,
            "type_a_detected_first_eval": sum(p["type_a_detected_first_eval"] for p in ps) / n,
            "type_a_present_at_loop_exit": sum(p["type_a_present_at_loop_exit"] for p in ps) / n,
            "type_a_removed_by_scrub": sum(p["type_a_removed_by_scrub"] for p in ps) / n,
            "n_infeasible_exits": n_inf,
            "type_a_report_coverage_among_infeasible": (
                sum(p["type_a_in_report_positive"] for p in ps if p["loop_status"] == "INFEASIBLE")
                / n_inf if n_inf else None),
            "type_b_persistence_fraction": sum(1 for p in ps if p["type_b_persist_after_scrub"]) / n,
            "type_b_report_coverage": sum(p["type_b_in_report_positive"] for p in ps) / n,
        }
    out["probes"] = probes
    (OUT / "residual_probe.json").write_text(json.dumps(out, ensure_ascii=False, indent=2))
    print(json.dumps({k: v for k, v in out.items() if k != "probes"}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
