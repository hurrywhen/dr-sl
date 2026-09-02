import math

from loop import lexicographic_loop, max_rounds
from protocol import TAU_L, TAU_R, TAU_U, probes_per_attr


def make_world(n, r_cost, leak_step=0.45, initial_leak=0.9, initial_R=0.95, probes=None):
    probes = probes or probes_per_attr(n)
    S = [f"s{i}" for i in range(n)]

    def dehydrate(X, S_, P):
        return {"leak": [initial_leak] * n, "R": initial_R}

    def loosen(D, X, S_, P):
        return {"leak": D["leak"][:], "R": min(1.0, D["R"] + 0.2)}

    def strengthen(D, s, X, S_, P):
        i = S_.index(s)
        new_leak = D["leak"][:]
        new_leak[i] = max(0.0, new_leak[i] - leak_step)
        return {"leak": new_leak, "R": D["R"] - r_cost[i]}

    def evaluate(D, Q, S_, X):
        hits = sum(int(round(probes * l)) for l in D["leak"])
        return {"hits": hits, "n_probes": probes * len(S_), "U": 0.8, "R": D["R"]}

    def leak_contrib(D, S_):
        return {s: D["leak"][i] for i, s in enumerate(S_)}

    return S, dehydrate, strengthen, loosen, evaluate, leak_contrib


def run_case(n, r_cost, initial_R=0.95):
    S, deh, stre, loos, eva, lcf = make_world(n, r_cost, initial_R=initial_R)
    res = lexicographic_loop("X", S, ["q"], None, deh, stre, loos, eva, lcf,
                             tau_l=TAU_L, tau_u=TAU_U, tau_r=TAU_R, n_stable=1)
    return res


def test_feasible():
    res = run_case(5, [0.02] * 5)
    assert res.status == "PASS", res
    assert res.rounds <= max_rounds(5) + 5
    assert res.L_upper <= TAU_L
    assert res.R >= TAU_R
    print("test_feasible OK:", res.status, "rounds=", res.rounds, "L_upper=", round(res.L_upper, 4))


def test_infeasible():
    res = run_case(5, [0.3] * 5)
    assert res.status == "INFEASIBLE", res
    assert len(res.residual_leak_report) == 5
    assert res.rounds <= max_rounds(5) + 5
    print("test_infeasible OK:", res.status, "rounds=", res.rounds, "report size=", len(res.residual_leak_report))


def test_phase1_then_strengthen():
    res = run_case(4, [0.02] * 4, initial_R=0.7)
    assert res.status == "PASS", res
    assert res.R >= TAU_R
    print("test_phase1_then_strengthen OK:", res.status, "rounds=", res.rounds)


def test_no_regression_below_gate():
    res = run_case(6, [0.05, 0.05, 0.05, 0.4, 0.4, 0.4])
    for h in res.history:
        if h["phase"] == "strengthen":
            assert h["R"] >= TAU_R, h
    print("test_no_regression_below_gate OK:", res.status)


def test_zero_hit_feasibility():
    n = 5
    probes = probes_per_attr(n)
    from metrics import wilson_upper
    assert wilson_upper(0, probes * n) <= TAU_L
    print("test_zero_hit_feasibility OK: probes_per_attr =", probes, "n_probes =", probes * n)


def test_phase1_no_progress_exits():
    n = 4
    S = [f"s{i}" for i in range(n)]

    def dehydrate(X, S_, P):
        return {"leak": [0.9] * n, "R": 0.5}

    def loosen(D, X, S_, P):
        return {"leak": D["leak"][:], "R": D["R"]}

    def strengthen(D, s, X, S_, P):
        return None

    def evaluate(D, Q, S_, X):
        return {"hits": 10, "n_probes": 60, "U": 0.8, "R": D["R"]}

    def leak_contrib(D, S_):
        return {s: 0.9 for s in S_}

    res = lexicographic_loop("X", S, ["q"], None, dehydrate, strengthen, loosen,
                             evaluate, leak_contrib, tau_l=TAU_L, tau_u=TAU_U,
                             tau_r=TAU_R, n_stable=1)
    assert res.status == "INFEASIBLE"
    assert res.rounds <= 2 + n, res.rounds
    print("test_phase1_no_progress_exits OK: rounds =", res.rounds)


if __name__ == "__main__":
    test_zero_hit_feasibility()
    test_feasible()
    test_infeasible()
    test_phase1_then_strengthen()
    test_no_regression_below_gate()
    test_phase1_no_progress_exits()
    print("ALL LOOP TESTS PASSED")
