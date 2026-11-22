#!/usr/bin/env python3
"""Downstream reference-answer preservation (round 3, protocol v3 §2).

Replaces the INVALID round-2 downstream experiment, whose last-sentence task
heuristic returned (nearly) the full original prompt for 20/80 field-list
instances, re-exposing sensitive X to the candidate answer model.

Round-3 design:
- Explicit `task` field from the dataset generator; runtime assertions that the
  task contains no gold sensitive value and is not the full prompt.
- Answers cached by artifact SHA-256: identical artifacts reuse one answer.
- A fixed paired seed is submitted to the answer backend (provider honoring is
  not guaranteed; disclosed as a limitation).
- Two independent judge models score every candidate (multi-judge agreement).
- Raw logs archive task, artifact/material hashes, model names, seed, raw
  responses, reference and candidate answers.

The metric is REFERENCE-ANSWER PRESERVATION: agreement with the answer obtained
from full X.  It is not absolute task correctness (a wrong reference can be
preserved); absolute quality needs expert rubrics / human scoring (future work).
Judges are external references with measurement error, never local release
inputs.  All material is synthetic; this is controlled disclosure.
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
from revision_stats import cluster_bootstrap, paired_delta

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "results" / "revision_round3"
METHODS = ("closed_loop", "generalization_only")
MAX_WORKERS = int(os.environ.get("REVISION_AUDIT_WORKERS", "4"))
ANSWER_SEED = 20261121
ANSWER_MODEL_ROLE = "online_strong"
JUDGE_ROLES = ("online_alt", "online_fast")  # primary (headline), robustness; protocol v4 §2

ANSWER_SYSTEM = ("你是专业助手。请仅根据给定材料，回应材料中提出的请求或问题。"
                 "给出具体、可操作的回答；材料中缺失的信息不臆造。")
JUDGE_SYSTEM = ("你是效用评审。给定同一任务的参考答案（基于完整原始材料）和候选答案（基于脱敏材料），"
                "判断候选答案相对参考答案在正确性与可用性上的保持程度。评分：1=基本保持，0.5=部分退化，0=不可用或错误。"
                '只输出 JSON：{"score": 0/0.5/1}。')


def sha(s):
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def parse_score(raw):
    import re
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


def assert_task_isolation(item):
    task = item["task"]
    assert task and task != item["prompt"], f"task equals prompt: {item['id']}"
    gold = (item["annotations"]["explicit_identifiers"]
            + item["annotations"]["quasi_identifiers"])
    for e in gold:
        assert e["value"] not in task, f"task leaks gold value: {item['id']}"


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    r2 = ROOT / "results" / "revision_20261121"
    offline = [json.loads(l) for l in (r2 / "offline_runtime.jsonl").open(encoding="utf-8")]
    items = {r["id"]: r for r in load_dataset(str(ROOT / "dataset/output/dr_sl_holdout_v1.jsonl"))}
    off = {(r["id"], r["method"]): r for r in offline
           if r["dataset"] == "holdout80" and r["sensitive_set"] == "runtime"}
    subset = json.loads((r2 / "audit_subset.json").read_text())
    for iid in subset:
        assert_task_isolation(items[iid])

    answer_backend = make_backend(ANSWER_MODEL_ROLE, timeout=120, retries=1, seed=ANSWER_SEED)
    answer_model = answer_backend.config.model
    judges = {role: make_backend(role, timeout=120, retries=1) for role in JUDGE_ROLES}

    # Stage 1: answers.  Cache by (material hash, task): identical artifacts
    # share one answer, removing unnecessary paired sampling noise.
    jobs = {}   # cache key -> (kind, iid, method, material, task)
    for iid in subset:
        X = items[iid]["prompt"]
        task = items[iid]["task"]
        jobs[("ref", sha(X), task)] = ("ref", iid, None, X, task)
        for m in METHODS:
            D = off[(iid, m)]["D"]
            jobs.setdefault(("cand", sha(D), task), ("cand", iid, m, D, task))

    answers = {}   # cache key -> raw answer
    ans_records, errors = [], []
    # Resume support: reuse archived answers/judgments so a transient network
    # failure does not force a full rerun (records are append-only audited).
    ans_path = OUT / "downstream_answers.jsonl"
    if ans_path.exists():
        for l in ans_path.open(encoding="utf-8"):
            r = json.loads(l)
            k = tuple(r["key"])
            if k in jobs and "answer" in r:
                answers[k] = r["answer"]
                ans_records.append(r)
    todo = [(k, v) for k, v in jobs.items() if k not in answers]

    def gen(job):
        key, (kind, iid, m, material, task) = job
        user = f"材料：\n{material}\n\n请回应材料中的请求：{task}"
        try:
            raw = answer_backend.complete(ANSWER_SYSTEM, user)
            return {"key": key, "kind": kind, "id": iid, "method": m, "task": task,
                    "material_sha256": sha(material), "answer_model": answer_model,
                    "answer_seed_submitted": ANSWER_SEED, "answer": raw}
        except Exception as e:
            return {"key": key, "kind": kind, "id": iid, "method": m, "error": str(e)[:300]}

    print(f"answer calls: {len(todo)} new ({len(answers)} resumed); reference {len(subset)} "
          f"+ unique candidates {len(jobs) - len(subset)}; paired seed {ANSWER_SEED} submitted", flush=True)
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as ex:
        futs = [ex.submit(gen, j) for j in todo]
        for i, fut in enumerate(as_completed(futs), 1):
            r = fut.result()
            if r.get("error"):
                errors.append(r)
            else:
                answers[r["key"]] = r["answer"]
                ans_records.append(r)
            if i % 30 == 0:
                print(f"answer progress {i}/{len(todo)} errors={len(errors)}", flush=True)
    with (OUT / "downstream_answers.jsonl").open("w", encoding="utf-8") as f:
        for r in ans_records:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    # Stage 2: two independent judges per candidate.
    judge_tasks = []
    for iid in subset:
        X = items[iid]["prompt"]
        task = items[iid]["task"]
        ref = answers.get(("ref", sha(X), task))
        if ref is None:
            continue
        for m in METHODS:
            D = off[(iid, m)]["D"]
            cand = answers.get(("cand", sha(D), task))
            if cand is not None:
                judge_tasks.append((iid, m, task, D, ref, cand))

    judged, jerrors = [], []
    raw_path = OUT / "downstream_raw.jsonl"
    done = set()
    if raw_path.exists():
        for l in raw_path.open(encoding="utf-8"):
            r = json.loads(l)
            if all(r.get(f"judge_{role}", {}).get("score") is not None for role in JUDGE_ROLES):
                judged.append(r)
                done.add((r["id"], r["method"]))
    judge_tasks = [t for t in judge_tasks if (t[0], t[1]) not in done]

    def judge(t):
        iid, m, task, D, ref, cand = t
        user = f"任务：{task}\n\n参考答案：\n{ref}\n\n候选答案：\n{cand}"
        out = {"id": iid, "method": m, "task": task, "artifact_sha256": sha(D),
               "reference": ref, "candidate": cand,
               "answer_model": answer_model, "answer_seed_submitted": ANSWER_SEED}
        try:
            for role in JUDGE_ROLES:
                raw = judges[role].complete(JUDGE_SYSTEM, user)
                out[f"judge_{role}"] = {"model": judges[role].config.model,
                                        "score": parse_score(raw), "raw": raw}
            return out
        except Exception as e:
            out["error"] = str(e)[:300]
            return out

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as ex:
        futs = [ex.submit(judge, t) for t in judge_tasks]
        for i, fut in enumerate(as_completed(futs), 1):
            r = fut.result()
            (jerrors if r.get("error") else judged).append(r)
            if i % 40 == 0:
                print(f"judge progress {i}/{len(judge_tasks)} errors={len(jerrors)}", flush=True)

    with (OUT / "downstream_raw.jsonl").open("w", encoding="utf-8") as f:
        for r in judged:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    # Summary.  Protocol v4 §2: primary judge online_alt (pre-specified in the
    # round-3 JUDGE_ROLES order), robustness judge online_fast; BOTH are reported
    # in full (per-method strata, paired CL−GEN delta + CI, disagreement counts).
    local = {(r["id"], r["method"]): r for r in offline
             if r["dataset"] == "holdout80" and r["sensitive_set"] == "runtime"}
    prim, sec = JUDGE_ROLES

    def scores(role):
        return {(r["id"], r["method"]): r[f"judge_{role}"]["score"] for r in judged
                if r.get(f"judge_{role}", {}).get("score") is not None}

    def judge_block(sc):
        block = {"by_method": {}, "n_instances_score_disagreement": None,
                 "paired_closed_minus_generalization": None}
        for m in METHODS:
            byid = {i: sc[(i, m)] for i in subset if (i, m) in sc}
            pass_ids = [i for i in byid if local.get((i, m), {}).get("release")]
            inf_ids = [i for i in byid if not local.get((i, m), {}).get("release")]
            block["by_method"][m] = {
                "ALL": cluster_bootstrap(byid),
                "PASS": cluster_bootstrap({i: byid[i] for i in pass_ids}),
                "INFEASIBLE": cluster_bootstrap({i: byid[i] for i in inf_ids}),
                "n": len(byid),
            }
        ids = [i for i in subset if (i, "closed_loop") in sc and (i, "generalization_only") in sc]
        left = {i: sc[(i, "closed_loop")] for i in ids}    # CL
        right = {i: sc[(i, "generalization_only")] for i in ids}  # GEN
        block["paired_closed_minus_generalization"] = paired_delta(left, right)
        block["n_instances_score_disagreement"] = sum(1 for i in ids if left[i] != right[i])
        block["n_paired_instances"] = len(ids)
        return block

    sp, ss = scores(prim), scores(sec)
    summary = {"metric": "reference_answer_preservation",
               "note": "agreement with the answer from full X; NOT absolute task correctness",
               "n_instances": len(subset), "n_answer_calls": len(jobs),
               "n_judge_calls": (len(done) + len(judge_tasks)) * len(JUDGE_ROLES),
               "answer_model": answer_model, "answer_seed_submitted": ANSWER_SEED,
               "judge_models": {role: judges[role].config.model for role in JUDGE_ROLES},
               "judge_roles": {"primary": prim, "robustness": sec},
               "n_errors": len(errors) + len(jerrors),
               "by_judge": {prim: judge_block(sp), sec: judge_block(ss)}}
    # Top-level by_method / paired fields mirror the PRIMARY judge (compatibility).
    summary["by_method"] = summary["by_judge"][prim]["by_method"]
    summary["paired_closed_minus_generalization"] = \
        summary["by_judge"][prim]["paired_closed_minus_generalization"]
    summary["n_instances_score_disagreement"] = \
        summary["by_judge"][prim]["n_instances_score_disagreement"]
    # Multi-judge agreement (all candidate scores).
    both = [(sp[k], ss[k]) for k in sp if k in ss]
    summary["judge_agreement"] = {
        "n": len(both),
        "exact_agreement": sum(1 for a, b in both if a == b) / len(both) if both else None,
        "mae": sum(abs(a - b) for a, b in both) / len(both) if both else None,
    }
    summary["n_identical_artifacts"] = sum(
        1 for i in subset if off[(i, "closed_loop")]["D"] == off[(i, "generalization_only")]["D"])
    summary["errors"] = errors + jerrors
    (OUT / "downstream_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2))
    print(json.dumps({k: v for k, v in summary.items() if k != "errors"}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
