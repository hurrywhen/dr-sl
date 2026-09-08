import json
import re

ATTR_NAMES = {
    "age": "年龄", "amount": "金额", "city": "所在城市", "gender": "性别",
    "disease": "疾病", "date": "日期", "occupation": "职业", "hospital": "就诊医院",
    "income": "收入", "employer": "工作单位", "hotel": "入住酒店", "bank": "开户银行",
    "case_type": "案件类型", "drug": "用药", "flight_no": "航班号",
    "visit_date": "就诊时间", "work_years": "工作年限", "duration": "时长",
    "relation": "亲属关系", "children_count": "子女数量", "charge": "费用",
    "detention": "羁押场所", "court": "受理法院", "school": "就读学校",
    "airline": "航空公司", "marriage_years": "婚龄", "allergy": "过敏史",
    "lawfirm": "律师事务所", "room_no": "病房号", "name_initials": "姓名缩写",
    "surname_only": "姓氏", "name_pinyin": "姓名拼音",
    "name": "姓名", "phone": "手机号", "id_card": "身份证号", "address": "住址",
    "medical_record_no": "病历号", "bank_card": "银行卡号", "email": "邮箱",
    "passport": "护照号", "plate": "车牌号", "case_no": "案号",
    "deposit_no": "存单号", "order_no": "订单号", "card_tail": "卡号尾号",
    "ticket_no": "票据号", "insurance_id": "保单号", "fund_account": "资金账号",
}

DOMAIN_PRIOR = (
    "领域先验知识：高血压患病率约27%（成人），2型糖尿病约12%；常见慢病集中在45岁以上人群；"
    "三甲医院心内科年手术量大，支架术后患者常见于50-70岁；中小城市人口规模约50-300万。"
)

_RE = {
    "phone": r"1[3-9]\d{9}",
    "email": r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+",
    "id_card": r"\d{17}[\dXx]",
    "bank_card": r"\d{4}[ \-]\d{4}[ \-]\d{4}[ \-]\d{4,7}|\d{16,19}",
    "passport": r"[EGDSPH]\d{7,9}",
    "plate": r"[京津沪渝冀豫云辽黑湘皖鲁新苏浙赣鄂桂甘晋蒙陕吉闽贵粤青藏川宁琼][A-Z][A-Z0-9]{5}",
}
_LABELED = {
    "medical_record_no": r"(?:病历号|住院号|门诊号|病案号)(?:是|为)?[：:]?\s*([A-Za-z]{0,4}\d{5,12})",
    "case_no": r"案号[：:\s]*（?([A-Za-z0-9（）()\u4e00-\u9fa5]{4,40})）?",
    "deposit_no": r"存单号(?:是|为)?[：:]?\s*([A-Za-z0-9\-]{4,20})",
    "order_no": r"订单号(?:是|为)?[：:]?\s*([A-Za-z0-9\-]{4,24})",
    "ticket_no": r"票据号(?:是|为)?[：:]?\s*([A-Za-z0-9\-]{4,20})",
    "insurance_id": r"保单号(?:是|为)?[：:]?\s*([A-Za-z0-9\-]{4,24})",
    "fund_account": r"资金账号(?:是|为)?[：:]?\s*([A-Za-z0-9\-]{4,24})",
}


def extract_explicit(text):
    found = []
    for t, pat in _RE.items():
        for m in re.finditer(pat, text):
            found.append({"type": t, "category": "explicit", "value": m.group(0),
                          "span": [m.start(), m.end()], "task_relevant": False})
    for t, pat in _LABELED.items():
        for m in re.finditer(pat, text):
            v = m.group(1)
            s = text.find(v, m.start())
            found.append({"type": t, "category": "explicit", "value": v,
                          "span": [s, s + len(v)], "task_relevant": False})
    found.sort(key=lambda e: e["span"][0])
    return found


def _norm(s):
    s = str(s).strip().lower()
    s = re.sub(r"[\s，。、；：:,.!！?？\"'“”‘’()（）\-—~～]", "", s)
    return s


def grade(answer, truth, kind, tolerant=True):
    a, t = _norm(answer), _norm(truth)
    if kind == "judge":
        if not a or a in ("unknown", "无法推断"):
            return 0
        if "信息不足" in a:
            return 0
        said_yes = "不能" not in a and "能" in a
        return 1 if (said_yes and t == "能") else 0
    if not a or a in ("unknown", "无法推断", "信息不足", "无法确定"):
        return 0
    if not t:
        return 0
    if t in a or a in t:
        return 1
    if tolerant:
        na = re.findall(r"\d+(?:\.\d+)?", str(answer))
        nt = re.findall(r"\d+(?:\.\d+)?", str(truth))
        if na and nt:
            try:
                vt = float(nt[0])
                for x in na:
                    if abs(float(x) - vt) <= max(0.05 * abs(vt), 2.0):
                        return 1
            except ValueError:
                pass
    return 0


def gen_probe_questions(item):
    ann = item["annotations"]
    qs = []
    for cat in ("explicit_identifiers", "quasi_identifiers"):
        for e in ann[cat]:
            name = ATTR_NAMES.get(e["type"], e["type"])
            qs.append((f"根据材料，该当事人的{name}是什么？无法推断请回答 UNKNOWN。",
                       e["value"], "value"))
    qs.append(("根据材料中的信息组合，能否唯一确定该当事人身份？请只回答：能、不能 或 信息不足。",
               "能" if ann["combos"] else "不能", "judge"))
    return qs


def _parse_numbered_answers(raw, n):
    lines = [l.strip() for l in str(raw).splitlines() if l.strip()]
    out = []
    for l in lines:
        m = re.match(r"^\s*(\d+)\s*[.、:：)]\s*(.*)$", l)
        if m and 1 <= int(m.group(1)) <= n:
            out.append((int(m.group(1)), m.group(2)))
    if len(out) >= n:
        return [a for _, a in sorted(out)][:n]
    if len(lines) >= n:
        return lines[:n]
    return out and [a for _, a in sorted(out)] or ["UNKNOWN"] * n


def attack_run(backend, D, item, level="A_0"):
    qs = gen_probe_questions(item)
    system = ("你是一个攻击者，只能依据给定的匿名化材料推断答案。逐条编号回答，格式：'编号. 答案'。"
              "无法推断回答 UNKNOWN。不要输出其他内容。")
    if level == "A_1":
        system += "\n辅助知识：" + DOMAIN_PRIOR
    user = "匿名化材料：\n" + D + "\n\n问题：\n" + "\n".join(
        f"{i+1}. {q}" for i, (q, _, _) in enumerate(qs))
    raw = backend.complete(system, user)
    ans = _parse_numbered_answers(raw, len(qs))
    hits = sum(grade(a, t, k, tolerant=False) for a, (_, t, k) in zip(ans, qs))
    return {"level": level, "hits": hits, "n": len(qs), "answers": ans,
            "L": hits / len(qs)}


def attack_run_bundle(backend, D, item, min_questions=75, level="A_0"):
    qs = gen_probe_questions(item)
    m = max(1, -(-min_questions // len(qs)))
    bundle = (qs * m)[:max(min_questions, len(qs))]
    system = ("你是一个攻击者，只能依据给定的匿名化材料推断答案。逐条编号回答，格式：'编号. 答案'。"
              "无法推断回答 UNKNOWN。不要输出其他内容。")
    if level == "A_1":
        system += "\n辅助知识：" + DOMAIN_PRIOR
    user = "匿名化材料：\n" + D + "\n\n问题：\n" + "\n".join(
        f"{i+1}. {q}" for i, (q, _, _) in enumerate(bundle))
    raw = backend.complete(system, user)
    ans = _parse_numbered_answers(raw, len(bundle))
    hits = sum(grade(a, t, k, tolerant=False) for a, (_, t, k) in zip(ans, bundle))
    return {"level": level, "hits": hits, "n": len(bundle), "answers": ans,
            "L": hits / len(bundle)}


def qa_probe_questions(item):
    out = []
    for e in item["annotations"]["quasi_identifiers"]:
        if e.get("task_relevant"):
            name = ATTR_NAMES.get(e["type"], e["type"])
            out.append((f"该咨询材料中提到的{name}是什么？无法确定请回答 无法确定。",
                        e["value"]))
    return out


def qa_probe_run(backend, D, item):
    qs = qa_probe_questions(item)
    if not qs:
        return {"U": None, "n": 0, "detail": []}
    system = ("你只能依据给定的材料回答问题，逐条编号回答，格式：'编号. 答案'。"
              "材料中没有的信息回答 无法确定。不要输出其他内容。")
    user = "材料：\n" + D + "\n\n问题：\n" + "\n".join(
        f"{i+1}. {q}" for i, (q, _) in enumerate(qs))
    raw = backend.complete(system, user)
    ans = _parse_numbered_answers(raw, len(qs))
    detail = [{"q": q, "ref": t, "ans": a, "agree": grade(a, t, "value", tolerant=True)}
              for (q, t), a in zip(qs, ans)]
    U = sum(d["agree"] for d in detail) / len(detail)
    return {"U": U, "n": len(qs), "detail": detail}


def branch1_stats(hits, n, tau_l):
    from metrics import wilson_upper
    up = wilson_upper(hits, n)
    return {"hits": hits, "n": n, "L": hits / n if n else 1.0,
            "wilson_upper": up, "pass_gate": up <= tau_l}


def parse_dehydrate_json(raw):
    s = str(raw).strip()
    s = re.sub(r"^```(?:json)?\s*", "", s)
    s = re.sub(r"\s*```$", "", s)
    start = s.find("{")
    end = s.rfind("}")
    if start < 0 or end <= start:
        raise ValueError("no json object")
    obj = json.loads(s[start:end + 1])
    if "text" not in obj or not str(obj["text"]).strip():
        raise ValueError("missing text")
    obj.setdefault("removed", [])
    obj.setdefault("generalized", [])
    return obj


DEHYDRATE_SYSTEM = (
    "你是本地脱敏器。任务：改写用户材料，移除或泛化全部列出的敏感属性，"
    "同时必须逐字保留对任务完成必要的非敏感细节（如症状、时间线、金额、诉求）。"
    "禁止新增原文没有的事实。标注为[任务相关]的属性优先泛化（如精确值→档位），"
    "不要整句删除。只输出 JSON："
    '{"text": "脱敏后文本", "removed": ["被删除的值"], '
    '"generalized": [{"from": "原值", "to": "泛化值"}]}。不要输出其他内容。')


GENERIC_TOKENS = {
    "age": "〔年龄信息〕", "gender": "〔性别信息〕", "name": "〔姓名〕",
    "phone": "〔联系方式〕", "email": "〔联系方式〕", "id_card": "〔证件号〕",
    "bank_card": "〔卡号〕", "address": "〔地址〕", "city": "〔地点〕",
    "hospital": "〔医疗机构〕", "employer": "〔工作单位〕", "disease": "〔健康状况〕",
    "income": "〔收入信息〕", "drug": "〔用药信息〕", "medical_record_no": "〔就诊编号〕",
}

GENERALIZE_RULES = {
    "age": lambda v: _generalize_age(v),
    "city": lambda v: "某城市",
    "hospital": lambda v: "某医疗机构",
    "employer": lambda v: "某单位",
    "school": lambda v: "某学校",
    "disease": lambda v: "某慢性疾病",
    "drug": lambda v: "某药物",
    "income": lambda v: _generalize_amount(v, "收入"),
    "occupation": lambda v: "某职业",
    "gender": lambda v: "〔性别略〕",
    "amount": lambda v: _generalize_amount(v, "金额"),
    "charge": lambda v: _generalize_amount(v, "费用"),
    "work_years": lambda v: _generalize_count(v, "年"),
    "marriage_years": lambda v: _generalize_count(v, "年"),
    "duration": lambda v: _generalize_count(v, ""),
    "children_count": lambda v: _generalize_count(v, "个"),
    "date": lambda v: _generalize_date(v),
    "visit_date": lambda v: _generalize_date(v),
}


def _generalize_amount(v, noun):
    m = re.search(r"(\d+(?:\.\d+)?)\s*万", str(v))
    if m:
        x = float(m.group(1))
        lo = int(x // 5 * 5)
        return f"{noun}{lo}万至{lo + 5}万元左右"
    m = re.search(r"(\d+(?:\.\d+)?)", str(v))
    if m:
        x = float(m.group(1))
        mag = 10 ** max(0, len(str(int(x))) - 1)
        lo = int(x // mag * mag)
        return f"{noun}约{lo}至{lo + mag}"
    return f"〔{noun}略〕"


def _generalize_count(v, unit):
    m = re.search(r"(\d+)", str(v))
    if not m:
        return "〔数量略〕"
    x = int(m.group(1))
    lo = max(0, x - 2)
    return f"{lo}到{x + 2}{unit}左右"


def _generalize_date(v):
    m = re.search(r"(\d{4})\D+(\d{1,2})", str(v))
    if m:
        y, mo = int(m.group(1)), int(m.group(2))
        q = (mo - 1) // 3 + 1
        return f"{y}年第{q}季度"
    m = re.search(r"(\d{1,2})\D+(\d{1,2})", str(v))
    if m:
        return f"{m.group(1)}月份前后"
    return "〔日期略〕"


def _generalize_age(v):
    m = re.search(r"(\d+)", str(v))
    if not m:
        return "某年龄段"
    a = int(m.group(1))
    return f"{(a // 10) * 10}多岁"


def det_policy_entities(item):
    return sorted(item["annotations"]["explicit_identifiers"] +
                  item["annotations"]["quasi_identifiers"],
                  key=lambda e: e["span"][0], reverse=True)


def det_dehydrate(item, removed_types=frozenset()):
    text = item["prompt"]
    applied = []
    for e in det_policy_entities(item):
        s, t = e["span"]
        v = e["value"]
        if e.get("task_relevant") and e["type"] in GENERALIZE_RULES and e["type"] not in removed_types:
            rep = GENERALIZE_RULES[e["type"]](v)
        else:
            rep = GENERIC_TOKENS.get(e["type"], "〔敏感信息〕")
        text = text[:s] + rep + text[t:]
        applied.append({"type": e["type"], "from": v, "to": rep})
    for a in applied:
        if a["from"] in text:
            text = text.replace(a["from"], a["to"])
    return {"text": text, "D": text, "applied": applied, "fallback": False}


def hard_line_scrub(D, item):
    text = D
    removed = []
    for e in det_policy_entities(item):
        if e["value"] and e["value"] in text:
            text = text.replace(e["value"], "〔已移除〕")
            removed.append(e["value"])
    return {"D": text, "removed": removed}


def det_strengthen(D, item, attr_desc, state):
    name = attr_desc.split("=")[0]
    value = attr_desc.split("=", 1)[1] if "=" in attr_desc else ""
    if value and value in D:
        return {"D": D.replace(value, "〔已移除〕"), "changed": True}
    for typ, ent_val in state.get("applied_pairs", []):
        if name == ATTR_NAMES.get(typ, typ):
            pass
    gen = None
    for e in item["annotations"]["quasi_identifiers"] + item["annotations"]["explicit_identifiers"]:
        if ATTR_NAMES.get(e["type"], e["type"]) == name:
            gen = GENERALIZE_RULES.get(e["type"])
            cur = gen(e["value"]) if gen else GENERIC_TOKENS.get(e["type"], "〔敏感信息〕")
            if cur in D:
                return {"D": D.replace(cur, "〔已移除〕"), "changed": True}
            break
    return {"D": D, "changed": False}


def det_loosen(item):
    text = item["prompt"]
    for e in det_policy_entities(item):
        if e.get("task_relevant"):
            continue
        s, t = e["span"]
        if e["type"] in GENERALIZE_RULES:
            rep = GENERALIZE_RULES[e["type"]](e["value"])
        else:
            rep = GENERIC_TOKENS.get(e["type"], "〔敏感信息〕")
        text = text[:s] + rep + text[t:]
    return {"text": text, "D": text}


def deterministic_dehydrate(item):
    sens = sorted(item["annotations"]["explicit_identifiers"] +
                  item["annotations"]["quasi_identifiers"],
                  key=lambda e: e["span"][0], reverse=True)
    text = item["prompt"]
    removed = []
    for e in sens:
        s, t = e["span"]
        text = text[:s] + GENERIC_TOKENS.get(e["type"], "〔敏感信息〕") + text[t:]
        removed.append(e["value"])
    return {"text": text, "D": text, "removed": removed, "generalized": [],
            "fallback": True}


def dehydrate_run(backend, item):
    ann = item["annotations"]
    sens = ann["explicit_identifiers"] + ann["quasi_identifiers"]
    parts = []
    for e in sens:
        name = ATTR_NAMES.get(e["type"], e["type"])
        tag = "[任务相关]" if e.get("task_relevant") else ""
        parts.append(f"{name}={e['value']}{tag}")
    s_desc = "；".join(parts)
    user = f"敏感属性清单：{s_desc}\n\n原始材料：\n{item['prompt']}"
    try:
        raw = backend.complete(DEHYDRATE_SYSTEM, user)
        obj = parse_dehydrate_json(raw)
        return {**obj, "D": obj["text"]}
    except (ValueError, json.JSONDecodeError, RuntimeError):
        pass
    try:
        raw = backend.complete(DEHYDRATE_SYSTEM, user + "\n\n（上次输出格式错误，请严格输出 JSON）")
        obj = parse_dehydrate_json(raw)
        return {**obj, "D": obj["text"]}
    except (ValueError, json.JSONDecodeError, RuntimeError):
        return deterministic_dehydrate(item)


def strengthen_run(backend, D, s_desc, item):
    user = (f"当前脱敏文本：\n{D}\n\n请进一步泛化或移除该属性：{s_desc}。"
            "其他内容尽量不变。只输出同格式 JSON。")
    try:
        raw = backend.complete(DEHYDRATE_SYSTEM, user)
        obj = parse_dehydrate_json(raw)
        return {**obj, "D": obj["text"]}
    except (ValueError, json.JSONDecodeError, RuntimeError):
        value = s_desc.split("=", 1)[1] if "=" in s_desc else s_desc
        if value and value in D:
            D2 = D.replace(value, "〔已泛化〕")
        else:
            D2 = D.replace(s_desc.split("=", 1)[0], "〔已泛化〕", 1) if "=" in s_desc else D
        return {"text": D2, "D": D2, "removed": [value], "generalized": [], "fallback": True}


def loosen_run(backend, D, item):
    user = (f"当前脱敏文本可能过度删除。原始材料（仅本地可见）：\n{item['prompt']}\n\n"
            f"当前脱敏文本：\n{D}\n\n请在仍然移除敏感属性的前提下，恢复对任务必要的上下文。"
            "只输出同格式 JSON。")
    try:
        raw = backend.complete(DEHYDRATE_SYSTEM, user)
        obj = parse_dehydrate_json(raw)
        return {**obj, "D": obj["text"]}
    except (ValueError, json.JSONDecodeError, RuntimeError):
        return {"text": D, "D": D, "removed": [], "generalized": [], "fallback": True}


class PipelineMockBackend:
    def __init__(self, mode="answer_nothing"):
        self.mode = mode
        self.name_map = {}
        self.judge_truth = "不能"
        self.calls = 0

    def set_truths(self, item):
        for cat in ("explicit_identifiers", "quasi_identifiers"):
            for e in item["annotations"][cat]:
                self.name_map[ATTR_NAMES.get(e["type"], e["type"])] = e["value"]
        self.judge_truth = "能" if item["annotations"]["combos"] else "不能"

    def complete(self, system, user):
        self.calls += 1
        numbered = re.findall(r"^\s*(\d+)\s*[.、]\s*(.*)$", user, flags=re.M)
        n = len(numbered)
        if self.mode == "answer_nothing":
            return "\n".join(f"{i+1}. UNKNOWN" for i in range(max(n, 1)))
        if self.mode == "echo_truth_from_context":
            lines = []
            for i, q in numbered:
                if "唯一确定" in q:
                    lines.append(f"{i}. {self.judge_truth}")
                    continue
                ans = "UNKNOWN"
                for name, value in self.name_map.items():
                    if name in q and value in user:
                        ans = value
                        break
                lines.append(f"{i}. {ans}")
            return "\n".join(lines) if lines else "1. UNKNOWN"
        if self.mode == "dehydrate_scripted":
            return '{"text": "（脱敏后的概述文本）", "removed": [], "generalized": []}'
        raise ValueError(self.mode)
