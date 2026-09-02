import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "dataset"))

import synth_values as sv
from protocol import POP_SIZE, POP_SEED, PRIMARY_DIMS, EXTENDED_DIMS, INCOME_BANDS, AGE_BAND
from qi import extract_qi

DISEASES = sv.DISEASES_COMMON + sv.DISEASES_RARE


def build_w1(n=POP_SIZE, seed=POP_SEED, profile="uniform"):
    rng = np.random.default_rng(seed)
    age = rng.integers(18, 86, size=n)
    gender = rng.integers(0, 2, size=n)
    city = rng.integers(0, len(sv.CITIES), size=n)
    disease = np.where(
        rng.random(n) < 0.8,
        rng.integers(0, len(sv.DISEASES_COMMON), size=n),
        rng.integers(len(sv.DISEASES_COMMON), len(DISEASES), size=n),
    )
    occupation = rng.integers(0, len(sv.OCCUPATIONS), size=n)
    hospital = rng.integers(0, len(sv.HOSPITALS), size=n)
    income_raw = rng.lognormal(mean=2.9, sigma=0.6, size=n)
    edges = [b[0] for b in INCOME_BANDS] + [float("inf")]
    income_band = np.clip(np.searchsorted(edges, income_raw, side="right") - 1, 0, len(INCOME_BANDS) - 1)
    if profile == "skewed":
        city_p = np.array([0.30, 0.22, 0.14, 0.10, 0.08, 0.06, 0.06, 0.04])
        city = rng.choice(len(sv.CITIES), size=n, p=city_p / city_p.sum())
        n_bands = len(range(18, 86, AGE_BAND))
        band_p = np.array([1, 2, 3, 5, 8, 10, 12, 12, 11, 9, 7, 6, 4, 3], dtype=float)[:n_bands]
        band = rng.choice(n_bands, size=n, p=band_p / band_p.sum())
        age = band * AGE_BAND + rng.integers(0, AGE_BAND, size=n)
        common_p = np.array([0.30, 0.25, 0.15, 0.10, 0.10])
        common_idx = rng.choice(len(sv.DISEASES_COMMON), size=n, p=common_p / common_p.sum())
        rare_idx = rng.integers(len(sv.DISEASES_COMMON), len(DISEASES), size=n)
        disease = np.where(rng.random(n) < 0.9, common_idx, rare_idx)
        occ_p = np.array([0.22, 0.18, 0.16, 0.14, 0.12, 0.10, 0.08])[:len(sv.OCCUPATIONS)]
        occupation = rng.choice(len(sv.OCCUPATIONS), size=n, p=occ_p / occ_p.sum())
    pop = {
        "age": age,
        "age_band": age // AGE_BAND,
        "gender": gender,
        "city": city,
        "disease": disease,
        "occupation": occupation,
        "hospital": hospital,
        "income_band": income_band,
        "n": n,
        "world": f"W1-{profile}",
        "seed": seed,
    }
    return pop


def ipf(dim_names, marginals, n_iters=50, tol=1e-6):
    shape = tuple(marginals["__shape__"])
    joint = np.full(shape, 1.0 / np.prod(shape))
    parsed = {}
    for key, table in marginals.items():
        if key == "__shape__":
            continue
        parsed[tuple(key.split(","))] = np.asarray(table["probs"], dtype=float)
    for _ in range(n_iters):
        delta = 0.0
        for key_dims, target_flat in parsed.items():
            axes = tuple(dim_names.index(d) for d in key_dims)
            reshape_dims = tuple(shape[a] if a in axes else 1 for a in range(len(dim_names)))
            target = target_flat.reshape(reshape_dims)
            sum_axes = tuple(a for a in range(len(dim_names)) if a not in axes)
            current = joint.sum(axis=sum_axes, keepdims=True)
            current = np.where(current <= 0, 1e-12, current)
            new_joint = joint * (target / current)
            delta = max(delta, float(np.abs(new_joint - joint).max()))
            joint = new_joint
        if delta < tol:
            break
    return joint / joint.sum()


def build_w2(marginals_path, n=POP_SIZE, seed=POP_SEED, dims=None):
    dims = dims or PRIMARY_DIMS
    with open(marginals_path) as f:
        marginals = json.load(f)
    joint = ipf(list(dims), marginals)
    rng = np.random.default_rng(seed)
    flat = joint.reshape(-1)
    cells = rng.choice(flat.size, size=n, p=flat)
    shape = joint.shape
    idx = np.unravel_index(cells, shape)
    pop = {dims[i]: idx[i].astype(np.int64) for i in range(len(dims))}
    if "age_band" in pop:
        pop["age"] = pop["age_band"] * AGE_BAND + rng.integers(0, AGE_BAND, size=n)
    pop.update({"n": n, "world": "W2", "seed": seed, "marginals": marginals_path})
    return pop


def query_k(pop, qi_tuple, dims):
    n = pop["n"]
    mask = np.ones(n, dtype=bool)
    for d, v in zip(dims, qi_tuple):
        if v is None or v < 0 or d not in pop:
            continue
        mask &= pop[d] == v
    return int(mask.sum())


def marginal_check(pop, dims, targets):
    report = {}
    for d in dims:
        if d not in pop or d not in targets:
            continue
        vals, counts = np.unique(pop[d], return_counts=True)
        emp = counts / counts.sum()
        tgt = np.asarray(targets[d]["probs"], dtype=float)
        k = min(len(emp), len(tgt))
        tv = 0.5 * float(np.abs(emp[:k] - tgt[:k]).sum())
        report[d] = {"total_variation": tv, "n_levels": int(len(vals))}
    return report


def run_k_experiment(dataset_path, splits=("test", "adversarial"), dims=PRIMARY_DIMS, pop=None):
    from qi import load_dataset
    rows = [r for r in load_dataset(dataset_path) if r["split"] in splits]
    pop = pop or build_w1()
    results = []
    for r in rows:
        qi = extract_qi(r["annotations"], dims)
        present = sum(1 for v in qi if v >= 0)
        k = query_k(pop, qi, dims) if present > 0 else None
        results.append({
            "id": r["id"],
            "domain": r["domain"],
            "split": r["split"],
            "qi_present": present,
            "k": k,
        })
    return pop, results
