#!/usr/bin/env python3
"""Cloud-assisted neural extractor contrast (round 4, protocol v4 §7).

DIAGNOSTIC ONLY.  Extraction sends the original X to a cloud LLM API, which is
itself a first disclosure; this condition is NOT a deployable local gate under
the paper's trust model and supports no local-neural-gating claim.  Its purpose
is to test whether the audited failures are specific to the deterministic
regex/lexicon implementation, and whether a neural extractor is robust to the
constructive vocabulary displacement (drift p000).

Frozen design (no tuning after results are inspected):
- Extractor: online_strong (qwen3.8-max), frozen system prompt below, no gold
  annotations, no lexicon lists; submitted seed 20261124 (honoring not guaranteed).
- Localization: each proposed value is located by EXACT substring search (all
  occurrences); unlocatable proposals are discarded and counted; overlaps are
  resolved longest-first exactly as in the deterministic extractor.
- Sets: holdout-1 (80), holdout-3 (80), drift p000 (40).  Methods closed_loop /
  generalization_only under the SAME gates and "mixed" task profile, plus
  coverage-gate variants.  Raw responses, model, seed, parse failures and
  unlocatable counts are archived; extraction is cached by SHA-256(X), resumable.
"""
import hashlib
import json
import os
import re
import sys
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "dataset"))

from backends import make_backend
from qi import load_dataset
from revision_stats import cluster_bootstrap, paired_delta, wilson_interval
from runtime import (MIXED_TASK_TYPES, external_gold_audit, gold_entities,
                     local_utility, runtime_view, run_runtime_item)
from runtime_extractor import _EXPLICIT_TYPES

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "results" / "revision_round3"
DATASETS = (("holdout80", "dr_sl_holdout_v1.jsonl"),
            ("holdout80_v3", "dr_sl_holdout_v3.jsonl"),
            ("drift_p000", "dr_sl_drift_p000.jsonl"))
METHODS = ("closed_loop", "generalization_only")
EXTRACTOR_ROLE = "online_strong"
EXTRACT_SEED = 20261124
MAX_WORKERS = int(os.environ.get("REVISION_AUDIT_WORKERS", "4"))

TYPES = {
    "name", "phone", "email", "id_card", "bank_card", "address",
    "medical_record_no", "passport", "plate", "case_no", "deposit_no",
    "order_no", "card_tail", "ticket_no", "insurance_id", "fund_account",
    "city", "hospital", "bank", "employer", "school", "airline", "hotel",
    "lawfirm", "court", "disease", "drug", "allergy", "occupation",
    "insurance_type", "case_type", "amount", "charge", "income", "date",
    "visit_date", "age", "flight_no", "duration", "children_count",
}

# Frozen extraction prompt (protocol v4 §7).  No gold, no lexicons.
EXTRACT_SYSTEM = (
    "你是中文合成记录的个人敏感信息抽取器。请从给定文本中抽取所有出现的个人敏感信息实体，"
    "输出且仅输出 JSON：{\"entities\":[{\"type\":\"类型\",\"value\":\"原文值\"}]}。"
    "value 必须是输入文本中逐字出现的子串，不得改写、归一化或编造；同一值多次出现只列一次。"
    "可用类型（仅限这些）：name(人名), phone(手机号), email(邮箱), id_card(身份证号), "
    "bank_card(银行卡号/账号), address(住址), medical_record_no(病历号), passport(护照号), "
    "plate(车牌), case_no(案号), deposit_no(存单号), order_no(订单号), card_tail(卡尾号), "
    "ticket_no(票据号), insurance_id(保单号), fund_account(资金账号), city(城市), "
    "hospital(医院), bank(银行), employer(单位/公司), school(学校), airline(航空公司), "
    "hotel(酒店), lawfirm(律所), court(法院), disease(疾病), drug(药品), allergy(过敏原), "
    "occupation(职业), insurance_type(险种), case_type(案由), amount(金额), "
    "charge(手续费/费用), income(收入), date(日期), visit_date(就诊/手术/入住日期), "
    "age(年龄), flight_no(航班号), duration(天数), children_count(孩子个数)。"
    "注意：金额/费用/收入要带单位（如\"150000元\"）；年龄带\"岁\"；日期按原文形式。"
    "没有可抽取实体时输出 {\"entities\":[]}。"
)


def sha(s):
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def parse_proposals(raw):
    """Parse the JSON entity list; return (proposals, parse_ok)."""
    s = str(raw).strip()
    s = re.sub(r"^```(?:json)?\s*", "", s)
    s = re.sub(r"\s*```$", "", s)
    a, b = s.find("{"), s.rfind("}")
    if a < 0 or b <= a:
        return [], False
    try:
        obj = json.loads(s[a:b + 1])
    except Exception:
        return [], False
    ents = obj.get("entities")
    if not isinstance(ents, list):
        return [], False
    out = []
    for e in ents:
        if isinstance(e, dict) and isinstance(e.get("type"), str) \
                and isinstance(e.get("value"), str) and e["value"]:
            out.append((e["type"].strip(), e["value"]))
    return out, True


def locate(text, proposals):
    """Exact-substring localization of all occurrences; longest-first overlap
    resolution identical to the deterministic extractor.  Returns
    (entities, n_unlocatable, n_unknown_type)."""
    found, unloc, unknown = [], 0, 0
    seen = set()
    for typ, val in proposals:
        if typ not in TYPES:
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


def audit_with_task(item, D, ents):
    a = external_gold_audit(item, D, ents)
    gt = [e for e in gold_entities(item) if e.get("task_relevant")]
    rv = {e["value"] for e in ents}
    a["n_gold_task"] = len(gt)
    a["task_recall"] = sum(1 for e in gt if e["value"] in rv) / len(gt) if gt else None
    return a


def run_rows(item, ents, dataset, meta):
    rows = []
    for m in METHODS:
        r = run_runtime_item(item, method=m, task_profile="mixed", entities=ents)
        view = runtime_view(item, ents, task_profile="mixed")
        util = local_utility(view, r["D"])
        audit = audit_with_task(item, r["D"], ents)
        row = {"dataset": dataset, "extractor": "neural_llm", "sensitive_set": "runtime",
               **r, **audit,
               "U_basis": util["basis"],
               "utility_fallback": util["basis"] == "unmarked_context",
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


def summarize(rows):
    out = {}
    groups = defaultdict(list)
    for r in rows:
        groups[(r["dataset"], r["method"])].append(r)
    for (ds, m), rs in sorted(groups.items()):
        n = len(rs)
        rel = [r for r in rs if r["release"]]
        wr = sum(1 for r in rel if r["gold_literal_hits"] > 0)
        tr = [r["task_recall"] for r in rs if r["task_recall"] is not None]
        out[f"{ds}/{m}"] = {
            "n": n,
            "release_rate": len(rel) / n,
            "release_rate_wilson95": list(wilson_interval(len(rel), n)),
            "recall": cluster_bootstrap({r["id"]: r["recall"] for r in rs}),
            "task_recall": cluster_bootstrap({r["id"]: r["task_recall"] for r in rs
                                              if r["task_recall"] is not None}) if tr else None,
            "over_extraction": cluster_bootstrap({r["id"]: r["over_extraction"] for r in rs}),
            "U_local": cluster_bootstrap({r["id"]: r["U_local"] for r in rs}),
            "gold_L": cluster_bootstrap({r["id"]: r["gold_L"] for r in rs}),
            "utility_fallback_fraction": sum(1 for r in rs if r["utility_fallback"]) / n,
            "utility_fallback_benign_fraction": sum(
                1 for r in rs if r["utility_fallback"] and r["n_gold_task"] == 0) / n,
            "utility_fallback_harmful_fraction": sum(
                1 for r in rs if r["utility_fallback"] and r["n_gold_task"] > 0) / n,
            "n_pass": len(rel),
            "pass_with_gold_residue": wr,
            "FalseRelease_gold": wr / len(rel) if rel else None,
            "FalseRelease_gold_wilson95": list(wilson_interval(wr, len(rel))) if rel else None,
        }
    return out


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    backend = make_backend(EXTRACTOR_ROLE, timeout=180, retries=1, seed=EXTRACT_SEED)
    cache_path = OUT / "neural_extraction_cache.jsonl"
    cache = {}
    if cache_path.exists():
        for l in cache_path.open(encoding="utf-8"):
            r = json.loads(l)
            if "entities" in r:
                cache[r["prompt_sha256"]] = r

    items = []
    for ds, fname in DATASETS:
        for it in load_dataset(str(ROOT / "dataset/output" / fname)):
            items.append((ds, it))
    todo = [(ds, it) for ds, it in items if sha(it["prompt"]) not in cache]
    print(f"neural extraction: {len(todo)} new calls ({len(cache)} cached); "
          f"model {backend.config.model}, seed {EXTRACT_SEED} submitted", flush=True)

    new_records, errors = [], []

    def call(t):
        ds, it = t
        try:
            raw = backend.complete(EXTRACT_SYSTEM, "文本：\n" + it["prompt"])
            proposals, ok = parse_proposals(raw)
            if not ok:
                return {"prompt_sha256": sha(it["prompt"]), "id": it["id"], "dataset": ds,
                        "error": "parse_failure", "raw": raw}
            ents, unloc, unknown = locate(it["prompt"], proposals)
            return {"prompt_sha256": sha(it["prompt"]), "id": it["id"], "dataset": ds,
                    "model": backend.config.model, "seed_submitted": EXTRACT_SEED,
                    "raw": raw, "n_proposed": len(proposals), "n_unlocatable": unloc,
                    "n_unknown_type": unknown, "entities": ents}
        except Exception as e:
            return {"prompt_sha256": sha(it["prompt"]), "id": it["id"], "dataset": ds,
                    "error": str(e)[:300]}

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as ex:
        futs = [ex.submit(call, t) for t in todo]
        for i, fut in enumerate(as_completed(futs), 1):
            r = fut.result()
            if r.get("error"):
                errors.append(r)
            else:
                cache[r["prompt_sha256"]] = r
                new_records.append(r)
            if i % 40 == 0:
                print(f"extraction progress {i}/{len(todo)} errors={len(errors)}", flush=True)
    # One retry pass for transient failures (recorded; no silent drops).
    if errors:
        retry, errors2 = [], []
        emap = {sha(it["prompt"]): (ds, it) for ds, it in items}
        for r in errors:
            ds, it = emap[r["prompt_sha256"]]
            rr = call((ds, it))
            (errors2 if rr.get("error") else retry).append(rr)
        for r in retry:
            cache[r["prompt_sha256"]] = r
            new_records.append(r)
        errors = errors2
    with cache_path.open("a", encoding="utf-8") as f:
        for r in new_records:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    rows = []
    for ds, it in items:
        c = cache.get(sha(it["prompt"]))
        if c is None:
            continue
        meta = {"n_proposed": c["n_proposed"], "n_unlocatable": c["n_unlocatable"],
                "n_unknown_type": c["n_unknown_type"]}
        rows.extend(run_rows(it, c["entities"], ds, meta))
    with (OUT / "neural_extractor_rows.jsonl").open("w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    summary = {"design": "cloud-assisted neural extractor contrast; DIAGNOSTIC ONLY "
                         "(extraction itself discloses X to the cloud; not a local gate)",
               "extractor_model": backend.config.model, "seed_submitted": EXTRACT_SEED,
               "prompt": EXTRACT_SYSTEM,
               "localization": "exact substring, all occurrences; unlocatable discarded; "
                               "longest-first overlap resolution",
               "n_instances": len(items), "n_extracted": len(items) - len(errors),
               "n_errors": len(errors),
               "extraction_stats": {
                   "n_proposed_total": sum(c["n_proposed"] for c in cache.values()),
                   "n_unlocatable_total": sum(c["n_unlocatable"] for c in cache.values()),
                   "n_unknown_type_total": sum(c["n_unknown_type"] for c in cache.values())},
               "methods": summarize(rows)}
    paired = {}
    for ds, _ in DATASETS:
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
                                        {i: b[i]["U_local"] for i in ids}),
            }
    summary["paired"] = paired
    summary["errors"] = errors
    (OUT / "neural_extractor_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2))
    for k, v in summary["methods"].items():
        if k.endswith("_covgate"):
            continue
        tr = v["task_recall"]["estimate"] if v["task_recall"] else None
        print(f"{k}: recall={v['recall']['estimate']:.3f} "
              f"task_recall={tr if tr is None else round(tr, 3)} "
              f"release={v['release_rate']:.3f} FR={v['FalseRelease_gold']} "
              f"FB_harmful={v['utility_fallback_harmful_fraction']:.3f}")
    print("extraction stats:", summary["extraction_stats"], "errors:", len(errors))
    print("wrote", OUT / "neural_extractor_summary.json")


if __name__ == "__main__":
    main()