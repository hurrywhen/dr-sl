import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

OUT = Path(__file__).resolve().parent.parent / "results" / "pilot_20260829"


def load_jsonl(p):
    return [json.loads(l) for l in open(p)] if Path(p).exists() else []


def fig_attacker_curve():
    att = {}
    for f in ("p2_leakage.jsonl", "p2_local.jsonl", "p2_strong.jsonl"):
        for r in load_jsonl(OUT / f):
            if r.get("L") is not None:
                att[(r.get("role"), r["level"])] = att.get((r.get("role"), r["level"]), []) + [r["L"]]
    names = {
        ("online_fast", "A_0"): "A0 qwen3.8-flash",
        ("online_fast", "A_1"): "A1 flash+prior",
        ("online_alt", "A_0"): "A0 glm-5.2",
        ("online_strong", "A_0"): "A0 qwen3.8-max",
        ("local_ornith", "A_0"): "A0 ornith(local)",
        ("local_ornith", "A_1"): "A1 ornith(local)",
    }
    order = [("local_ornith", "A_0"), ("local_ornith", "A_1"), ("online_fast", "A_0"),
             ("online_fast", "A_1"), ("online_alt", "A_0"), ("online_strong", "A_0")]
    ks = json.load(open(Path(__file__).resolve().parent.parent / "results" / "kanonymity" / "summary.json"))
    a3 = ks["runs"]["skewed@100000"]["p_k_lt_kstar"] * ks["runs"]["skewed@100000"]["n_instances_with_qi"] / ks["runs"]["skewed@100000"]["n_instances_total"]

    fig, ax = plt.subplots(figsize=(9, 4.6))
    labels = [names.get(k, str(k)) for k in order] + ["A3 k-anon(all)"]
    vals = [float(np.mean(att[k])) for k in order] + [a3]
    colors = ["#4c78a8", "#4c78a8", "#f58518", "#f58518", "#e45756", "#b279a2", "#9d755d"]
    bars = ax.bar(range(len(vals)), vals, color=colors)
    ax.set_xticks(range(len(vals)))
    ax.set_xticklabels(labels, rotation=18, ha="right", fontsize=9)
    ax.set_ylabel("leakage hit rate")
    ax.set_ylim(0, 1)
    ax.set_title("Graded attacker curve on direct-forwarded text (test, n=160; strict grading)")
    for b, v in zip(bars, vals):
        ax.text(b.get_x() + b.get_width() / 2, v + 0.01, f"{v:.2f}", ha="center", fontsize=8)
    fig.tight_layout()
    fig.savefig(OUT / "fig_attacker_curve.png", dpi=150)
    print("saved fig_attacker_curve.png")


def fig_train_loop():
    rows = [r for r in load_jsonl(OUT / "p7_train_loop.jsonl") if r.get("status") in ("PASS", "INFEASIBLE")]
    rows.sort(key=lambda r: r["idx"])
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.2))
    ax = axes[0]
    ax.scatter([r["idx"] for r in rows], [r["rounds"] for r in rows],
               c=["#2ca02c" if r["status"] == "PASS" else "#d62728" for r in rows], s=12, alpha=0.7)
    win = 20
    ma = np.convolve([r["rounds"] for r in rows], np.ones(win) / win, mode="valid")
    ax.plot(np.arange(win - 1, len(rows)), ma, color="black", lw=1.5, label=f"MA{win}")
    ax.set_xlabel("instance index (train stream)")
    ax.set_ylabel("loop rounds")
    ax.set_title("H1 check: rounds over accumulated stream")
    ax.legend(fontsize=8)
    ax = axes[1]
    lb = [r["L_before"] for r in rows]
    la = [r["L_after"] for r in rows]
    ax.scatter(lb, la, s=12, alpha=0.6,
               c=["#2ca02c" if r["status"] == "PASS" else "#d62728" for r in rows])
    ax.plot([0, 1], [0, 1], "k--", lw=1)
    ax.set_xlabel("L before (direct forward)")
    ax.set_ylabel("L after (DR-SL)")
    ax.set_title("Leakage reduction per instance")
    fig.tight_layout()
    fig.savefig(OUT / "fig_train_loop.png", dpi=150)
    print("saved fig_train_loop.png")


if __name__ == "__main__":
    fig_attacker_curve()
    fig_train_loop()
