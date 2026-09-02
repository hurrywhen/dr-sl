import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))

from protocol import PRIMARY_DIMS, EXTENDED_DIMS, POP_SIZE, POP_SEED, K_STAR
from qi import load_dataset, extract_qi
from synthpop import build_w1, query_k, run_k_experiment, marginal_check

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "dataset" / "output" / "dr_sl_dataset_v2.jsonl"
OUT = ROOT / "results" / "kanonymity"
SCALES = (10_000, 100_000, 1_000_000)
PROFILES = ("uniform", "skewed")


def validate_query_mechanism(seed=7):
    small = build_w1(n=20000, seed=seed)
    rng = np.random.default_rng(seed)
    ok = True
    for _ in range(50):
        qi = tuple(int(rng.integers(-1, 4)) for _ in PRIMARY_DIMS)
        expected = 0
        for j in range(small["n"]):
            match = True
            for d, v in zip(PRIMARY_DIMS, qi):
                if v < 0:
                    continue
                if int(small[d][j]) != v:
                    match = False
                    break
            if match:
                expected += 1
        got = query_k(small, qi, PRIMARY_DIMS)
        if got != expected:
            ok = False
            print("MISMATCH", qi, got, expected)
            break
    print("validate_query_mechanism:", "OK" if ok else "FAIL")
    return ok


def summarize(results, label):
    ks = [r["k"] for r in results if r["k"] is not None]
    arr = np.asarray(ks)
    by_domain = {}
    for r in results:
        if r["k"] is None:
            continue
        by_domain.setdefault(r["domain"], []).append(r["k"])
    summary = {
        "label": label,
        "n_instances_total": len(results),
        "n_instances_with_qi": len(ks),
        "median_k": float(np.median(arr)) if len(ks) else None,
        "p_k_lt_kstar": float((arr < K_STAR).mean()) if len(ks) else None,
        "p_k_eq_0": float((arr == 0).mean()) if len(ks) else None,
        "p_k_eq_1": float((arr == 1).mean()) if len(ks) else None,
        "p_lowk_nonzero": float(((arr >= 1) & (arr < K_STAR)).mean()) if len(ks) else None,
        "p_k_ge_11": float((arr >= 11).mean()) if len(ks) else None,
        "per_domain": {
            d: {
                "n": len(v),
                "median_k": float(np.median(v)),
                "p_k_lt_kstar": float((np.asarray(v) < K_STAR).mean()),
                "p_k_eq_1": float((np.asarray(v) == 1).mean()),
            }
            for d, v in sorted(by_domain.items())
        },
        "k_star": K_STAR,
    }
    return summary


def plot_grid(grid, path):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.2), sharey=True)
    for profile, ax in zip(PROFILES, axes):
        for stat, style in (("p_k_lt_kstar", "o-"), ("p_k_eq_1", "s--"), ("p_k_eq_0", "^:")):
            ys = [grid[(profile, n)][stat] for n in SCALES]
            ax.plot(SCALES, ys, style, label=stat)
        ax.set_xscale("log")
        ax.set_xlabel("reference population size N")
        ax.set_title(f"W1 {profile}")
        ax.grid(alpha=0.3)
    axes[0].set_ylabel("fraction of instances")
    axes[0].legend()
    fig.suptitle("A3 quasi-identifier risk vs reference population (k* = %d, primary dims)" % K_STAR)
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)
    print("figure saved:", path)


def plot_k_distribution(results, path, title):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    ks = [max(1, r["k"]) for r in results if r["k"] is not None]
    domains = sorted({r["domain"] for r in results if r["k"] is not None})
    fig, ax = plt.subplots(figsize=(8, 4.5))
    bins = np.logspace(0, np.log10(max(ks) + 1), 40)
    for dom in domains:
        kd = [max(1, r["k"]) for r in results if r["k"] is not None and r["domain"] == dom]
        ax.hist(kd, bins=bins, alpha=0.55, label=dom)
    ax.axvline(K_STAR, color="red", linestyle="--", label=f"k*={K_STAR}")
    ax.set_xscale("log")
    ax.set_xlabel("k (matching records in synthetic population)")
    ax.set_ylabel("instances")
    ax.set_title(title)
    ax.legend()
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)
    print("figure saved:", path)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    validate_query_mechanism()

    grid = {}
    report = {"k_star": K_STAR, "dims": list(PRIMARY_DIMS),
              "note": "QI tuples extracted from gold annotations (oracle extractor). "
                      "Two hit conventions reported: p_k_lt_kstar = conservative, "
                      "subject-included (k_tilde = k+1 <= k*, i.e. k <= 4, counting k=0 "
                      "out-of-support tuples as unique); p_lowk_nonzero = strict DB-count "
                      "only (1 <= k < k*). k=0 means the tuple is absent from the reference "
                      "population (reported separately as p_k_eq_0).",
              "runs": {}}
    for profile in PROFILES:
        for n in SCALES:
            pop = build_w1(n=n, seed=POP_SEED, profile=profile)
            _, results = run_k_experiment(str(DATA), splits=("test", "adversarial"),
                                          dims=PRIMARY_DIMS, pop=pop)
            label = f"{profile}@{n}"
            summary = summarize(results, label)
            grid[(profile, n)] = summary
            report["runs"][label] = summary
            if label == f"skewed@{SCALES[1]}":
                with open(OUT / "k_results_main.json", "w") as f:
                    json.dump(results, f, ensure_ascii=False, indent=1)
                plot_k_distribution(results, OUT / "k_distribution_main.png",
                                    "A3 k distribution (W1 skewed, N=1e5)")
            print(f"{label:>16}: median_k={summary['median_k']:.0f}  "
                  f"P(k<{K_STAR})={summary['p_k_lt_kstar']:.3f}  "
                  f"P(k=1)={summary['p_k_eq_1']:.3f}  P(k=0)={summary['p_k_eq_0']:.3f}  "
                  f"n_qi={summary['n_instances_with_qi']}")

    plot_grid(grid, OUT / "k_vs_population.png")

    pop_full = build_w1(n=POP_SIZE, seed=POP_SEED, profile="uniform")
    mc = marginal_check(pop_full, ["city", "gender"], {
        "city": {"probs": [1 / 8] * 8},
        "gender": {"probs": [0.5, 0.5]},
    })
    report["marginal_check_uniform_1e6"] = mc

    _, results_ext = run_k_experiment(str(DATA), splits=("test", "adversarial"),
                                      dims=EXTENDED_DIMS, pop=pop_full)
    report["runs"]["extended@uniform@1000000"] = summarize(results_ext, "extended@uniform@1000000")

    with open(OUT / "summary.json", "w") as f:
        json.dump(report, f, ensure_ascii=False, indent=1)
    print("\nsummary saved:", OUT / "summary.json")


if __name__ == "__main__":
    main()
