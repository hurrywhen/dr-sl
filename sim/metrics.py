import math

Z95 = 1.959963984540054


def wilson_interval(hits, n, z=Z95):
    if n == 0:
        return 0.0, 1.0
    p = hits / n
    denom = 1 + z * z / n
    center = (p + z * z / (2 * n)) / denom
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / denom
    return max(0.0, center - half), min(1.0, center + half)


def wilson_upper(hits, n, z=Z95):
    return wilson_interval(hits, n, z)[1]


def passes_threshold(hits, n, tau):
    return wilson_upper(hits, n) <= tau


def mean_ci(values, n_boot=1000, seed=0):
    import numpy as np
    values = np.asarray(values, dtype=float)
    if values.size == 0:
        return float("nan"), (float("nan"), float("nan"))
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, values.size, size=(n_boot, values.size))
    boots = values[idx].mean(axis=1)
    return float(values.mean()), (float(np.quantile(boots, 0.025)), float(np.quantile(boots, 0.975)))
