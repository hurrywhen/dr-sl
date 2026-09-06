import json
import re

from pipeline import ATTR_NAMES, extract_explicit

TYPE_LIST = "、".join(list(ATTR_NAMES.keys())[:40])

EXTRACT_SYSTEM = (
    "你是敏感信息抽取器。从用户材料中抽取全部显式标识符与准标识符属性，"
    f"类型必须取自词表：{TYPE_LIST}。value 必须是原文逐字片段。"
    '只输出 JSON 数组：[{"type": 类型, "value": 原文片段}]。没有则输出 []。不要输出其他内容。')

CRITIC_SYSTEM = (
    "你是敏感信息抽取复核员。检查给定材料是否还有遗漏的敏感属性"
    "（尤其注意：年龄、性别、疾病、职业、地点、收入、单位、学校、日期等准标识符，"
    "以及姓名、证件号、账号等显式标识符）。把遗漏项与原已抽取项一起完整输出。"
    '只输出 JSON 数组：[{"type": 类型, "value": 原文片段}]。不要输出其他内容。')


def parse_extraction_json(raw, text):
    s = str(raw).strip()
    s = re.sub(r"^```(?:json)?\s*", "", s)
    s = re.sub(r"\s*```$", "", s)
    start, end = s.find("["), s.rfind("]")
    if start < 0 or end <= start:
        return []
    try:
        arr = json.loads(s[start:end + 1])
    except json.JSONDecodeError:
        return []
    out = []
    if not isinstance(arr, list):
        return []
    for e in arr:
        if not isinstance(e, dict):
            continue
        v = str(e.get("value", "")).strip()
        t = str(e.get("type", "")).strip()
        if not v or v not in text:
            continue
        out.append({"type": t or "unknown", "value": v,
                    "category": "quasi" if t in ATTR_NAMES and t not in (
                        "name", "phone", "email", "id_card", "bank_card", "address",
                        "medical_record_no", "passport", "plate", "case_no",
                        "deposit_no", "order_no", "card_tail", "ticket_no",
                        "insurance_id", "fund_account") else "explicit"})
    return out


def _with_rules(system, rules):
    if not rules:
        return system
    return system + "\n抽取改进规则：\n" + "\n".join(f"- {r}" for r in rules)


def llm_layer(backend, text, rules=None):
    try:
        raw1 = backend.complete(_with_rules(EXTRACT_SYSTEM, rules), "材料：\n" + text)
    except RuntimeError:
        raw1 = "[]"
    first = parse_extraction_json(raw1, text)
    known = "、".join(sorted({e["value"] for e in first})) or "（暂无）"
    try:
        raw2 = backend.complete(_with_rules(CRITIC_SYSTEM, rules),
                                f"已抽取：{known}\n\n材料：\n{text}")
    except RuntimeError:
        raw2 = "[]"
    second = parse_extraction_json(raw2, text)
    merged, seen = [], set()
    for e in first + second:
        if e["value"] in seen:
            continue
        seen.add(e["value"])
        idx = text.find(e["value"])
        e["span"] = [idx, idx + len(e["value"])]
        merged.append(e)
    merged.sort(key=lambda e: e["span"][0])
    return merged


def cascade_extract(backend, text, rules=None):
    ents = extract_explicit(text)
    seen = {e["value"] for e in ents}
    for e in llm_layer(backend, text, rules=rules):
        if e["value"] in seen:
            continue
        seen.add(e["value"])
        ents.append(e)
    ents.sort(key=lambda e: e["span"][0])
    return ents


def eval_extraction(found, gold_item):
    found_vals = {e["value"] for e in found}
    rep = {"recall_explicit": None, "recall_quasi": None, "recall_overall": None,
           "missed_values": [], "precision_extra": None}
    gold_all = []
    for cat in ("explicit_identifiers", "quasi_identifiers"):
        gold_all.extend(gold_item["annotations"].get(cat, []))
    gold_vals = {e["value"] for e in gold_all}
    hit = gold_vals & found_vals
    rep["missed_values"] = sorted(gold_vals - found_vals)
    rep["recall_overall"] = len(hit) / len(gold_vals) if gold_vals else 1.0
    for cat, key in (("explicit_identifiers", "recall_explicit"),
                     ("quasi_identifiers", "recall_quasi")):
        gv = {e["value"] for e in gold_item["annotations"].get(cat, [])}
        rep[key] = len(gv & found_vals) / len(gv) if gv else 1.0
    rep["precision_extra"] = len(found_vals - gold_vals)
    return rep
