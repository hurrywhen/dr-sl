"""Deterministic runtime extractor for the synthetic benchmark track.

This module never reads dataset annotations.  It combines explicit patterns,
public synthetic-domain lexicons, and generic labeled-span rules.  It is an
explicit deterministic local extractor, not a claim of open-world NER recall.
"""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "dataset"))

import synth_values as sv
from pipeline import extract_explicit

_EXPLICIT_TYPES = {
    "name", "phone", "email", "id_card", "bank_card", "address",
    "medical_record_no", "passport", "plate", "case_no", "deposit_no",
    "order_no", "card_tail", "ticket_no", "insurance_id", "fund_account",
}

_LEXICONS = {
    "city": sv.CITIES,
    "hospital": sv.HOSPITALS,
    "bank": sv.BANKS,
    "employer": sv.COMPANIES,
    "school": sv.SCHOOLS,
    "airline": sv.AIRLINES,
    "hotel": sv.HOTELS,
    "lawfirm": sv.LAWFIRMS,
    "court": sv.COURTS,
    "disease": sv.DISEASES_COMMON + sv.DISEASES_RARE,
    "drug": sv.DRUGS,
    "occupation": sv.OCCUPATIONS,
    "insurance_type": sv.INSURANCE_TYPES,
    "case_type": sv.CASE_TYPES,
}
_NAMES = [a + b for a in sv.SURNAMES for b in sv.GIVEN]
_LEXICONS["name"] = _NAMES

_DATE_RE = re.compile(r"\d{4}年\d{1,2}月\d{1,2}日")
_AGE_RE = re.compile(r"\d{1,3}岁")
_MONEY_RE = re.compile(r"\d+(?:\.\d+)?(?:万)?元")
_INCOME_RE = re.compile(r"(?:月|年)收入约?\d+(?:\.\d+)?(?:万)?元")
_ADDRESS_RE = re.compile(
    "(?:" + "|".join(map(re.escape, sv.CITIES)) + ")"
    "(?:" + "|".join(map(re.escape, sv.STREETS)) + ")"
    r"\d{1,3}号\d{1,2}栋\d{3,4}室")

_LABEL_PATTERNS = [
    ("name", r"(?:姓名|当事人|咨询对象|客户|患者|申请人|户名|法人|付款人|收款人|入住人|出差人|学生|孩子|家属)(?:是|为)?[：:（(]?\s*([一-龥]{2,4})"),
    ("age", r"(?:年龄|年纪)[：:]?\s*(\d{1,3}岁)"),
    ("gender", r"(?:性别)[：:]?\s*([男女])"),
    ("medical_record_no", r"(?:病历号|住院号|门诊号|病案号)[：:]?\s*([A-Za-z]{0,4}\d{5,12})"),
    ("case_no", r"案号[：:\s]*[（(]?([A-Za-z0-9（）()一-龥]{4,40})[）)]?"),
    ("deposit_no", r"存单号[：:]?\s*([A-Za-z0-9\-]{4,24})"),
    ("order_no", r"订单号[：:]?\s*([A-Za-z0-9\-]{4,24})"),
    ("ticket_no", r"票据号[：:]?\s*([A-Za-z0-9\-]{4,24})"),
    ("insurance_id", r"(?:保单号|医保卡号)[：:]?\s*([A-Za-z0-9\-]{4,24})"),
    ("fund_account", r"(?:资金账号|公积金账号)[：:]?\s*([A-Za-z0-9\-]{4,24})"),
    ("card_tail", r"(?:卡号尾号|尾号)[：:]?\s*(\d{4})"),
    ("room_no", r"(?:房号|病房号)[：:]?\s*(\d{3,4})"),
    ("work_years", r"(?:工作年限|工作)[：:]?\s*(\d{1,2}年)"),
    ("marriage_years", r"婚龄[：:]?\s*(\d{1,2}年)"),
    ("children_count", r"(?:子女数量|子女)[：:]?\s*(\d{1,2}个)"),
    ("duration", r"(?:时长|行程)[：:]?\s*(\d{1,2}天|[一二三四五六七八九十]+天)"),
    ("flight_no", r"(?:航班号|航班)[：:]?\s*([A-Z]{2}\d{3,4})"),
    ("relation", r"(?:亲属关系|关系)[：:]?\s*(女儿|儿子|配偶|父亲|母亲)"),
    ("allergy", r"(?:过敏史|对)([一-龥]{2,6})(?:过敏)"),
]


def _category(typ):
    return "explicit" if typ in _EXPLICIT_TYPES else "quasi"


def _add(found, typ, value, start, end, source):
    if not value:
        return
    found.append({"type": typ, "value": value, "span": [start, end],
                  "category": _category(typ), "source": source})


def runtime_extract(text):
    found = []
    for e in extract_explicit(text):
        _add(found, e["type"], e["value"], e["span"][0], e["span"][1], "regex")

    for m in _ADDRESS_RE.finditer(text):
        _add(found, "address", m.group(0), m.start(), m.end(), "address_pattern")
    for m in _INCOME_RE.finditer(text):
        _add(found, "income", m.group(0), m.start(), m.end(), "income_pattern")
    for m in _DATE_RE.finditer(text):
        prefix = text[max(0, m.start() - 8):m.start()]
        typ = "visit_date" if any(k in prefix for k in ("就诊", "手术", "入住", "发病")) else "date"
        _add(found, typ, m.group(0), m.start(), m.end(), "date_pattern")
    for m in _AGE_RE.finditer(text):
        _add(found, "age", m.group(0), m.start(), m.end(), "age_pattern")

    for typ, pat in _LABEL_PATTERNS:
        for m in re.finditer(pat, text):
            v = m.group(1)
            s = text.find(v, m.start())
            if s >= 0:
                _add(found, typ, v, s, s + len(v), "label_pattern")

    for typ, values in _LEXICONS.items():
        for v in values:
            start = 0
            while True:
                idx = text.find(v, start)
                if idx < 0:
                    break
                _add(found, typ, v, idx, idx + len(v), "lexicon")
                start = idx + len(v)

    # Prefer longer spans; on ties prefer earlier start.  This avoids counting
    # a city inside an address as a second overlapping entity.
    found.sort(key=lambda e: (-(e["span"][1] - e["span"][0]), e["span"][0], e["type"]))
    kept = []
    occupied = []
    for e in found:
        s, t = e["span"]
        if any(not (t <= a or s >= b) for a, b in occupied):
            continue
        kept.append(e)
        occupied.append((s, t))
    kept.sort(key=lambda e: e["span"][0])
    return kept
