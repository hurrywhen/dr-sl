"""Regression tests for tied-rank Spearman (round-3 P0 fix).

Cross-validates against an independent implementation: average ranks computed by
a different algorithm (count-based), then Pearson via statistics.correlation
(Python >= 3.10).  Also checks hand-computed reference cases with heavy ties.
"""
import random
import statistics

from revision_stratified import average_ranks, spearman


def _independent_ranks(xs):
    """Count-based average rank: rank(x) = 1 + (#smaller) + (#equal - 1)/2."""
    out = []
    for v in xs:
        smaller = sum(1 for u in xs if u < v)
        equal = sum(1 for u in xs if u == v)
        out.append(1.0 + smaller + (equal - 1) / 2.0)
    return out


def _independent_spearman(x, y):
    rx, ry = _independent_ranks(x), _independent_ranks(y)
    if len(set(rx)) < 2 or len(set(ry)) < 2:
        return None
    return statistics.correlation(rx, ry)


def test_average_ranks_hand_cases():
    assert average_ranks([10, 20, 30]) == [1.0, 2.0, 3.0]
    assert average_ranks([5, 5, 5]) == [2.0, 2.0, 2.0]
    assert average_ranks([1, 2, 2, 3]) == [1.0, 2.5, 2.5, 4.0]
    assert average_ranks([0, 0.5, 1, 0.5]) == [1.0, 2.5, 4.0, 2.5]
    print("test_average_ranks_hand_cases OK")


def test_spearman_heavy_ties_reference():
    # Scores concentrated on {0, 0.5, 1}, as in the calibration data.
    x = [0, 0, 0.5, 0.5, 1, 1, 1, 0.5]
    y = [0, 0.5, 0.5, 1, 1, 0.5, 1, 0]
    got = spearman(x, y)
    ref = _independent_spearman(x, y)
    assert abs(got - ref) < 1e-12, (got, ref)
    # Hand check via the tie-corrected formula on a small case:
    # x=[1,2,2,3], y=[1,1,2,3]: rx=[1,2.5,2.5,4], ry=[1.5,1.5,3,4]
    got2 = spearman([1, 2, 2, 3], [1, 1, 2, 3])
    ref2 = _independent_spearman([1, 2, 2, 3], [1, 1, 2, 3])
    assert abs(got2 - ref2) < 1e-12
    print("test_spearman_heavy_ties_reference OK", round(got, 4))


def test_spearman_random_tied_crossvalidation():
    rng = random.Random(20261121)
    for trial in range(300):
        n = rng.randint(5, 60)
        x = [rng.choice([0.0, 0.5, 1.0]) for _ in range(n)]
        y = [rng.choice([0.0, 0.5, 1.0]) for _ in range(n)]
        got = spearman(x, y)
        ref = _independent_spearman(x, y)
        if ref is None:
            assert got is None
        else:
            assert got is not None and abs(got - ref) < 1e-9, (trial, got, ref)
    # continuous values (no ties) must also agree
    for trial in range(100):
        n = rng.randint(5, 60)
        x = [rng.random() for _ in range(n)]
        y = [rng.random() for _ in range(n)]
        assert abs(spearman(x, y) - _independent_spearman(x, y)) < 1e-9
    print("test_spearman_random_tied_crossvalidation OK (400 configs)")


def test_double_argsort_was_wrong():
    """Documents the round-2 bug: double argsort breaks ties arbitrarily."""
    import numpy as np
    x = [0.0, 0.0, 0.5, 1.0, 1.0]
    wrong = np.argsort(np.argsort(x)).astype(float)
    right = average_ranks(x)
    assert list(wrong) != right  # distinct ranks for equal values
    assert right == [1.5, 1.5, 3.0, 4.5, 4.5]
    print("test_double_argsort_was_wrong OK")


if __name__ == "__main__":
    test_average_ranks_hand_cases()
    test_spearman_heavy_ties_reference()
    test_spearman_random_tied_crossvalidation()
    test_double_argsort_was_wrong()
    print("ALL SPEARMAN TIE TESTS PASSED")
