import numpy as np

from shift import (
    type_signature, coverage, mix_ids, tfidf_matrix,
    domain_auc, auc_from_scores, mmd_test,
)


def _item(qtypes, explicit=False):
    return {
        "annotations": {
            "quasi_identifiers": [{"type": t} for t in qtypes],
            "explicit_identifiers": [{"type": "phone"}] if explicit else [],
        }
    }


def test_signature_and_coverage():
    lib = [_item(["age", "disease"]), _item(["city"])]
    online = [
        _item(["age", "disease"]),
        _item(["age"]),
        _item(["age", "disease", "hospital"]),
        _item([]),
    ]
    cov = coverage(online, lib)
    assert cov["exact"] == 0.5
    assert cov["subset"] == 0.75
    assert sorted(list(cov["uncovered"].keys())) == [("age", "disease", "hospital")]
    sig = type_signature(_item(["age"], explicit=True))
    assert "EXPLICIT" in sig
    print("test_signature_and_coverage OK")


def test_mix_ids():
    test_ids = [f"T{i}" for i in range(100)]
    new_ids = [f"N{i}" for i in range(100)]
    mixed = mix_ids(test_ids, new_ids, 0.25, seed=1)
    n_new = sum(1 for i in mixed if i.startswith("N"))
    assert n_new == 25, n_new
    assert len(mixed) == 125
    assert mix_ids(test_ids, new_ids, 0.25, seed=1) == mixed
    assert set(mix_ids(test_ids, new_ids, 0.0, seed=1)) == set(test_ids)
    print("test_mix_ids OK")


def test_auc_sanity():
    assert abs(auc_from_scores([0.1, 0.2, 0.8, 0.9], [0, 0, 1, 1]) - 1.0) < 1e-12
    assert abs(auc_from_scores([0.9, 0.8, 0.2, 0.1], [0, 0, 1, 1]) - 0.0) < 1e-12
    print("test_auc_sanity OK")


def test_domain_auc_separable():
    rng = np.random.default_rng(0)
    s = [f"患者{a}岁，确诊{b}，在{c}医院就诊。" for a, b, c in
         zip(rng.integers(20, 80, 60), ["高血压"] * 60, ["仁济"] * 60)]
    t = [f"账户余额{a}元，信用卡{b}，请查询{c}业务。" for a, b, c in
         zip(rng.integers(1000, 9000, 60), ["6222"] * 60, ["理财"] * 60)]
    auc, (lo, hi) = domain_auc(s, t)
    assert auc > 0.9, auc
    print(f"test_domain_auc_separable OK (auc={auc:.3f})")


def test_domain_auc_indistinguishable():
    rng = np.random.default_rng(0)
    base = [f"患者{a}岁，确诊高血压，在仁济医院就诊。" for a in rng.integers(20, 80, 60)]
    s = base[:30]
    t = base[30:]
    auc, _ = domain_auc(s, t)
    assert 0.3 <= auc <= 0.7, auc
    print(f"test_domain_auc_indistinguishable OK (auc={auc:.3f})")


def test_mmd():
    rng = np.random.default_rng(0)
    X = rng.normal(0, 1, size=(60, 8))
    Y_same = rng.normal(0, 1, size=(60, 8))
    Y_diff = rng.normal(2.0, 1, size=(60, 8))
    _, p_same = mmd_test(X, Y_same, n_perm=200, seed=0)
    _, p_diff = mmd_test(X, Y_diff, n_perm=200, seed=0)
    assert p_same > 0.05, p_same
    assert p_diff <= 0.05, p_diff
    print(f"test_mmd OK (p_same={p_same:.3f}, p_diff={p_diff:.3f})")


if __name__ == "__main__":
    test_signature_and_coverage()
    test_mix_ids()
    test_auc_sanity()
    test_domain_auc_separable()
    test_domain_auc_indistinguishable()
    test_mmd()
    print("ALL SHIFT TESTS PASSED")
