import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from revision_stats import (cluster_bootstrap, finite_permutation_p,
                            paired_delta, zero_observation_summary)


def test_cluster_bootstrap_unit():
    # Two instances, many nested rows each.  Bootstrap must resample instances.
    vals = {"a": [0.0] * 100, "b": [1.0] * 100}
    out = cluster_bootstrap(vals, n_boot=500, seed=1)
    assert out["unit"] == "instance_cluster"
    assert out["n_instances"] == 2
    assert abs(out["estimate"] - 0.5) < 1e-9
    print("test_cluster_bootstrap_unit OK")


def test_finite_permutation_never_zero():
    p = finite_permutation_p([1.0, 1.0, 1.0, 1.0], n_perm=100, seed=1)
    assert p > 0.0
    assert p <= 1.0
    print("test_finite_permutation_never_zero OK", p)


def test_paired_delta_direction():
    """Round-4 P0: paired_delta(left, right) must be left − right.

    The former paired_cluster_delta(a, b) computed b−a and was mislabelled at
    two call sites.  Asymmetric hand case fixes the direction unambiguously.
    """
    left = {"x": 0.9, "y": 0.7, "z": 0.5}
    right = {"x": 0.1, "y": 0.2, "z": 0.3}
    out = paired_delta(left, right, n_boot=200, seed=1)
    # diffs 0.8/0.5/0.2 -> mean 0.5 = mean(left) 0.7 - mean(right) 0.2
    assert abs(out["estimate"] - 0.5) < 1e-9, out["estimate"]
    rev = paired_delta(right, left, n_boot=200, seed=1)
    assert abs(rev["estimate"] + 0.5) < 1e-9
    # CI must flip exactly under argument swap (same bootstrap seed).
    assert abs(out["ci95"][0] + rev["ci95"][1]) < 1e-9
    assert abs(out["ci95"][1] + rev["ci95"][0]) < 1e-9
    print("test_paired_delta_direction OK")


def test_paired_delta_mean_identity():
    """mean(Δ) == mean(left) − mean(right) on random tied data (P0 regression)."""
    import random
    rng = random.Random(20261122)
    for trial in range(200):
        n = rng.randint(3, 50)
        ids = [f"i{k}" for k in range(n)]
        left = {i: rng.choice([0.0, 0.5, 1.0]) for i in ids}
        right = {i: rng.choice([0.0, 0.5, 1.0]) for i in ids}
        # drop a few keys to exercise the common-instance intersection
        if n > 5:
            del left[ids[0]]
            del right[ids[-1]]
        common = sorted(set(left) & set(right))
        out = paired_delta(left, right, n_boot=100, seed=1)
        ml = sum(left[i] for i in common) / len(common)
        mr = sum(right[i] for i in common) / len(common)
        assert abs(out["estimate"] - (ml - mr)) < 1e-9, (trial, out["estimate"], ml - mr)
    print("test_paired_delta_mean_identity OK (200 configs)")


def test_zero_summary_no_guarantee():
    rows = [{"id": "a", "attacker": "m1", "strategy": "s1", "hits": 0, "n": 5, "n_model_calls": 1, "n_unique_questions": 5},
            {"id": "a", "attacker": "m2", "strategy": "s1", "hits": 0, "n": 5, "n_model_calls": 1, "n_unique_questions": 5}]
    out = zero_observation_summary(rows)
    assert out["n_instances"] == 1
    assert out["n_attackers"] == 2
    assert out["observed_hits"] == 0
    assert out["statistical_guarantee"] is None
    print("test_zero_summary_no_guarantee OK")


if __name__ == "__main__":
    test_cluster_bootstrap_unit()
    test_finite_permutation_never_zero()
    test_paired_delta_direction()
    test_paired_delta_mean_identity()
    test_zero_summary_no_guarantee()
    print("ALL REVISION STATS TESTS PASSED")
