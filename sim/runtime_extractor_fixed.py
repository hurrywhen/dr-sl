"""Fixed-contrast runtime extractor (round 3, revision_protocol_v3.md §3).

Fixes ONLY clear implementation defects of the frozen original extractor, with
NO lexicon additions and no tuning on holdout outcomes:

  (a) the money pattern ``_MONEY_RE`` was defined in the original module but
      never applied by ``runtime_extract`` (amount/charge never recovered);
  (b) the email pattern used Python's Unicode ``\\w`` class, which over-matches
      Chinese label prefixes (e.g. "邮箱abc@..." -> value "邮箱abc@...");
      the local part is restricted to ASCII;
  (c) the allergy label rule missed the labeled form "过敏史：X", and the
      "孩子/患者" name-label rule collided with "对X过敏" (the name span
      swallowed the allergy span); a negative lookahead prevents a name
      capture starting with the preposition 对.

The original ``runtime_extractor.py`` remains frozen and unchanged; all
round-1/2 results stand.  This variant is validated confirmatorily on the new
holdout-3 only (holdout-1/2 runs are diagnostic, since the defects were
discovered there).
"""
import re

from runtime_extractor import (_AGE_RE, _DATE_RE, _INCOME_RE, _LABEL_PATTERNS,
                               _LEXICONS, _MONEY_RE, _add, runtime_extract)
from pipeline import extract_explicit

_EMAIL_FIXED_RE = re.compile(r"[A-Za-z0-9._+-]+@[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)+")
_ALLERGY_LABELED_RE = re.compile(r"过敏史[：:]\s*([一-龥]{2,6})")
_CHARGE_PREFIX = ("手续费", "费用", "收费", "工本费")

# Name-label rule with the 对-collision fix (defect c).
_LABEL_PATTERNS_FIXED = [
    (typ, pat.replace("([一-龥]{2,4})", "((?!对)[一-龥]{2,4})")
     if typ == "name" else pat)
    for typ, pat in _LABEL_PATTERNS
]


def runtime_extract_fixed(text):
    found = []
    for e in extract_explicit(text):
        if e["type"] == "email":
            continue  # replaced by the ASCII-local-part pattern below
        _add(found, e["type"], e["value"], e["span"][0], e["span"][1], "regex")

    # (b) ASCII email local part.
    for m in _EMAIL_FIXED_RE.finditer(text):
        _add(found, "email", m.group(0), m.start(), m.end(), "email_fixed")

    # Address pattern is lexicon-based and unchanged; reuse original behavior by
    # re-running the original extractor's address matches via its module regex.
    import runtime_extractor as _orig
    for m in _orig._ADDRESS_RE.finditer(text):
        _add(found, "address", m.group(0), m.start(), m.end(), "address_pattern")
    for m in _INCOME_RE.finditer(text):
        _add(found, "income", m.group(0), m.start(), m.end(), "income_pattern")
    for m in _DATE_RE.finditer(text):
        prefix = text[max(0, m.start() - 8):m.start()]
        typ = "visit_date" if any(k in prefix for k in ("就诊", "手术", "入住", "发病")) else "date"
        _add(found, typ, m.group(0), m.start(), m.end(), "date_pattern")
    for m in _AGE_RE.finditer(text):
        _add(found, "age", m.group(0), m.start(), m.end(), "age_pattern")

    # (a) wire the money pattern; charge vs amount by label context.
    for m in _MONEY_RE.finditer(text):
        prefix = text[max(0, m.start() - 6):m.start()]
        typ = "charge" if any(k in prefix for k in _CHARGE_PREFIX) else "amount"
        _add(found, typ, m.group(0), m.start(), m.end(), "money_pattern")

    for typ, pat in _LABEL_PATTERNS_FIXED:
        for m in re.finditer(pat, text):
            v = m.group(1)
            s = text.find(v, m.start())
            if s >= 0:
                _add(found, typ, v, s, s + len(v), "label_pattern")

    # (c) labeled allergy form.
    for m in _ALLERGY_LABELED_RE.finditer(text):
        v = m.group(1)
        s = text.find(v, m.start())
        if s >= 0:
            _add(found, "allergy", v, s, s + len(v), "label_pattern")

    for typ, values in _LEXICONS.items():
        for v in values:
            start = 0
            while True:
                idx = text.find(v, start)
                if idx < 0:
                    break
                _add(found, typ, v, idx, idx + len(v), "lexicon")
                start = idx + len(v)

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
