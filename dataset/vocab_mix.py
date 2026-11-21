"""Vocabulary mixing RNG for natural-drift and dose–response tests (round 3).

A lexicon-dependent draw returns a value from the OLD pool (synth_values) with
probability p_old, else from the NEW disjoint pool (synth_values_v2).  Template
code is unchanged: it calls r.choice(pool) on the v2 pools, and this wrapper
substitutes the corresponding old pool per draw.  Non-lexicon draws (digits,
dates, money amounts) pass through untouched.
"""
import random

import synth_values as old
import synth_values_v2 as new

# holdout-1 used an inline allergy pool (not present in synth_values).
OLD_ALLERGIES = ["海鲜", "花粉", "芒果"]

_PAIRS = [
    (new.SURNAMES, old.SURNAMES), (new.GIVEN, old.GIVEN),
    (new.CITIES, old.CITIES), (new.STREETS, old.STREETS),
    (new.HOSPITALS, old.HOSPITALS), (new.BANKS, old.BANKS),
    (new.COMPANIES, old.COMPANIES), (new.SCHOOLS, old.SCHOOLS),
    (new.HOTELS, old.HOTELS), (new.LAWFIRMS, old.LAWFIRMS),
    (new.COURTS, old.COURTS),
    (new.DISEASES_COMMON, old.DISEASES_COMMON),
    (new.DISEASES_RARE, old.DISEASES_RARE),
    (new.DRUGS, old.DRUGS), (new.OCCUPATIONS, old.OCCUPATIONS),
    (new.INSURANCE_TYPES, old.INSURANCE_TYPES),
    (new.CASE_TYPES, old.CASE_TYPES),
    (new.ALLERGIES, OLD_ALLERGIES),
]

OLD_NAME_POOL = {a + b for a in old.SURNAMES for b in old.GIVEN}
NEW_NAME_POOL = {a + b for a in new.SURNAMES for b in new.GIVEN}

# Gold types whose values are lexicon-dependent (used for realized-overlap stats).
LEXICON_TYPES = {"name", "city", "hospital", "bank", "employer", "school",
                 "hotel", "lawfirm", "court", "disease", "drug", "occupation",
                 "insurance_type", "case_type", "allergy"}

_OLD_LEXICON_VALUES = {
    "name": OLD_NAME_POOL,
    "city": set(old.CITIES), "hospital": set(old.HOSPITALS),
    "bank": set(old.BANKS), "employer": set(old.COMPANIES),
    "school": set(old.SCHOOLS), "hotel": set(old.HOTELS),
    "lawfirm": set(old.LAWFIRMS), "court": set(old.COURTS),
    "disease": set(old.DISEASES_COMMON + old.DISEASES_RARE),
    "drug": set(old.DRUGS), "occupation": set(old.OCCUPATIONS),
    "insurance_type": set(old.INSURANCE_TYPES), "case_type": set(old.CASE_TYPES),
    "allergy": set(OLD_ALLERGIES),
}


def is_old_lexicon_value(typ, value):
    return value in _OLD_LEXICON_VALUES.get(typ, set())


class MixRng:
    """random.Random-compatible wrapper mixing old/new pools per draw."""

    def __init__(self, seed, p_old):
        self.rng = random.Random(seed)
        self.p = p_old
        self.map = {id(n): o for n, o in _PAIRS}

    def choice(self, seq):
        old_seq = self.map.get(id(seq))
        if old_seq is not None and self.rng.random() < self.p:
            return self.rng.choice(old_seq)
        return self.rng.choice(seq)

    def randint(self, a, b):
        return self.rng.randint(a, b)

    def random(self):
        return self.rng.random()
