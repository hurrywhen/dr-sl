import json
import re
from enum import IntEnum

from pipeline import det_dehydrate, det_policy_entities, GENERIC_TOKENS, ATTR_NAMES


class DegradeLevels(IntEnum):
    D0 = 0
    D1 = 1
    D2 = 2
    D3 = 3


def memorization_check(rule, forbidden_values, source_texts, ell=16,
                       gen_scorer=None, gen_min=4):
    for v in forbidden_values:
        if v and str(v) in rule:
            return False, "literal_value"
    for src in source_texts:
        src = str(src)
        L = ell + 1
        for i in range(max(0, len(rule) - L + 1)):
            if rule[i:i + L] in src:
                return False, "long_quote"
    if gen_scorer is not None:
        try:
            score = gen_scorer(rule)
        except Exception:
            return False, "gen_score_error"
        if score < gen_min:
            return False, "gen_score"
    return True, "pass"


def parse_rules(raw):
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
    return [str(x).strip() for x in arr if isinstance(x, str) and str(x).strip()]


DISTILL_SYSTEM = (
    "你是脱敏经验蒸馏器。根据给出的失败统计（仅含属性类型与原因，不含任何具体值），"
    "归纳不超过 5 条通用的脱水改进规则，每条规则必须抽象、可复用、不包含任何具体取值。"
    '只输出 JSON 数组：["规则一…", "规则二…"]。不要输出其他内容。')


def distill_rules(backend, experiences, forbidden_values, source_texts,
                  gen_scorer=None, gen_min=4, max_rules=5):
    from collections import Counter
    causes = Counter((e.get("domain", "?"), e.get("attr_type", "?")) for e in experiences)
    summary = "；".join(f"{d}/{t} 失败 {c} 次" for (d, t), c in causes.most_common(20))
    try:
        raw = backend.complete(DISTILL_SYSTEM, f"失败统计：{summary}")
    except RuntimeError:
        return [], []
    rules = parse_rules(raw)[:max_rules]
    accepted, rejected = [], []
    for r in rules:
        ok, reason = memorization_check(r, forbidden_values, source_texts,
                                        gen_scorer=gen_scorer, gen_min=gen_min)
        (accepted if ok else rejected).append({"rule": r, "reason": reason})
    return accepted, rejected


REFINE_BASE = (
    "你是脱敏精修器。给定一份已做保守脱敏的文本与改进规则，请输出改进后的文本："
    "进一步确保敏感属性不泄漏（按规则泛化或删除），同时逐字保留任务完成所需的非敏感细节，"
    "禁止新增原文没有的事实。只输出 JSON：{\"text\": \"…\"}。不要输出其他内容。")


def build_refine_prompt(rules):
    if not rules:
        return REFINE_BASE
    return REFINE_BASE + "\n改进规则：\n" + "\n".join(f"- {r}" for r in rules)


def _parse_text_json(raw):
    s = str(raw).strip()
    s = re.sub(r"^```(?:json)?\s*", "", s)
    s = re.sub(r"\s*```$", "", s)
    start, end = s.find("{"), s.rfind("}")
    if start < 0 or end <= start:
        return None
    try:
        obj = json.loads(s[start:end + 1])
    except json.JSONDecodeError:
        return None
    t = obj.get("text")
    return str(t) if t and str(t).strip() else None


def _leaks_values(text, item):
    vals = [e["value"] for e in det_policy_entities(item)]
    return [v for v in vals if v in text]


def refine_dehydrate(backend, D0, item, rules):
    prompt = build_refine_prompt(rules)
    user = f"待精修文本：\n{D0}\n\n原始任务语境（仅本地可见）：\n{item['prompt'][:600]}"
    try:
        raw = backend.complete(prompt, user)
    except RuntimeError:
        return D0, False
    t = _parse_text_json(raw)
    if t is None or _leaks_values(t, item):
        return D0, False
    return t, True


def strengthen_llm(backend, D, attr_desc, item, rules):
    prompt = build_refine_prompt(rules)
    user = (f"请在下述文本中进一步泛化或移除属性「{attr_desc}」，其余内容尽量不变。"
            f"\n文本：\n{D}")
    try:
        raw = backend.complete(prompt, user)
    except RuntimeError:
        return None
    t = _parse_text_json(raw)
    if t is None or _leaks_values(t, item):
        return None
    return t


def degrade(item):
    text = item["prompt"]
    ents = det_policy_entities(item)
    d1 = text
    for e in ents:
        if e["category"] == "explicit":
            s, t = e["span"]
            d1 = d1[:s] + GENERIC_TOKENS.get(e["type"], "〔敏感信息〕") + d1[t:]
    d2 = det_dehydrate(item)["D"]
    d3 = text
    for e in ents:
        s, t = e["span"]
        d3 = d3[:s] + "〔已移除〕" + d3[t:]
    return {DegradeLevels.D0: text, DegradeLevels.D1: d1,
            DegradeLevels.D2: d2, DegradeLevels.D3: d3}


def gen_score_prompt_backend(scorer_backend):
    def score(rule):
        raw = scorer_backend.complete(
            "你是规则评审。评估下面这条脱敏规则的通用性与抽象性（1-5 分，5 最好）。"
            "只输出一个数字。", f"规则：{rule}")
        m = re.search(r"[1-5]", str(raw))
        return int(m.group(0)) if m else 1
    return score
