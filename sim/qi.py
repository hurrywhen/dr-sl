import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "dataset"))

import synth_values as sv
from protocol import AGE_BAND, INCOME_BANDS

CITY_IDX = {c: i for i, c in enumerate(sv.CITIES)}
DISEASES = sv.DISEASES_COMMON + sv.DISEASES_RARE
DISEASE_IDX = {d: i for i, d in enumerate(DISEASES)}
OCC_IDX = {o: i for i, o in enumerate(sv.OCCUPATIONS)}
HOSP_IDX = {h: i for i, h in enumerate(sv.HOSPITALS)}

_AGE_RE = re.compile(r"(\d+)\s*岁")
_AGE_MONTH_RE = re.compile(r"(\d+)\s*(?:个月|月龄)")
_NUM_RE = re.compile(r"(\d+(?:\.\d+)?)")


def parse_age(value):
    m = _AGE_RE.search(value)
    if m:
        return int(m.group(1))
    m = _AGE_MONTH_RE.search(value)
    if m:
        return max(0, int(int(m.group(1)) / 12))
    m = _NUM_RE.search(value)
    return int(m.group(1)) if m else None


def income_band(value):
    m = _NUM_RE.search(value)
    if not m:
        return None
    x = float(m.group(1))
    for i, (lo, hi) in enumerate(INCOME_BANDS):
        if lo <= x < hi:
            return i
    return len(INCOME_BANDS) - 1


def normalize_gender(value):
    if "男" in value:
        return 0
    if "女" in value:
        return 1
    return None


def extract_qi(annotations, dims):
    qi = {}
    for q in annotations.get("quasi_identifiers", []):
        t, v = q["type"], q["value"]
        if t == "age" and "age_band" in dims:
            a = parse_age(v)
            if a is not None:
                qi["age_band"] = a // AGE_BAND
        elif t == "gender" and "gender" in dims:
            g = normalize_gender(v)
            if g is not None:
                qi["gender"] = g
        elif t == "city" and "city" in dims:
            if v in CITY_IDX:
                qi["city"] = CITY_IDX[v]
        elif t == "disease" and "disease" in dims:
            if v in DISEASE_IDX:
                qi["disease"] = DISEASE_IDX[v]
        elif t == "occupation" and "occupation" in dims:
            if v in OCC_IDX:
                qi["occupation"] = OCC_IDX[v]
        elif t == "hospital" and "hospital" in dims:
            if v in HOSP_IDX:
                qi["hospital"] = HOSP_IDX[v]
        elif t == "income" and "income_band" in dims:
            b = income_band(v)
            if b is not None:
                qi["income_band"] = b
    return tuple(qi.get(d, -1) for d in dims)


def load_dataset(path):
    import json
    with open(path) as f:
        return [json.loads(line) for line in f]
