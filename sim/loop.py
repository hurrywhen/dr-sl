from dataclasses import dataclass, field

from protocol import MAX_ROUNDS_FACTOR, MAX_ROUNDS_EXTRA


@dataclass
class LoopResult:
    status: str
    D: object
    rounds: int
    history: list = field(default_factory=list)
    residual_leak_report: list = field(default_factory=list)
    R: float = None
    L_upper: float = None  # Legacy field name; now the observed point rate.
    U: float = None
    stable: bool = False
    n_evaluations: int = 0


def max_rounds(n_attrs):
    return MAX_ROUNDS_FACTOR * n_attrs + MAX_ROUNDS_EXTRA


def _eval(evaluate_fn, D, Q, S, X):
    m = dict(evaluate_fn(D, Q, S, X))
    n = m.get("n_probes", 0)
    observed = m.get("L", m.get("hits", 0) / n if n else 1.0)
    m["L"] = float(observed)
    # Kept for readers of archived result files.  This is not a Wilson bound.
    m["L_upper"] = float(observed)
    m["gate_type"] = "heuristic_point_rate"
    return m


def _pass(metrics, tau_l, tau_u):
    return (metrics.get("n_probes", 0) > 0 and metrics["L"] <= tau_l
            and metrics.get("U") is not None and metrics["U"] >= tau_u)


def _snapshot(metrics):
    return {"L": float(metrics["L"]), "U": float(metrics["U"]),
            "R": metrics.get("R"), "n_probes": metrics.get("n_probes", 0)}


def _stable(window, n_stable, delta, tau_l, tau_u):
    if len(window) < n_stable:
        return False
    recent = window[-n_stable:]
    if not all(_pass(m, tau_l, tau_u) for m in recent):
        return False
    for key in ("L", "U", "R"):
        vals = [m[key] for m in recent if m.get(key) is not None]
        if len(vals) == len(recent) and max(vals) - min(vals) > delta:
            return False
    return True


def lexicographic_loop(X, S, Q, P, dehydrate_fn, strengthen_fn, loosen_fn, evaluate_fn,
                       leak_contrib_fn, tau_l, tau_u, tau_r, n_stable=3, delta=0.05):
    """Finite-budget lexicographic loop with an implemented stability gate.

    Stability evaluations repeat the *same* artifact.  Every artifact receives
    at most ``n_stable`` such evaluations, so stochastic instability cannot
    bypass the finite budget.  Accepted artifact changes reset the window.
    """
    n_stable = max(1, int(n_stable))
    n_attrs = len(S)
    B = max_rounds(n_attrs)
    D = dehydrate_fn(X, S, P)
    metrics = _eval(evaluate_fn, D, Q, S, X)
    n_evaluations = 1
    window = [_snapshot(metrics)]
    stability_checks = 1
    history = [{"phase": "init", "L": metrics["L"], "L_upper": metrics["L"],
                "U": metrics["U"], "R": metrics["R"], "gate_type": metrics["gate_type"]}]

    t = 0
    no_progress = 0
    while metrics["R"] < tau_r and t < B:
        D_new = loosen_fn(D, X, S, P)
        t += 1
        if D_new is None:
            history.append({"phase": "loosen_none"})
            break
        m_new = _eval(evaluate_fn, D_new, Q, S, X)
        n_evaluations += 1
        if m_new["R"] > metrics["R"]:
            D, metrics = D_new, m_new
            window, stability_checks = [_snapshot(metrics)], 1
            no_progress = 0
            history.append({"phase": "loosen", "L": metrics["L"], "L_upper": metrics["L"],
                            "U": metrics["U"], "R": metrics["R"]})
        else:
            no_progress += 1
            history.append({"phase": "loosen_no_progress", "R": m_new["R"]})
            if no_progress >= 2:
                break

    skipped = set()
    tried_loosen = set()
    stable = _stable(window, n_stable, delta, tau_l, tau_u)

    while not stable and t < B:
        # Complete the same-artifact stability window before changing D.
        if _pass(metrics, tau_l, tau_u) and stability_checks < n_stable:
            metrics = _eval(evaluate_fn, D, Q, S, X)
            n_evaluations += 1
            stability_checks += 1
            window.append(_snapshot(metrics))
            window = window[-n_stable:]
            history.append({"phase": "stability_check", "L": metrics["L"],
                            "L_upper": metrics["L"], "U": metrics["U"],
                            "R": metrics["R"], "check": stability_checks})
            stable = _stable(window, n_stable, delta, tau_l, tau_u)
            if stable or _pass(metrics, tau_l, tau_u):
                continue
            window = [_snapshot(metrics)]

        candidates = [s for s in S if s not in skipped]
        if not candidates:
            break
        contribs = leak_contrib_fn(D, S)
        s_star = max(candidates, key=lambda s: contribs.get(s, 0.0))
        if contribs.get(s_star, 0.0) <= 0:
            skipped.add(s_star)
            t += 1
            history.append({"phase": "skip_zero_contribution", "s": s_star})
            continue

        D_new = strengthen_fn(D, s_star, X, S, P)
        t += 1
        if D_new is None:
            skipped.add(s_star)
            history.append({"phase": "strengthen_fail", "s": s_star})
            continue
        m_new = _eval(evaluate_fn, D_new, Q, S, X)
        n_evaluations += 1
        if m_new["R"] >= tau_r and m_new["U"] is not None and m_new["U"] >= tau_u:
            D, metrics = D_new, m_new
            window, stability_checks = [_snapshot(metrics)], 1
            history.append({"phase": "strengthen", "s": s_star, "L": metrics["L"],
                            "L_upper": metrics["L"], "U": metrics["U"], "R": metrics["R"]})
            stable = _stable(window, n_stable, delta, tau_l, tau_u)
            continue

        accepted_loosen = False
        if s_star not in tried_loosen:
            tried_loosen.add(s_star)
            D_loose = loosen_fn(D, X, S, P)
            if D_loose is not None:
                m_loose = _eval(evaluate_fn, D_loose, Q, S, X)
                n_evaluations += 1
                if m_loose["R"] > metrics["R"]:
                    D, metrics = D_loose, m_loose
                    window, stability_checks = [_snapshot(metrics)], 1
                    history.append({"phase": "loosen", "L": metrics["L"],
                                    "L_upper": metrics["L"], "U": metrics["U"],
                                    "R": metrics["R"]})
                    tried_loosen.clear()
                    stable = _stable(window, n_stable, delta, tau_l, tau_u)
                    accepted_loosen = True
        if accepted_loosen:
            continue
        skipped.add(s_star)
        window = [_snapshot(metrics)]
        history.append({"phase": "strengthen_reject", "s": s_star, "R_new": m_new["R"]})

    if stable and _stable(window, n_stable, delta, tau_l, tau_u):
        return LoopResult("PASS", D, t, history, R=metrics["R"],
                          L_upper=metrics["L"], U=metrics["U"], stable=True,
                          n_evaluations=n_evaluations)

    contribs = leak_contrib_fn(D, S)
    residual = [{"s": s, "contrib": contribs.get(s),
                 "reason": ("skipped (gate-infeasible)" if s in skipped
                            else "stability or budget requirement unmet")}
                for s in S]
    return LoopResult("INFEASIBLE", D, t, history,
                      residual_leak_report=residual, R=metrics["R"],
                      L_upper=metrics["L"], U=metrics["U"], stable=False,
                      n_evaluations=n_evaluations)
