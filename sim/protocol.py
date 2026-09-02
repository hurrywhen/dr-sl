TAU_L = 0.05
TAU_U = 0.70
TAU_R = 0.90
N_STABLE = 3
DELTA = 0.05
MAX_ROUNDS_FACTOR = 3
MAX_ROUNDS_EXTRA = 5
QUOTE_LEN = 16
GEN_SCORE_MIN = 4
DISTILL_K = 50
K_STAR = 5
TEMPERATURE = 0.3
SEEDS = (20260828, 20260829, 20260830)
PROBES_PER_ATTR = 3
ZERO_HIT_FEASIBLE_PROBES = 75


def min_probes_for(tau_l, z=1.959963984540054):
    import math
    return math.ceil(z * z * (1.0 / tau_l - 1.0))


def probes_per_attr(n_attrs, tau_l=TAU_L):
    import math
    total = max(ZERO_HIT_FEASIBLE_PROBES, min_probes_for(tau_l))
    return math.ceil(total / n_attrs)
N_QA_QUESTIONS = 12
ABSTAIN_SCORE = 0.25
AGE_BAND = 5
INCOME_BANDS = ((0, 5), (5, 10), (10, 30), (30, 60), (60, float("inf")))
POP_SIZE = 1_000_000
POP_SEED = 20260828
PRIMARY_DIMS = ("age_band", "gender", "city", "disease", "occupation")
EXTENDED_DIMS = ("age_band", "gender", "city", "disease", "occupation", "hospital", "income_band")
