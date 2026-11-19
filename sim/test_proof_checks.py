import math

import numpy as np

from proof_checks import (
    exact_entropy,
    exact_mi,
    fano_lower_bound,
    map_accuracy,
    pufferfish_epsilon_true,
    pufferfish_witness_bound,
    random_channel,
    random_joint_dsm,
    random_xst_with_channel,
)

SEED = 20260829
N_CONFIGS = 1000
TOL = 1e-9


def test_entropy_mi_sanity():
    p = np.array([0.5, 0.5])
    assert abs(exact_entropy(p) - 1.0) < 1e-12
    indep = np.outer([0.3, 0.7], [0.4, 0.6])
    assert abs(exact_mi(indep)) < 1e-12
    diag = np.diag([0.5, 0.5])
    assert abs(exact_mi(diag) - 1.0) < 1e-12
    print("test_entropy_mi_sanity OK")


def test_fano_lower_bound_property():
    rng = np.random.default_rng(SEED)
    violations = []
    for _ in range(N_CONFIGS):
        m = int(rng.integers(1, 4))
        sizes = [int(rng.integers(2, 6)) for _ in range(m)]
        d_size = int(rng.integers(2, 7))
        joint = random_joint_dsm(rng, d_size, sizes)
        I_DS, H_S, hit_rates = _fano_quantities(joint, sizes)
        bound = fano_lower_bound(H_S, hit_rates, sizes)
        if I_DS < bound - TOL:
            violations.append((I_DS, bound, hit_rates, sizes))
    assert not violations, violations[:3]
    print(f"test_fano_lower_bound_property OK ({N_CONFIGS} configs)")


def _fano_quantities(joint, sizes):
    m = len(sizes)
    flat_s = joint.sum(axis=0)
    H_S = exact_entropy(flat_s.reshape(-1))
    hit_rates = []
    for i in range(m):
        axes = tuple(a + 1 for a in range(m) if a != i)
        p_di_si = joint.sum(axis=axes) if axes else joint
        p_di = p_di_si.sum(axis=1, keepdims=True)
        post = np.where(p_di > 0, p_di_si / np.where(p_di > 0, p_di, 1.0), 0.0)
        correct = post.max(axis=1)
        hit_rates.append(float((p_di[:, 0] * correct).sum()))
    I_DS = _mi_from_joint(joint)
    return I_DS, H_S, hit_rates


def _mi_from_joint(joint):
    flat = joint.reshape(joint.shape[0], -1)
    return exact_mi(flat)


def test_pufferfish_witness_property():
    rng = np.random.default_rng(SEED + 1)
    violations = []
    for _ in range(N_CONFIGS):
        K = int(rng.integers(2, 7))
        M = int(rng.integers(2, 9))
        channel = random_channel(rng, K, M)
        prior = rng.dirichlet(np.ones(K))
        eps_true = pufferfish_epsilon_true(channel, prior)
        L_star = map_accuracy(channel, prior)
        bound = pufferfish_witness_bound(L_star, prior.min(), prior.max())
        if eps_true < bound - TOL:
            violations.append((eps_true, bound, L_star, K, M))
        L_weak = float(rng.uniform(1.0 / K, max(1.0 / K, L_star)))
        if pufferfish_witness_bound(L_weak, prior.min(), prior.max()) > bound + TOL:
            violations.append(("monotonicity", L_weak, L_star))
    assert not violations, violations[:3]
    print(f"test_pufferfish_witness_property OK ({N_CONFIGS} configs)")


def test_pufferfish_boundary_independent_channel():
    rng = np.random.default_rng(SEED + 2)
    K, M = 4, 5
    q = rng.dirichlet(np.ones(M))
    channel = np.tile(q, (K, 1))
    prior = rng.dirichlet(np.ones(K))
    L_star = map_accuracy(channel, prior)
    bound = pufferfish_witness_bound(L_star, prior.min(), prior.max())
    assert abs(L_star - prior.max()) < 1e-9
    assert bound <= 1e-9
    print("test_pufferfish_boundary_independent_channel OK")


def test_fano_threshold_corollary_counterexample():
    """The deleted threshold-mapping corollary is false.

    Uniform S over 100 values, D independent of S: I(D;S)=0 and optimal
    guessing hit rate L=0.01 <= tau_L=0.05, yet substituting tau_L into the
    Fano expression yields a positive lower bound.  This regression test
    records the counterexample; it does not validate the corollary.
    """
    k = 100
    prior = np.full(k, 1.0 / k)
    channel = np.tile(np.full(1, 1.0), (k, 1))  # single output, independent
    L_star = map_accuracy(channel, prior)
    assert abs(L_star - 0.01) < 1e-12
    joint = np.outer(prior, np.array([1.0]))
    I_DS = exact_mi(joint)
    assert abs(I_DS) < 1e-12
    invalid_bound = fano_lower_bound(math.log2(k), [0.05], [k])
    assert invalid_bound > 0.0
    assert I_DS < invalid_bound
    print("test_fano_threshold_corollary_counterexample OK", invalid_bound)


def test_feasibility_criterion_property():
    rng = np.random.default_rng(SEED + 3)
    violations = []
    for _ in range(N_CONFIGS):
        joint, p_d_given_xs = random_xst_with_channel(rng)
        I_DT = _cond_mi_from_table(joint, "D", "T")
        I_DS = _cond_mi_from_table(joint, "D", "S")
        I_XT_givenS = _cond_mi_x_t_given_s(joint)
        if I_DT > I_DS + I_XT_givenS + TOL:
            violations.append((I_DT, I_DS, I_XT_givenS))
    assert not violations, violations[:3]
    print(f"test_feasibility_criterion_property OK ({N_CONFIGS} configs)")


def _cond_mi_from_table(joint, var1, var2):
    idx = {"X": 0, "S": 1, "T": 2, "D": 3}
    a, b = idx[var1], idx[var2]
    others = tuple(i for i in range(4) if i not in (a, b))
    p_ab = joint.sum(axis=others)
    return exact_mi(p_ab)


def _cond_mi_x_t_given_s(joint):
    total = 0.0
    p_s = joint.sum(axis=(0, 2, 3))
    for s in range(joint.shape[1]):
        if p_s[s] <= 0:
            continue
        slice_xt = joint[:, s, :, :].sum(axis=2)
        total += p_s[s] * exact_mi(slice_xt)
    return total


if __name__ == "__main__":
    test_entropy_mi_sanity()
    test_fano_lower_bound_property()
    test_pufferfish_witness_property()
    test_pufferfish_boundary_independent_channel()
    test_feasibility_criterion_property()
    test_fano_threshold_corollary_counterexample()
    print("ALL PROOF-CHECK TESTS PASSED")
