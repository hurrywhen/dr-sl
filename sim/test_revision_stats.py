import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from revision_stats import (cluster_bootstrap, finite_permutation_p,
                            paired_cluster_delta, zero_observation_summary)


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


def test_paired_delta():
    a = {"x": 0.2, "y": 0.4}
    b = {"x": 0.1, "y": 0.5}
    out = paired_cluster_delta(a, b, n_boot=200, seed=1)
    assert abs(out["estimate"] - 0.0) < 1e-9
    print("test_paired_delta OK")


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
    test_paired_delta()
    test_zero_summary_no_guarantee()
    print("ALL REVISION STATS TESTS PASSED")
