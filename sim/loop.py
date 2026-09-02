from dataclasses import dataclass, field

from metrics import wilson_upper
from protocol import MAX_ROUNDS_FACTOR, MAX_ROUNDS_EXTRA


@dataclass
class LoopResult:
    status: str
    D: object
    rounds: int
    history: list = field(default_factory=list)
    residual_leak_report: list = field(default_factory=list)
    R: float = None
    L_upper: float = None
    U: float = None


def max_rounds(n_attrs):
    return MAX_ROUNDS_FACTOR * n_attrs + MAX_ROUNDS_EXTRA


def _eval(evaluate_fn, D, Q, S, X):
    m = evaluate_fn(D, Q, S, X)
    m["L_upper"] = wilson_upper(m["hits"], m["n_probes"])
    return m


def _pass(metrics, tau_l, tau_u):
    return metrics["L_upper"] <= tau_l and metrics["U"] >= tau_u


def lexicographic_loop(X, S, Q, P, dehydrate_fn, strengthen_fn, loosen_fn, evaluate_fn,
                       leak_contrib_fn, tau_l, tau_u, tau_r, n_stable=1, delta=0.05):
    n_attrs = len(S)
    B = max_rounds(n_attrs)
    D = dehydrate_fn(X, S, P)
    metrics = _eval(evaluate_fn, D, Q, S, X)
    history = [{"phase": "init", "L_upper": metrics["L_upper"], "U": metrics["U"], "R": metrics["R"]}]

    t = 0
    no_progress = 0
    while metrics["R"] < tau_r and t < B:
        D_new = loosen_fn(D, X, S, P)
        if D_new is None:
            break
        m_new = _eval(evaluate_fn, D_new, Q, S, X)
        if m_new["R"] > metrics["R"]:
            D, metrics = D_new, m_new
            no_progress = 0
            history.append({"phase": "loosen", "L_upper": metrics["L_upper"], "U": metrics["U"], "R": metrics["R"]})
        else:
            no_progress += 1
            history.append({"phase": "loosen_no_progress", "R": m_new["R"]})
            if no_progress >= 2:
                break
        t += 1

    skipped = set()
    tried_loosen = set()
    stable_count = 1 if _pass(metrics, tau_l, tau_u) else 0

    while not (stable_count >= n_stable) and t < B:
        candidates = [s for s in S if s not in skipped]
        if not candidates:
            break
        contribs = leak_contrib_fn(D, S)
        s_star = max(candidates, key=lambda s: contribs[s])
        if contribs[s_star] <= 0:
            skipped.add(s_star)
            continue
        D_new = strengthen_fn(D, s_star, X, S, P)
        if D_new is None:
            skipped.add(s_star)
            history.append({"phase": "strengthen_fail", "s": s_star})
            t += 1
            continue
        m_new = _eval(evaluate_fn, D_new, Q, S, X)
        if m_new["R"] >= tau_r and m_new["U"] >= tau_u:
            D, metrics = D_new, m_new
            stable_count = stable_count + 1 if _pass(metrics, tau_l, tau_u) else 0
            history.append({"phase": "strengthen", "s": s_star, "L_upper": metrics["L_upper"],
                            "U": metrics["U"], "R": metrics["R"]})
            t += 1
            continue
        if s_star not in tried_loosen:
            tried_loosen.add(s_star)
            D_loose = loosen_fn(D, X, S, P)
            if D_loose is not None:
                m_loose = _eval(evaluate_fn, D_loose, Q, S, X)
                if m_loose["R"] > metrics["R"]:
                    D, metrics = D_loose, m_loose
                    stable_count = stable_count + 1 if _pass(metrics, tau_l, tau_u) else 0
                    history.append({"phase": "loosen", "L_upper": metrics["L_upper"],
                                    "U": metrics["U"], "R": metrics["R"]})
                    tried_loosen.clear()
                    t += 1
                    continue
        skipped.add(s_star)
        history.append({"phase": "strengthen_reject", "s": s_star, "R_new": m_new["R"]})
        t += 1

    if _pass(metrics, tau_l, tau_u):
        return LoopResult("PASS", D, t, history, R=metrics["R"],
                          L_upper=metrics["L_upper"], U=metrics["U"])

    contribs = leak_contrib_fn(D, S)
    residual = [{"s": s, "contrib": contribs.get(s),
                 "reason": "skipped (gate-infeasible)" if s in skipped else "budget exhausted"}
                for s in S]
    return LoopResult("INFEASIBLE", D, t, history,
                      residual_leak_report=residual, R=metrics["R"],
                      L_upper=metrics["L_upper"], U=metrics["U"])
