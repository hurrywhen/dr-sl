#!/usr/bin/env python3
"""Round-5 neural-contrast credibility experiments (protocol v5 §2–§4).

DIAGNOSTIC ONLY — every condition is cloud-assisted (extraction itself discloses
X); none is a deployable local gate.  Pre-registered before any call:

- stability_r1 / stability_r2: qwen3.8-max, round-4 frozen prompt BYTE-IDENTICAL
  (original incomplete taxonomy), submitted seeds 20261126 / 20261127, on a
  deterministic 60-instance subset (first 5 per domain in sorted-id order from
  each of holdout-1, holdout-3, drift-p000).  120 calls.
- family_glm: glm-5.2 (online_alt, second model family), same subset, same
  round-4 prompt, submitted seed 20261128.  60 calls.
- h4_complete: qwen3.8-max, prompt v2 = round-4 prompt + exactly three added
  type declarations (room_no, marriage_years, work_years; complete 43-type
  taxonomy), submitted seed 20261129, on NEW holdout-4 (template family #4,
  natural mix, seed 20261125; generated before any h4 result was inspected).
  80 calls.  Pre-registered expectation: FR_taxonomy_gap = 0 on h4 (coverage
  asserted); any residual FR is a declared-type miss.  No prompt amendment
  after inspection.

Also runs the deterministic reference on holdout-4 (original + fixed extractor,
offline, no calls).  Raw responses archived in neural_round5_cache.jsonl
(resumable; keyed by condition × prompt-sha256).  The round-4 archive is kept
byte-intact; round-4 results are NOT relabelled or recomputed with prompt v2.
"""
import hashlib
import json
import os
import sys
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "dataset"))

from backends import make_backend
from qi import load_dataset
from revision_neural_extractor import (EXTRACT_SYSTEM, TYPES, audit_with_task,
                                       parse_proposals, sha, summarize)
from revision_neural_analysis import (char_coverage, coverage_block,
                                      fr_decomposition, gold_type_map,
                                      load_items, partial_span_values)
from revision_stats import cluster_bootstrap, paired_delta, wilson_interval
from runtime import MIXED_TASK_TYPES, local_utility, runtime_view, run_runtime_item
from runtime_extractor import _EXPLICIT_TYPES, runtime_extract
from runtime_extractor_fixed import runtime_extract_fixed

ROOT = Path(__file__).resolve().parent.parent
R3 = ROOT / "results" / "revision_round3"
MAX_WORKERS = int(os.environ.get("REVISION_AUDIT_WORKERS", "4"))
METHODS = ("closed_loop", "generalization_only")

# Complete taxonomy (protocol v5 §4): mechanical union, verified by
# sim/test_neural_taxonomy.py to cover every dataset's gold types.
TYPES_V2 = TYPES | {"room_no", "marriage_years", "work_years"}

# Prompt v2: round-4 prompt with EXACTLY three added type declarations;
# every other instruction byte-identical (asserted below).
_MARKER = "children_count(孩子个数)。"
assert EXTRACT_SYSTEM.count(_MARKER) == 1
EXTRACT_SYSTEM_V2 = EXTRACT_SYSTEM.replace(
    _MARKER, "children_count(孩子个数), room_no(房间号), marriage_years(婚龄), work_years(工作年限)。")

SUBSET_DATASETS = (("holdout80", "dr_sl_holdout_v1.jsonl"),
                   ("holdout80_v3", "dr_sl_holdout_v3.jsonl"),
                   ("drift_p000", "dr_sl_drift_p000.jsonl"))
CONDITIONS = {
    "stability_r1": {"role": "online_strong", "seed": 20261126, "prompt": EXTRACT_SYSTEM,
                     "types": TYPES, "prompt_version": "v1_round4", "data": "subset"},
    "stability_r2": {"role": "online_strong", "seed": 20261127, "prompt": EXTRACT_SYSTEM,
                     "types": TYPES, "prompt_version": "v1_round4", "data": "subset"},
    "family_glm": {"role": "online_alt", "seed": 20261128, "prompt": EXTRACT_SYSTEM,
                   "types": TYPES, "prompt_version": "v1_round4", "data": "subset"},
    "h4_complete": {"role": "online_strong", "seed": 20261129, "prompt": EXTRACT_SYSTEM_V2,
                    "types": TYPES_V2, "prompt_version": "v2_complete", "data": "holdout80_v4"},
}


def locate_with_types(text, proposals, types):
    """Exact-substring localization, algorithmically identical to
    revision_neural_extractor.locate but with an explicit taxonomy parameter
    (the round-4 function is TYPES-fixed and kept byte-intact)."""
    found, unloc, unknown = [], 0, 0
    seen = set()
    for typ, val in proposals:
        if typ not in types:
            unknown += 1
            continue
        start, any_occ = 0, False
        while True:
            idx = text.find(val, start)
            if idx < 0:
                break
            any_occ = True
            key = (typ, val, idx)
            if key not in seen:
                seen.add(key)
                found.append({"type": typ, "value": val, "span": [idx, idx + len(val)],
                              "category": "explicit" if typ in _EXPLICIT_TYPES else "quasi",
                              "source": "neural_llm"})
            start = idx + len(val)
        if not any_occ:
            unloc += 1
    found.sort(key=lambda e: (-(e["span"][1] - e["span"][0]), e["span"][0], e["type"]))
    kept, occupied = [], []
    for e in found:
        s, t = e["span"]
        if any(not (t <= a or s >= b) for a, b in occupied):
            continue
        kept.append(e)
        occupied.append((s, t))
    kept.sort(key=lambda e: e["span"][0])
    return kept, unloc, unknown


def select_subset():
    """First 5 instances per domain in sorted-id order, per dataset (60 total)."""
    out = []
    for ds, fname in SUBSET_DATASETS:
        items = load_items(fname)
        by_domain = defaultdict(list)
        for i in sorted(items):
            by_domain[items[i]["domain"]].append(i)
        for dom in sorted(by_domain):
            for i in by_domain[dom][:5]:
                out.append((ds, items[i]))
    assert len(out) == 60
    return out


def run_rows(item, ents, dataset, condition, meta):
    rows = []
    for m in METHODS:
        r = run_runtime_item(item, method=m, task_profile="mixed", entities=ents)
        view = runtime_view(item, ents, task_profile="mixed")
        util = local_utility(view, r["D"])
        audit = audit_with_task(item, r["D"], ents)
        row = {"dataset": dataset, "condition": condition, "extractor": "neural_llm",
               "sensitive_set": "runtime", **r, **audit,
               "U_basis": util["basis"],
               "utility_fallback": util["basis"] == "unmarked_context",
               "char_coverage": char_coverage(item, ents),
               "n_partial_span_values": len(partial_span_values(item, ents)),
               "artifact_sha256": sha(r["D"]),
               "n_proposed": meta["n_proposed"], "n_unlocatable": meta["n_unlocatable"],
               "n_unknown_type": meta["n_unknown_type"]}
        has_task = any(e["type"] in MIXED_TASK_TYPES.get(item["domain"], set()) for e in ents)
        gated = dict(row)
        gated["method"] = m + "_covgate"
        if not has_task:
            gated.update({"status": "UNSCORABLE", "release": False,
                          "coverage_gate": "no_task_attributes_extracted"})
        else:
            gated["coverage_gate"] = "ok"
        rows.extend([row, gated])
    return rows


def entity_set(ents):
    return {(e["type"], e["value"], e["span"][0], e["span"][1]) for e in ents}


def main():
    R3.mkdir(parents=True, exist_ok=True)
    cache_path = R3 / "neural_round5_cache.jsonl"
    cache = {}
    if cache_path.exists():
        for l in cache_path.open(encoding="utf-8"):
            r = json.loads(l)
            if "entities" in r:
                cache[(r["condition"], r["prompt_sha256"])] = r

    subset = select_subset()
    h4 = [("holdout80_v4", it) for it in load_dataset(str(ROOT / "dataset/output/dr_sl_holdout_v4.jsonl"))]
    # Coverage assertion (pre-registered): h4 gold types fully declared in v2.
    h4_types = {t for _, it in h4 for t in gold_type_map(it).values()}
    assert h4_types <= TYPES_V2, h4_types - TYPES_V2

    jobs = []
    for cond, cfg in CONDITIONS.items():
        data = subset if cfg["data"] == "subset" else h4
        for ds, it in data:
            if (cond, sha(it["prompt"])) not in cache:
                jobs.append((cond, ds, it))
    backends = {cfg["role"]: make_backend(cfg["role"], timeout=180, retries=1, seed=cfg["seed"])
                for cfg in CONDITIONS.values()}
    print(f"round-5 neural: {len(jobs)} new calls ({len(cache)} cached); "
          f"conditions {list(CONDITIONS)}", flush=True)

    new_records, errors = [], []

    def call(job):
        cond, ds, it = job
        cfg = CONDITIONS[cond]
        b = backends[cfg["role"]]
        try:
            raw = b.complete(cfg["prompt"], "文本：\n" + it["prompt"])
            proposals, ok = parse_proposals(raw)
            if not ok:
                return {"condition": cond, "prompt_sha256": sha(it["prompt"]), "id": it["id"],
                        "dataset": ds, "error": "parse_failure", "raw": raw}
            ents, unloc, unknown = locate_with_types(it["prompt"], proposals, cfg["types"])
            return {"condition": cond, "prompt_sha256": sha(it["prompt"]), "id": it["id"],
                    "dataset": ds, "model": b.config.model, "seed_submitted": cfg["seed"],
                    "prompt_version": cfg["prompt_version"], "raw": raw,
                    "n_proposed": len(proposals), "n_unlocatable": unloc,
                    "n_unknown_type": unknown, "entities": ents}
        except Exception as e:
            return {"condition": cond, "prompt_sha256": sha(it["prompt"]), "id": it["id"],
                    "dataset": ds, "error": str(e)[:300]}

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as ex:
        futs = [ex.submit(call, j) for j in jobs]
        for i, fut in enumerate(as_completed(futs), 1):
            r = fut.result()
            if r.get("error"):
                errors.append(r)
            else:
                cache[(r["condition"], r["prompt_sha256"])] = r
                new_records.append(r)
            if i % 40 == 0:
                print(f"progress {i}/{len(jobs)} errors={len(errors)}", flush=True)
    if errors:
        retry, errors2 = [], []
        jmap = {(c, sha(it["prompt"])): (c, ds, it) for c, ds, it in
                [(c, ds, it) for c in CONDITIONS for ds, it in (subset if CONDITIONS[c]["data"] == "subset" else h4)]}
        for r in errors:
            rr = call(jmap[(r["condition"], r["prompt_sha256"])])
            (errors2 if rr.get("error") else retry).append(rr)
        for r in retry:
            cache[(r["condition"], r["prompt_sha256"])] = r
            new_records.append(r)
        errors = errors2
    with cache_path.open("a", encoding="utf-8") as f:
        for r in new_records:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    # Rows + per-condition summaries.
    all_rows = []
    cond_summaries = {}
    for cond, cfg in CONDITIONS.items():
        data = subset if cfg["data"] == "subset" else h4
        rows = []
        for ds, it in data:
            c = cache.get((cond, sha(it["prompt"])))
            if c is None:
                continue
            meta = {k: c[k] for k in ("n_proposed", "n_unlocatable", "n_unknown_type")}
            rows.extend(run_rows(it, c["entities"], ds, cond, meta))
        all_rows.extend(rows)
        items = {it["id"]: it for _, it in data}
        methods = summarize(rows)
        cl = [r for r in rows if r["method"] == "closed_loop"]
        props = {}
        for r in cl:
            c = cache[(cond, sha(items[r["id"]]["prompt"]))]
            props[r["id"]], _ = parse_proposals(c["raw"])
        dec = fr_decomposition(cl, items, cfg["types"], props)
        cov = coverage_block(cl, items)
        paired = {}
        for ds in sorted({r["dataset"] for r in rows}):
            a = {r["id"]: r for r in rows if r["dataset"] == ds and r["method"] == "closed_loop"}
            b = {r["id"]: r for r in rows if r["dataset"] == ds and r["method"] == "generalization_only"}
            ids = sorted(set(a) & set(b))
            if ids:
                paired[ds] = {
                    "release_delta": paired_delta({i: float(a[i]["release"]) for i in ids},
                                                  {i: float(b[i]["release"]) for i in ids}),
                    "gold_L_delta": paired_delta({i: a[i]["gold_L"] for i in ids},
                                                 {i: b[i]["gold_L"] for i in ids}),
                    "U_delta": paired_delta({i: a[i]["U_local"] for i in ids},
                                            {i: b[i]["U_local"] for i in ids})}
        cond_summaries[cond] = {
            "model": backends[cfg["role"]].config.model, "seed_submitted": cfg["seed"],
            "prompt_version": cfg["prompt_version"],
            "taxonomy_n": len(cfg["types"]),
            "n_instances": len(data), "n_extracted": len(cl),
            "extraction_stats": {
                "n_proposed_total": sum(cache[(cond, sha(it["prompt"]))]["n_proposed"] for _, it in data if (cond, sha(it["prompt"])) in cache),
                "n_unlocatable_total": sum(cache[(cond, sha(it["prompt"]))]["n_unlocatable"] for _, it in data if (cond, sha(it["prompt"])) in cache),
                "n_unknown_type_total": sum(cache[(cond, sha(it["prompt"]))]["n_unknown_type"] for _, it in data if (cond, sha(it["prompt"])) in cache)},
            "methods": methods, "fr_decomposition": dec, "coverage_layers": cov,
            "paired": paired}
    with (R3 / "neural_round5_rows.jsonl").open("w", encoding="utf-8") as f:
        for r in all_rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    # Stability: entity-set agreement of r1/r2 vs the round-4 run (seed 20261124).
    r4cache = {}
    for l in (R3 / "neural_extraction_cache.jsonl").open(encoding="utf-8"):
        r = json.loads(l)
        r4cache[r["prompt_sha256"]] = r
    stability = {}
    for cond in ("stability_r1", "stability_r2", "family_glm"):
        exact, jacc = [], []
        per_ds = defaultdict(lambda: {"exact": 0, "n": 0})
        for ds, it in subset:
            c = cache.get((cond, sha(it["prompt"])))
            c0 = r4cache.get(sha(it["prompt"]))
            if c is None or c0 is None:
                continue
            a, b = entity_set(c["entities"]), entity_set(c0["entities"])
            eq = a == b
            exact.append(eq)
            jacc.append(len(a & b) / len(a | b) if a | b else 1.0)
            per_ds[ds]["exact"] += eq
            per_ds[ds]["n"] += 1
        stability[cond] = {
            "vs_round4_seed20261124": {
                "n": len(exact),
                "exact_entity_set_agreement": sum(exact) / len(exact) if exact else None,
                "mean_jaccard": sum(jacc) / len(jacc) if jacc else None,
                "by_dataset": {k: dict(v) for k, v in per_ds.items()}}}
    # r1 vs r2 agreement (sampling variation between two fresh runs).
    e12, j12 = [], []
    for ds, it in subset:
        c1 = cache.get(("stability_r1", sha(it["prompt"])))
        c2 = cache.get(("stability_r2", sha(it["prompt"])))
        if c1 and c2:
            a, b = entity_set(c1["entities"]), entity_set(c2["entities"])
            e12.append(a == b)
            j12.append(len(a & b) / len(a | b) if a | b else 1.0)
    stability["r1_vs_r2"] = {"n": len(e12),
                             "exact_entity_set_agreement": sum(e12) / len(e12) if e12 else None,
                             "mean_jaccard": sum(j12) / len(j12) if j12 else None}

    # Deterministic reference on holdout-4 (offline, no calls).
    det_rows = []
    for ds, it in h4:
        for ex_name, fn in (("original", runtime_extract), ("fixed", runtime_extract_fixed)):
            ents = fn(it["prompt"])
            for m in METHODS:
                r = run_runtime_item(it, method=m, task_profile="mixed", entities=ents)
                view = runtime_view(it, ents, task_profile="mixed")
                util = local_utility(view, r["D"])
                audit = audit_with_task(it, r["D"], ents)
                row = {"dataset": "holdout80_v4", "extractor": ex_name,
                       "sensitive_set": "runtime", **r, **audit,
                       "U_basis": util["basis"],
                       "utility_fallback": util["basis"] == "unmarked_context",
                       "char_coverage": char_coverage(it, ents),
                       "artifact_sha256": sha(r["D"])}
                has_task = any(e["type"] in MIXED_TASK_TYPES.get(it["domain"], set()) for e in ents)
                gated = dict(row)
                gated["method"] = m + "_covgate"
                if not has_task:
                    gated.update({"status": "UNSCORABLE", "release": False,
                                  "coverage_gate": "no_task_attributes_extracted"})
                else:
                    gated["coverage_gate"] = "ok"
                det_rows.extend([row, gated])
    with (R3 / "offline_h4.jsonl").open("w", encoding="utf-8") as f:
        for r in det_rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    det_methods = {}
    for ex in ("original", "fixed"):
        # summarize() groups by (dataset, method); run it per extractor so the
        # two variants are not pooled, then namespace keys by extractor.
        sub = summarize([r for r in det_rows if r["extractor"] == ex])
        for k, v in sub.items():
            det_methods[f"holdout80_v4/{ex}/{k.split('/', 1)[1]}"] = v
    det_paired = {}
    items4 = {it["id"]: it for _, it in h4}
    for ex in ("original", "fixed"):
        a = {r["id"]: r for r in det_rows if r["extractor"] == ex and r["method"] == "closed_loop"}
        b = {r["id"]: r for r in det_rows if r["extractor"] == ex and r["method"] == "generalization_only"}
        ids = sorted(set(a) & set(b))
        det_paired[ex] = {
            "release_delta": paired_delta({i: float(a[i]["release"]) for i in ids},
                                          {i: float(b[i]["release"]) for i in ids}),
            "gold_L_delta": paired_delta({i: a[i]["gold_L"] for i in ids},
                                         {i: b[i]["gold_L"] for i in ids}),
            "U_delta": paired_delta({i: a[i]["U_local"] for i in ids},
                                    {i: b[i]["U_local"] for i in ids})}
    det_dec = {}
    for ex in ("original", "fixed"):
        cl = [r for r in det_rows if r["extractor"] == ex and r["method"] == "closed_loop"]
        # deterministic extractor has no declared-taxonomy restriction; use the
        # full gold type set so every residual is a "declared-type miss" analogue
        det_dec[ex] = fr_decomposition(cl, items4, set().union(*(set(gold_type_map(it)) for it in items4.values())))
    (R3 / "offline_h4_summary.json").write_text(json.dumps(
        {"dataset": "holdout80_v4", "n": len(h4),
         "realized_old_vocab_fraction": sum(it["realized_old_vocab_fraction"] or 0 for _, it in h4) / len(h4),
         "methods": det_methods, "paired": det_paired, "fr_decomposition": det_dec},
        ensure_ascii=False, indent=2))

    summary = {"protocol": "revision_protocol_v5.md §2–§4",
               "design": "cloud-assisted DIAGNOSTIC conditions; single-run per condition; "
                         "instance-level intervals only (sampling variation characterized "
                         "on the 60-instance subset, not population CIs)",
               "subset_rule": "first 5 per domain in sorted-id order, 20/dataset, 60 total",
               "prompt_v2": EXTRACT_SYSTEM_V2,
               "taxonomy_v2_n": len(TYPES_V2),
               "conditions": cond_summaries, "stability": stability,
               "n_errors": len(errors), "errors": errors}
    (R3 / "neural_round5_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2))
    for cond, s in cond_summaries.items():
        for k, v in s["methods"].items():
            if k.endswith("_covgate") or not k.endswith("closed_loop"):
                continue
            d = s["fr_decomposition"]
            print(f"{cond} {k}: recall={v['recall']['estimate']:.3f} "
                  f"charcov={s['coverage_layers']['sensitive_char_coverage']['estimate']:.3f} "
                  f"rel={v['release_rate']:.3f} FR={d['FalseRelease_gold']['k']}/{d['n_pass']} "
                  f"gap={d['FR_taxonomy_gap']['k']} decl={d['FR_declared_type_miss']['k']}")
    print("stability:", json.dumps({k: {kk: vv for kk, vv in v.items() if kk != 'by_dataset'}
                                     for k, v in stability.items()}, ensure_ascii=False))
    print("errors:", len(errors), "| wrote", R3 / "neural_round5_summary.json")


if __name__ == "__main__":
    main()
