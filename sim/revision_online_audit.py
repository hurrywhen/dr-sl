#!/usr/bin/env python3
"""Controlled-disclosure external audit on the frozen holdout subset.

Online models are used only after local artifacts/decisions are frozen.  The
reference-based semantic judge sees original X solely for offline criterion
validation and never participates in local release.  Raw outputs are archived.
"""
import json
import os
import re
import sys
import time
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "dataset"))

from backends import make_backend
from pipeline import (ENUM_SYSTEM, _parse_enum_values, _parse_numbered_answers,
                      gen_probe_questions, grade)
from qi import load_dataset
from revision_stats import cluster_bootstrap, zero_observation_summary
from stage5 import JUDGE_SYSTEM

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "results" / os.environ.get("REVISION_OUT", "revision_20261118")
AUDIT_METHODS = ("closed_loop", "hardline_only", "intact_style", "prism_random")
PER_DOMAIN = 10
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
            "n_unique_questions": len(qs), "strategy": strategy, "attacker": attacker}


def judge_once(backend, D, X):
    user = "原始材料：\n" + X + "\n\n处理后材料：\n" + D
    raw = backend.complete(JUDGE_SYSTEM, user)
    return {"score": parse_judge(raw), "raw": raw}


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    offline_path = OUT / "offline_runtime.jsonl"
    if not offline_path.exists():
        raise SystemExit("run revision_experiment.py first")
    offline = [json.loads(l) for l in offline_path.open(encoding="utf-8")]
    hold = {r["id"]: r for r in offline if r["dataset"] == "holdout80" and r["sensitive_set"] == "runtime"}
    items = {r["id"]: r for r in load_dataset(str(ROOT / "dataset" / "output" / "dr_sl_holdout_v1.jsonl"))}
    by_domain = defaultdict(list)
    for iid in sorted(hold):
        by_domain[items[iid]["domain"]].append(iid)
    subset = [iid for d in sorted(by_domain) for iid in by_domain[d][:PER_DOMAIN]]
    (OUT / "audit_subset.json").write_text(json.dumps(subset, indent=2))

    backends = {"flash": make_backend("online_fast", timeout=120, retries=1),
                "glm": make_backend("online_alt", timeout=120, retries=1)}
    judge_backend = make_backend("online_strong", timeout=120, retries=1)

    tasks = []
    for iid in subset:
        item = items[iid]
        gold_qs = [q for q in gen_probe_questions(item) if q[2] == "value"]
        for method in AUDIT_METHODS:
            rec = hold[iid]
            # find matching method row
            row = next(r for r in offline if r["dataset"] == "holdout80" and r["sensitive_set"] == "runtime"
                       and r["id"] == iid and r["method"] == method)
            D = row["D"]
            for attacker, backend in backends.items():
                for strategy in ("unique_questions", "enum"):
                    tasks.append(("attack", iid, method, attacker, strategy, backend, D, gold_qs))
            tasks.append(("judge", iid, method, "strong", "semantic", judge_backend, D, item["prompt"]))

    results = []
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

    attacks = [r for r in results if r["kind"] == "attack" and not r.get("error")]
    judges = [r for r in results if r["kind"] == "judge" and not r.get("error") and r.get("score") is not None]
    summary = {"n_tasks": len(tasks), "n_errors": len(errors),
               "zero_observation": zero_observation_summary(attacks),
               "by_method": {}}
    for method in AUDIT_METHODS:
        rows = [r for r in attacks if r["method"] == method]
        per_instance_max = defaultdict(list)
        for r in rows:
            per_instance_max[r["id"]].append(r["L"])
        summary["by_method"][method] = {
            "external_L_max": cluster_bootstrap({i: max(v) for i, v in per_instance_max.items()}),
            "external_L_mean": cluster_bootstrap({i: sum(v)/len(v) for i, v in per_instance_max.items()}),
            "zero_observation": zero_observation_summary(rows),
        }
        jrows = [r for r in judges if r["method"] == method]
        if jrows:
            summary["by_method"][method]["semantic_judge"] = cluster_bootstrap({r["id"]: r["score"] for r in jrows})
    # local vs judge threshold agreement
    local_rows = { (r["id"], r["method"]): r for r in offline if r["dataset"]=="holdout80" and r["sensitive_set"]=="runtime" }
    confusion = defaultdict(int)
    pairs = []
    for r in judges:
        lr = local_rows.get((r["id"], r["method"]))
        if not lr:
            continue
        local_rel = bool(lr["release"])
        judge_rel = r["score"] >= 0.5
        confusion[(local_rel, judge_rel)] += 1
        pairs.append({"id": r["id"], "method": r["method"], "local_U": lr["U_local"],
                      "judge_U": r["score"], "local_release": local_rel, "judge_release": judge_rel})
    summary["threshold_confusion"] = {f"local_{a}_judge_{b}": n for (a, b), n in confusion.items()}
    summary["judge_pairs"] = pairs
    summary["errors"] = errors
    (OUT / "online_audit_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2))
    print(json.dumps({k: v for k, v in summary.items() if k != "judge_pairs"}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
