import math

import numpy as np


def exact_entropy(p):
    p = np.asarray(p, dtype=float).reshape(-1)
    p = p[p > 0]
    return float(-(p * np.log2(p)).sum())


def exact_mi(joint):
    joint = np.asarray(joint, dtype=float)
    if joint.ndim != 2:
        joint = joint.reshape(joint.shape[0], -1)
    px = joint.sum(axis=1, keepdims=True)
    py = joint.sum(axis=0, keepdims=True)
    mask = joint > 0
    ratio = np.zeros_like(joint)
    denom = px @ py
    ratio[mask] = joint[mask] / denom[mask]
    return float((joint[mask] * np.log2(ratio[mask])).sum())


def _h2(p):
    if p <= 0.0 or p >= 1.0:
        return 0.0
    return -(p * math.log2(p) + (1 - p) * math.log2(1 - p))


def fano_lower_bound(H_S, hit_rates, value_sizes):
    total = H_S
    for L, k in zip(hit_rates, value_sizes):
        if k <= 1:
            continue
        pe = 1.0 - L
        total -= _h2(pe) + pe * math.log2(k - 1)
    return total


def random_joint_dsm(rng, d_size, sizes):
    style = rng.integers(0, 2)
    if style == 0:
        p_d = rng.dirichlet(np.ones(d_size) * float(rng.uniform(0.3, 3.0)))
        joint = np.zeros((d_size, *sizes))
        for d in range(d_size):
            cond = 1.0
            for i, k in enumerate(sizes):
                cond_i = rng.dirichlet(np.ones(k) * float(rng.uniform(0.3, 3.0)))
                shape = [1] * len(sizes)
                shape[i] = k
                cond = cond * cond_i.reshape(shape)
            joint[d] = p_d[d] * cond
    else:
        flat = rng.dirichlet(np.ones(d_size * int(np.prod(sizes))) * float(rng.uniform(0.3, 3.0)))
        joint = flat.reshape((d_size, *sizes))
    return joint / joint.sum()


def random_channel(rng, K, M):
    alpha = float(rng.uniform(0.2, 5.0))
    return np.array([rng.dirichlet(np.ones(M) * alpha) for _ in range(K)])


def pufferfish_epsilon_true(channel, prior=None):
    eps = 0.0
    K, M = channel.shape
    for v1 in range(K):
        for v2 in range(v1 + 1, K):
            for d in range(M):
                a, b = channel[v1, d], channel[v2, d]
                if a <= 0 and b <= 0:
                    continue
                if a <= 0 or b <= 0:
                    return float("inf")
                eps = max(eps, abs(math.log(a / b)))
    return eps


def map_accuracy(channel, prior):
    p_d = prior @ channel
    total = 0.0
    for d in range(channel.shape[1]):
        if p_d[d] <= 0:
            continue
        post = channel[:, d] * prior / p_d[d]
        total += p_d[d] * post.max()
    return float(total)


def pufferfish_witness_bound(L, p_min, p_max):
    if L <= 0.0:
        return float("-inf")
    if L >= 1.0:
        return float("inf")
    return math.log(L / (1.0 - L)) + math.log(p_min / p_max)


def random_xst_with_channel(rng):
    nx = int(rng.integers(2, 7))
    ns = int(rng.integers(2, min(nx + 1, 6)))
    nt = int(rng.integers(2, min(nx + 1, 6)))
    nd = int(rng.integers(2, 7))
    p_x = rng.dirichlet(np.ones(nx) * float(rng.uniform(0.3, 3.0)))
    f = rng.integers(0, ns, size=nx)
    g = rng.integers(0, nt, size=nx)
    alpha = float(rng.uniform(0.2, 5.0))
    joint = np.zeros((nx, ns, nt, nd))
    channel = np.zeros((nx, ns, nd))
    for x in range(nx):
        for s in range(ns):
            channel[x, s] = rng.dirichlet(np.ones(nd) * alpha)
        s, t = f[x], g[x]
        joint[x, s, t, :] = p_x[x] * channel[x, s]
    return joint, channel
