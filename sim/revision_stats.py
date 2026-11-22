"""Instance-cluster statistics for the revised evaluation.

Repeated probes, attackers and formats are nested within an instance.  These
helpers resample instances, never individual probe rows.
"""
import math
from collections import defaultdict

import numpy as np

Z95 = 1.959963984540054


def wilson_interval(hits, n, z=Z95):
    if n == 0:
        return 0.0, 1.0
    p = hits / n
    denom = 1 + z * z / n
    center = (p + z * z / (2 * n)) / denom
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / denom
    return max(0.0, center - half), min(1.0, center + half)


def cluster_bootstrap(values_by_id, n_boot=2000, seed=20261118, statistic="mean"):
    """Percentile bootstrap over instance clusters.

    values_by_id maps instance id -> scalar or sequence of nested observations.
    For sequences, the within-instance mean is computed first, then instances
    are resampled.  Returns point estimate and 95% percentile interval.
    """
    ids = sorted(values_by_id)
    if not ids:
        return None
    per_instance = []
    for i in ids:
        v = values_by_id[i]
        if isinstance(v, (list, tuple, np.ndarray)):
            arr = np.asarray(v, dtype=float)
            per_instance.append(float(arr.mean()) if arr.size else np.nan)
        else:
            per_instance.append(float(v))
    arr = np.asarray(per_instance, dtype=float)
    arr = arr[~np.isnan(arr)]
    if arr.size == 0:
        return None
    point = float(arr.mean())
    if arr.size == 1:
        return {"estimate": point, "ci95": [point, point], "n_instances": 1,
                "n_boot": n_boot, "unit": "instance_cluster"}
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, arr.size, size=(n_boot, arr.size))
    boots = arr[idx].mean(axis=1)
    lo, hi = np.quantile(boots, [0.025, 0.975])
    return {"estimate": point, "ci95": [float(lo), float(hi)],
            "n_instances": int(arr.size), "n_boot": n_boot,
            "unit": "instance_cluster"}


def paired_delta(left_by_id, right_by_id, n_boot=2000, seed=20261118):
    """Instance-cluster paired difference **left − right** (direction explicit).

    Round-4 correction: the former ``paired_cluster_delta(a, b)`` computed b−a,
    which two call sites mislabelled as CL−GEN (protocol v4 §1).  The estimate
    must equal mean(left) − mean(right) on the common instances; this identity
    is asserted here and at every call site.
    """
    common = sorted(set(left_by_id) & set(right_by_id))
    if not common:
        return None
    diffs = [float(left_by_id[i]) - float(right_by_id[i]) for i in common]
    ml = sum(float(left_by_id[i]) for i in common) / len(common)
    mr = sum(float(right_by_id[i]) for i in common) / len(common)
    assert abs(sum(diffs) / len(diffs) - (ml - mr)) < 1e-9, "paired direction identity violated"
    return cluster_bootstrap({i: d for i, d in zip(common, diffs)},
                             n_boot=n_boot, seed=seed)


def finite_permutation_p(diffs, n_perm=2000, seed=20261118, alternative="greater"):
    """Sign-flip permutation test with finite-sample correction (b+1)/(B+1)."""
    d = np.asarray(diffs, dtype=float)
    if d.size == 0:
        return None
    obs = float(d.mean())
    rng = np.random.default_rng(seed)
    exceed = 0
    for _ in range(n_perm):
        flipped = d * rng.choice([-1.0, 1.0], size=d.size)
        stat = float(flipped.mean())
        if alternative == "greater":
            exceed += int(stat >= obs)
        elif alternative == "less":
            exceed += int(stat <= obs)
        else:
            exceed += int(abs(stat) >= abs(obs))
    return (exceed + 1) / (n_perm + 1)


def zero_observation_summary(rows):
    """Describe zero observed hits without a pooled binomial guarantee."""
    instances = {r["id"] for r in rows}
    attackers = {r.get("attacker") for r in rows if r.get("attacker")}
    strategies = {r.get("strategy") for r in rows if r.get("strategy")}
    calls = sum(int(r.get("n_model_calls", 1)) for r in rows)
    questions = sum(int(r.get("n_unique_questions", r.get("n", 0))) for r in rows)
    hits = sum(int(r.get("hits", 0)) for r in rows)
    return {"n_instances": len(instances), "n_attackers": len(attackers),
            "n_strategies": len(strategies), "n_model_calls": calls,
            "n_unique_questions": questions, "observed_hits": hits,
            "interpretation": "zero observed hits under specified attackers/protocol"
            if hits == 0 else "observed hits present",
            "statistical_guarantee": None}
