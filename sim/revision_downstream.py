#!/usr/bin/env python3
"""Downstream task utility (round 2, protocol v2 §5).

For the frozen holdout-1 audit subset and methods closed_loop / generalization_only:
a strong cloud model answers the embedded task from X (reference, once per
instance) and from each de-identified artifact D; an independent alt model judges
each D-answer against the X-reference on a 0/0.5/1 correctness/usefulness scale.

This is a task-level utility measure, distinct from the artifact-level semantic
judge.  The judge is an external reference with measurement error: it is not
ground-truth task success, not a local release input, and not a human-acceptability
gold standard.  All material is synthetic; this is controlled disclosure.
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
from qi import load_dataset
from revision_stats import cluster_bootstrap

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "results" / os.environ.get("REVISION_OUT", "revision_20261121")
METHODS = ("closed_loop", "generalization_only")
MAX_WORKERS = int(os.environ.get("REVISION_AUDIT_WORKERS", "4"))

ANSWER_SYSTEM = ("你是专业助手。请仅根据给定材料，回应材料中提出的请求或问题。"
                 "给出具体、可操作的回答；材料中缺失的信息不臆造。")
JUDGE_SYSTEM = ("你是效用评审。给定同一任务的参考答案（基于完整原始材料）和候选答案（基于脱敏材料），"
                "判断候选答案相对参考答案在正确性与可用性上的保持程度。评分：1=基本保持，0.5=部分退化，0=不可用或错误。"
                '只输出 JSON：{"score": 0/0.5/1}。')


def extract_task(prompt):
    p = re.sub(r"补充说明：.*$", "", prompt, flags=re.S).strip()
    sentences = [s.strip() for s in re.split(r"(?<=[。？])", p) if s.strip()]
    return sentences[-1] if sentences else p


def parse_score(raw):
    s = str(raw).strip()
    s = re.sub(r"^```(?:json)?\s*", "", s)
    s = re.sub(r"\s*```$", "", s)
    a, b = s.find("{"), s.rfind("}")
    if a >= 0 and b > a:
        try:
            v = float(json.loads(s[a:b + 1]).get("score"))
            if v in (0.0, 0.5, 1.0):
                return v
        except Exception:
            pass
    m = re.search(r'"?score"?\s*[:：]\s*(1\.0|1|0\.5|0\.0|0)(?!\d)', s)
    return float(m.group(1)) if m else None


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    offline = [json.loads(l) for l in (OUT / "offline_runtime.jsonl").open(encoding="utf-8")]
    items = {r["id"]: r for r in load_dataset(str(ROOT / "dataset/output/dr_sl_holdout_v1.jsonl"))}
    off = {(r["id"], r["method"]): r for r in offline
           if r["dataset"] == "holdout80" and r["sensitive_set"] == "runtime"}
    subset = json.loads((OUT / "audit_subset.json").read_text())

    answer_backend = make_backend("online_strong", timeout=120, retries=1)
    judge_backend = make_backend("online_alt", timeout=120, retries=1)

    # Stage 1: reference answers from X (once per instance) + candidate answers from D.
    ans_tasks = []
    for iid in subset:
        X = items[iid]["prompt"]
        task = extract_task(X)
        ans_tasks.append(("ref", iid, None, X, task))
        for m in METHODS:
            ans_tasks.append(("cand", iid, m, off[(iid, m)]["D"], task))

    answers = {}
    errors = []

    def gen(t):
        kind, iid, m, material, task = t
        user = f"材料：\n{material}\n\n请回应材料中的请求：{task}"
        try:
            raw = answer_backend.complete(ANSWER_SYSTEM, user)
            return {"kind": kind, "id": iid, "method": m, "task": task, "answer": raw}
        except Exception as e:
            return {"kind": kind, "id": iid, "method": m, "error": str(e)[:300]}

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as ex:
        futs = [ex.submit(gen, t) for t in ans_tasks]
        for i, fut in enumerate(as_completed(futs), 1):
            r = fut.result()
            if r.get("error"):
                errors.append(r)
            else:
                answers[(r["kind"], r["id"], r["method"])] = r["answer"]
            if i % 40 == 0:
                print(f"answer progress {i}/{len(ans_tasks)} errors={len(errors)}", flush=True)

    # Stage 2: judge each candidate answer against the reference.
    judge_tasks = []
    for iid in subset:
        ref = answers.get(("ref", iid, None))
        task = extract_task(items[iid]["prompt"])
        if ref is None:
            continue
        for m in METHODS:
            cand = answers.get(("cand", iid, m))
            if cand is not None:
                judge_tasks.append((iid, m, task, ref, cand))

    judged = []

    def judge(t):
        iid, m, task, ref, cand = t
        user = f"任务：{task}\n\n参考答案：\n{ref}\n\n候选答案：\n{cand}"
        try:
            raw = judge_backend.complete(JUDGE_SYSTEM, user)
            return {"id": iid, "method": m, "score": parse_score(raw), "raw": raw,
                    "reference": ref, "candidate": cand}
        except Exception as e:
            return {"id": iid, "method": m, "error": str(e)[:300]}

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as ex:
        futs = [ex.submit(judge, t) for t in judge_tasks]
        for i, fut in enumerate(as_completed(futs), 1):
            r = fut.result()
            judged.append(r)
            if r.get("error"):
                errors.append(r)
            if i % 40 == 0:
                print(f"judge progress {i}/{len(judge_tasks)} errors={len(errors)}", flush=True)

    with (OUT / "downstream_raw.jsonl").open("w", encoding="utf-8") as f:
        for r in judged:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    local = {(r["id"], r["method"]): r for r in offline
             if r["dataset"] == "holdout80" and r["sensitive_set"] == "runtime"}
    summary = {"n_instances": len(subset), "n_errors": len(errors), "by_method": {}}
    for m in METHODS:
        rows = [r for r in judged if r["method"] == m and r.get("score") is not None]
        byid = {r["id"]: r["score"] for r in rows}
        pass_ids = [i for i in byid if local.get((i, m), {}).get("release")]
        inf_ids = [i for i in byid if not local.get((i, m), {}).get("release")]
        summary["by_method"][m] = {
            "ALL": cluster_bootstrap(byid),
            "PASS": cluster_bootstrap({i: byid[i] for i in pass_ids}),
            "INFEASIBLE": cluster_bootstrap({i: byid[i] for i in inf_ids}),
            "n": len(rows),
        }
    summary["errors"] = errors
    (OUT / "downstream_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2))
    print(json.dumps({k: v for k, v in summary.items() if k != "errors"}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
