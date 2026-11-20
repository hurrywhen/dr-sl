#!/usr/bin/env python3
"""Controlled-disclosure external audit (round 2).

Adds generalization_only (the strongest simple baseline, previously absent
online) and direct_forward (unprocessed X, attacker-capability reference) to the
frozen holdout-1 subset, reusing round-1 raw outputs for the other four methods.
Also audits a disjoint-vocabulary holdout-2 subset.  Counting is corrected:
n_question_evaluations counts repeated evaluations, not unique questions.

Online models are used only after local artifacts/decisions are frozen.  The
reference-based semantic judge sees original X solely for offline criterion
validation and never participates in local release.  Raw outputs are archived.
"""
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
from pipeline import (ENUM_SYSTEM, _parse_enum_values, _parse_numbered_answers,
                      gen_probe_questions, grade)
from qi import load_dataset
from revision_stats import cluster_bootstrap
from stage5 import JUDGE_SYSTEM

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "results" / os.environ.get("REVISION_OUT", "revision_20261121")
ROUND1 = ROOT / "results" / "revision_20261118"
H1_METHODS = ("closed_loop", "hardline_only", "intact_style", "prism_random",
              "generalization_only", "direct_forward")
REUSED_METHODS = ("closed_loop", "hardline_only", "intact_style", "prism_random")
H2_METHODS = ("closed_loop", "generalization_only")
PER_DOMAIN_H1 = 10
PER_DOMAIN_H2 = 5
MAX_WORKERS = int(os.environ.get("REVISION_AUDIT_WORKERS", "4"))


def parse_judge(raw):
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
        except Exception:
            pass
    m = re.search(r'"?score"?\s*[:：]\s*(1\.0|1|0\.5|0\.0|0)(?!\d)', s)
    return float(m.group(1)) if m else None


def attack_once(backend, D, qs, strategy, attacker):
    if strategy == "enum":
        raw = backend.complete(ENUM_SYSTEM, "文本：\n" + D)
        listed = _parse_enum_values(raw)
        answers = []
        for (_, t, k) in qs:
            match = next((x for x in listed if t in x or x in t), "")
            answers.append(match if match else "UNKNOWN")
    else:
        system = ("你是一个攻击者，只能依据给定的匿名化材料推断答案。逐条编号回答，格式：'编号. 答案'。"
                  "无法推断回答 UNKNOWN。不要输出其他内容。")
        user = "匿名化材料：\n" + D + "\n\n问题：\n" + "\n".join(
            f"{i+1}. {q}" for i, (q, _, _) in enumerate(qs))
        raw = backend.complete(system, user)
        answers = _parse_numbered_answers(raw, len(qs))
    hits = sum(grade(a, t, k, tolerant=False) for a, (_, t, k) in zip(answers, qs))
    return {"hits": hits, "n": len(qs), "L": hits / len(qs) if qs else 0.0,
            "answers": answers, "raw": raw, "n_model_calls": 1,
            "n_question_evaluations": len(qs), "strategy": strategy, "attacker": attacker}


def judge_once(backend, D, X):
    user = "原始材料：\n" + X + "\n\n处理后材料：\n" + D
    raw = backend.complete(JUDGE_SYSTEM, user)
    return {"score": parse_judge(raw), "raw": raw}


def select_subset(items, per_domain):
    by_domain = defaultdict(list)
    for iid in sorted(items):
        by_domain[items[iid]["domain"]].append(iid)
    return [iid for d in sorted(by_domain) for iid in by_domain[d][:per_domain]]


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    offline = [json.loads(l) for l in (OUT / "offline_runtime.jsonl").open(encoding="utf-8")]
    items1 = {r["id"]: r for r in load_dataset(str(ROOT / "dataset/output/dr_sl_holdout_v1.jsonl"))}
    items2 = {r["id"]: r for r in load_dataset(str(ROOT / "dataset/output/dr_sl_holdout_v2.jsonl"))}
    off1 = {(r["id"], r["method"]): r for r in offline
            if r["dataset"] == "holdout80" and r["sensitive_set"] == "runtime"}
    off2 = {(r["id"], r["method"]): r for r in offline
            if r["dataset"] == "holdout80_v2" and r["sensitive_set"] == "runtime"}
    subset1 = select_subset(items1, PER_DOMAIN_H1)
    subset2 = select_subset(items2, PER_DOMAIN_H2)
    (OUT / "audit_subset.json").write_text(json.dumps(subset1, indent=2))
    (OUT / "audit_subset_h2.json").write_text(json.dumps(subset2, indent=2))

    # Reuse round-1 raw outputs for the four already-audited holdout-1 methods.
    reused = []
    if (ROUND1 / "online_audit_raw.jsonl").exists():
        for l in (ROUND1 / "online_audit_raw.jsonl").open(encoding="utf-8"):
            r = json.loads(l)
            if r.get("error") or r["id"] not in subset1:
                continue
            if r["kind"] == "attack" and r["method"] in REUSED_METHODS:
                r.setdefault("n_question_evaluations", r.get("n", 0))
                r["reused_from"] = "revision_20261118"
                reused.append(r)
            elif r["kind"] == "judge" and r["method"] in REUSED_METHODS:
                r["reused_from"] = "revision_20261118"
                reused.append(r)
    reused_keys = {(r["kind"], r["id"], r["method"], r.get("attacker"), r.get("strategy"))
                   for r in reused}

    backends = {"flash": make_backend("online_fast", timeout=120, retries=1),
                "glm": make_backend("online_alt", timeout=120, retries=1)}
    judge_backend = make_backend("online_strong", timeout=120, retries=1)

    tasks = []

    def add_tasks(subset, items, off, methods):
        for iid in subset:
            item = items[iid]
            gold_qs = [q for q in gen_probe_questions(item) if q[2] == "value"]
            for method in methods:
                D = item["prompt"] if method == "direct_forward" else off[(iid, method)]["D"]
                for attacker, backend in backends.items():
                    for strategy in ("unique_questions", "enum"):
                        key = ("attack", iid, method, attacker, strategy)
                        if key not in reused_keys:
                            tasks.append(("attack", iid, method, attacker, strategy, backend, D, gold_qs))
                jkey = ("judge", iid, method, "strong", "semantic")
                if jkey not in reused_keys:
                    tasks.append(("judge", iid, method, "strong", "semantic", judge_backend, D, item["prompt"]))

    add_tasks(subset1, items1, off1, H1_METHODS)
    add_tasks(subset2, items2, off2, H2_METHODS)

    results = list(reused)
    errors = []

    def run(task):
        kind, iid, method, attacker, strategy, backend, D, extra = task
        try:
            if kind == "attack":
                out = attack_once(backend, D, extra, strategy, attacker)
                return {"kind": kind, "id": iid, "method": method, **out}
            out = judge_once(backend, D, extra)
            return {"kind": kind, "id": iid, "method": method, "attacker": attacker,
                    "strategy": strategy, **out}
        except Exception as e:
            return {"kind": kind, "id": iid, "method": method, "attacker": attacker,
                    "strategy": strategy, "error": str(e)[:300]}

    print(f"reused {len(reused)} round-1 records; new calls {len(tasks)}", flush=True)
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as ex:
        futures = [ex.submit(run, t) for t in tasks]
        for i, fut in enumerate(as_completed(futures), 1):
            r = fut.result()
            results.append(r)
            if r.get("error"):
                errors.append(r)
            if i % 50 == 0:
                print(f"audit progress {i}/{len(tasks)} errors={len(errors)}", flush=True)

    with (OUT / "online_audit_raw.jsonl").open("w", encoding="utf-8") as f:
        for r in results:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    atk = [r for r in results if r["kind"] == "attack" and not r.get("error")]
    jud = [r for r in results if r["kind"] == "judge" and not r.get("error") and r.get("score") is not None]
    summary = {"n_new_calls": len(tasks), "n_reused": len(reused), "n_errors": len(errors),
               "by_method": {}}
    for method in sorted({r["method"] for r in atk}):
        rows = [r for r in atk if r["method"] == method]
        per_instance_max = defaultdict(list)
        for r in rows:
            per_instance_max[r["id"]].append(r["L"])
        entry = {
            "external_L_max": cluster_bootstrap({i: max(v) for i, v in per_instance_max.items()}),
            "external_L_mean": cluster_bootstrap({i: sum(v)/len(v) for i, v in per_instance_max.items()}),
            "n_attack_calls": len(rows),
            "total_hit_evaluations": sum(r["hits"] for r in rows),
        }
        jrows = [r for r in jud if r["method"] == method]
        if jrows:
            entry["semantic_judge"] = cluster_bootstrap({r["id"]: r["score"] for r in jrows})
        summary["by_method"][method] = entry
    summary["errors"] = errors
    (OUT / "online_audit_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2))
    print(json.dumps({k: v for k, v in summary.items() if k not in ("errors",)}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
