import numpy as np


def type_signature(item):
    types = {e["type"] for e in item["annotations"]["quasi_identifiers"]}
    if item["annotations"]["explicit_identifiers"]:
        types.add("EXPLICIT")
    return frozenset(types)


def coverage(online_items, library_items):
    lib = {type_signature(i) for i in library_items if type_signature(i)}
    exact = 0
    subset = 0
    uncovered = {}
    for i in online_items:
        sig = type_signature(i)
        if not sig:
            exact += 1
            subset += 1
            continue
        if sig in lib:
            exact += 1
            subset += 1
        elif any(sig <= c for c in lib):
            subset += 1
        else:
            uncovered.setdefault(sig, 0)
            uncovered[sig] += 1
    n = len(online_items)
    return {"exact": exact / n if n else 1.0,
            "subset": subset / n if n else 1.0,
            "uncovered": {tuple(sorted(k)): v for k, v in uncovered.items()}}


def mix_ids(test_ids, tnew_ids, alpha, seed):
    rng = np.random.default_rng(seed)
    n = len(test_ids)
    k_new = int(round(alpha * n))
    k_new = min(k_new, len(tnew_ids))
    chosen = rng.choice(len(tnew_ids), size=k_new, replace=False)
    out = list(test_ids)
    for j, idx in enumerate(chosen):
        pos = int(rng.integers(0, len(out) + 1))
        out.insert(pos, tnew_ids[idx])
    return out


def _char_ngrams(text, ns=(2, 3)):
    grams = []
    for n in ns:
        grams.extend(text[i:i + n] for i in range(max(0, len(text) - n + 1)))
    return grams


def tfidf_matrix(texts, ns=(2, 3)):
    vocab = {}
    docs = []
    for t in texts:
        grams = _char_ngrams(t, ns)
        row = {}
        for g in grams:
            row[g] = row.get(g, 0) + 1
        docs.append(row)
        for g in row:
            vocab.setdefault(g, len(vocab))
    n, d = len(texts), len(vocab)
    mat = np.zeros((n, d))
    for i, row in enumerate(docs):
        for g, c in row.items():
            mat[i, vocab[g]] = 1.0 + np.log(c)
    df = (mat > 0).sum(axis=0) + 1.0
    idf = np.log((n + 1) / df) + 1.0
    mat = mat * idf
    norms = np.linalg.norm(mat, axis=1, keepdims=True)
    norms[norms == 0] = 1.0
    return mat / norms


def _logreg_fit_predict(X_tr, y_tr, X_te, lr=0.1, iters=300, l2=1e-3, seed=0):
    rng = np.random.default_rng(seed)
    w = rng.normal(0, 0.01, size=X_tr.shape[1])
    b = 0.0
    n = X_tr.shape[0]
    for _ in range(iters):
        z = X_tr @ w + b
        p = 1.0 / (1.0 + np.exp(-np.clip(z, -30, 30)))
        grad_w = X_tr.T @ (p - y_tr) / n + l2 * w
        grad_b = float((p - y_tr).mean())
        w -= lr * grad_w
        b -= lr * grad_b
    return X_te @ w + b


def auc_from_scores(scores, labels):
    scores = np.asarray(scores, dtype=float)
    labels = np.asarray(labels)
    pos = scores[labels == 1]
    neg = scores[labels == 0]
    if len(pos) == 0 or len(neg) == 0:
        return float("nan")
    ranks = np.argsort(np.argsort(scores)) + 1.0
    r_pos = ranks[labels == 1].sum()
    return float((r_pos - len(pos) * (len(pos) + 1) / 2) / (len(pos) * len(neg)))


def domain_auc(texts_s, texts_t, n_folds=5, seed=0):
    X = tfidf_matrix(list(texts_s) + list(texts_t))
    y = np.array([0] * len(texts_s) + [1] * len(texts_t))
    rng = np.random.default_rng(seed)
    idx = rng.permutation(len(y))
    folds = np.array_split(idx, n_folds)
    scores = np.zeros(len(y))
    for f in folds:
        mask = np.ones(len(y), dtype=bool)
        mask[f] = False
        s = _logreg_fit_predict(X[mask], y[mask].astype(float), X[f], seed=seed)
        scores[f] = s
    auc = auc_from_scores(scores, y)
    n1, n0 = int(y.sum()), int((1 - y).sum())
    se = float(np.sqrt(auc * (1 - auc) / min(n1, n0))) if 0 < auc < 1 else 0.05
    return auc, (auc - 1.96 * se, auc + 1.96 * se)


def _gaussian_kernel(X, Y, bw):
    xx = (X * X).sum(axis=1)[:, None]
    yy = (Y * Y).sum(axis=1)[None, :]
    d2 = xx + yy - 2 * X @ Y.T
    return np.exp(-d2 / (2 * bw * bw))


def mmd_test(X, Y, n_perm=1000, seed=0):
    X = np.asarray(X, dtype=float)
    Y = np.asarray(Y, dtype=float)
    stacked = np.vstack([X, Y])
    d2 = ((stacked[:, None, :] - stacked[None, :, :]) ** 2).sum(-1)
    med = np.median(d2[d2 > 0]) if (d2 > 0).any() else 1.0
    bw = float(np.sqrt(med / 2)) or 1.0
    Kxx = _gaussian_kernel(X, X, bw)
    Kyy = _gaussian_kernel(Y, Y, bw)
    Kxy = _gaussian_kernel(X, Y, bw)
    n, m = len(X), len(Y)
    mmd2 = float(Kxx.mean() + Kyy.mean() - 2 * Kxy.mean())
    rng = np.random.default_rng(seed)
    all_idx = np.arange(n + m)
    count = 0
    for _ in range(n_perm):
        perm = rng.permutation(all_idx)
        a, b = perm[:n], perm[n:]
        K = _gaussian_kernel(stacked[a], stacked[b], bw)
        Kaa = _gaussian_kernel(stacked[a], stacked[a], bw)
        Kbb = _gaussian_kernel(stacked[b], stacked[b], bw)
        if float(Kaa.mean() + Kbb.mean() - 2 * K.mean()) >= mmd2:
            count += 1
    return mmd2, (count + 1) / (n_perm + 1)
