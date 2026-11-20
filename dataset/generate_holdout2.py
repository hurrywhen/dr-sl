"""Frozen disjoint-vocabulary holdout-2 generator (seed 20261121).

Stress test of vocabulary shift: entity values come from synth_values_v2, which
is asserted disjoint from the runtime extractor's lexicons.  Templates are a new
phrasing family (not copies of holdout-1).  Lexicon-dependent quasi-identifiers
(city/hospital/disease/drug/employer/occupation/bank/court/lawfirm) appear in
natural, unlabeled contexts so dictionary lookup cannot recover them.  Annotations
are for external scoring only; runtime policy code must not read them.
"""
import json
import random
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import synth_values_v2 as sv

SEED = 20261121
OUT = Path(__file__).resolve().parent / "output" / "dr_sl_holdout_v2.jsonl"
DOMAINS = ("medical", "banking", "travel", "legal")
PER_DOMAIN = 20

TASK_TYPES = {
    "medical": {"age", "disease", "drug", "allergy"},
    "banking": {"amount", "charge"},
    "travel": {"date", "visit_date", "city"},
    "legal": {"case_type", "amount", "date"},
}


def E(cat, typ, val, rel):
    return {"category": cat, "type": typ, "value": val, "task_relevant": bool(rel)}


def T(s):
    return ("text", s)


def Q(domain, typ, val):
    return E("quasi", typ, val, typ in TASK_TYPES[domain])


def X(typ, val):
    return E("explicit", typ, val, False)


def assemble(parts):
    text, ents = "", []
    for p in parts:
        if isinstance(p, tuple) and p[0] == "text":
            text += p[1]
        else:
            e = p
            s = len(text)
            text += e["value"]
            ents.append({**e, "span": [s, s + len(e["value"])]})
    return text, ents


def med1(r):
    return [T("门诊随访记录。来访者"), X("name", sv.person_name(r)),
            T("，"), Q("medical", "age", f"{sv.age(r)}岁"),
            T("，长期居住在"), Q("medical", "city", r.choice(sv.CITIES)),
            T("，确诊"), Q("medical", "disease", r.choice(sv.DISEASES_COMMON)),
            T("，日常服用"), Q("medical", "drug", r.choice(sv.DRUGS)),
            T("，随访机构为"), Q("medical", "hospital", r.choice(sv.HOSPITALS)),
            T("。联系电话"), X("phone", sv.phone(r)),
            T("。请评估当前方案是否需要调整。")]


def med2(r):
    return [T("健康档案摘要："), X("name", sv.person_name(r)),
            T("，"), Q("medical", "age", f"{r.randint(25, 80)}岁"),
            T("，职业为"), Q("medical", "occupation", r.choice(sv.OCCUPATIONS)),
            T("。近期诊断为"), Q("medical", "disease", r.choice(sv.DISEASES_RARE)),
            T("，对"), Q("medical", "allergy", r.choice(sv.ALLERGIES)),
            T("过敏。联系邮箱"), X("email", sv.email(r)),
            T("。请给出长期管理建议。")]


def med3(r):
    return [T("儿科问诊：患儿"), X("name", sv.person_name(r)),
            T("，"), Q("medical", "age", f"{r.randint(3, 15)}岁"),
            T("，过敏史："), Q("medical", "allergy", r.choice(sv.ALLERGIES)),
            T("，现用"), Q("medical", "drug", r.choice(sv.DRUGS)),
            T("，就诊日期"), Q("medical", "visit_date", sv.date_str(r)),
            T("，病历号"), X("medical_record_no", sv.mrn(r)),
            T("。请分析反复低烧的可能原因。")]


def med4(r):
    return [T("医患对话\n医生：请核对信息。\n患者（"), X("name", sv.person_name(r)),
            T("）：我"), Q("medical", "age", f"{r.randint(45, 85)}岁"),
            T("，在"), Q("medical", "hospital", r.choice(sv.HOSPITALS)),
            T("就诊，时间是"), Q("medical", "visit_date", sv.date_str(r)),
            T("，身份证"), X("id_card", sv.id_card(r)),
            T("。\n医生：请描述症状。\n患者：胸闷气短，活动后加重。")]


def bank1(r):
    return [T("信贷审批表\n申请人："), X("name", sv.person_name(r)),
            T("\n证件号："), X("id_card", sv.id_card(r)),
            T("\n任职于"), Q("banking", "employer", r.choice(sv.COMPANIES)),
            T("\n收入情况："), Q("banking", "income", sv.income(r)),
            T("\n申请金额："), Q("banking", "amount", sv.money(r, 50000, 500000)),
            T("\n常住"), Q("banking", "city", r.choice(sv.CITIES)),
            T("\n联系电话："), X("phone", sv.phone(r)),
            T("\n请评估经营贷通过率。")]


def bank2(r):
    return [T("转账复核：付款人"), X("name", sv.person_name(r)),
            T("，账号"), X("bank_card", sv.bank_card(r)),
            T("，金额"), Q("banking", "amount", sv.money(r, 10000, 300000)),
            T("，日期"), Q("banking", "date", sv.date_str(r)),
            T("，开户行为"), Q("banking", "bank", r.choice(sv.BANKS)),
            T("，手续费"), Q("banking", "charge", sv.money(r, 5, 200)),
            T("。请核对大额转账风控要求。")]


def bank3(r):
    return [T("客服记录\n客户（"), X("name", sv.person_name(r)),
            T("）：信用卡尾号"), X("card_tail", "".join(r.choice("0123456789") for _ in range(4))),
            T("被盗刷，合计"), Q("banking", "amount", sv.money(r, 500, 20000)),
            T("，职业是"), Q("banking", "occupation", r.choice(sv.OCCUPATIONS)),
            T("，预留手机"), X("phone", sv.phone(r)),
            T("。\n客服：请说明诉求。\n客户：希望尽快冻结并追回。")]


def bank4(r):
    return [T("存款代办咨询：户名"), X("name", sv.person_name(r)),
            T("，"), Q("banking", "age", f"{r.randint(60, 90)}岁"),
            T("，存单号"), X("deposit_no", "CD" + "".join(r.choice("0123456789") for _ in range(10))),
            T("，存款金额"), Q("banking", "amount", sv.money(r, 50000, 500000)),
            T("，开户行为"), Q("banking", "bank", r.choice(sv.BANKS)),
            T("，住址"), X("address", sv.address(r)),
            T("。家属能否代办提前支取？")]


def trav1(r):
    return [T("行程预订\n乘客："), X("name", sv.person_name(r)),
            T("\n护照号："), X("passport", sv.passport(r)),
            T("\n出发日期："), Q("travel", "date", sv.date_str(r)),
            T("\n自"), Q("travel", "city", r.choice(sv.CITIES)),
            T("出发\n航班号："), Q("travel", "flight_no", sv.flight_no(r)),
            T("\n入住"), Q("travel", "hotel", r.choice(sv.HOTELS)),
            T("\n联系电话："), X("phone", sv.phone(r)),
            T("\n请检查衔接是否合理。")]


def trav2(r):
    return [T("家庭出游：从"), Q("travel", "city", r.choice(sv.CITIES)),
            T("出发，孩子"), Q("travel", "age", f"{r.randint(3, 12)}岁"),
            T("，子女数量"), Q("travel", "children_count", f"{r.randint(1, 3)}个"),
            T("，行程"), Q("travel", "duration", f"{r.randint(3, 8)}天"),
            T("，预算"), Q("travel", "amount", sv.money(r, 8000, 30000)),
            T("，孩子对"), Q("travel", "allergy", r.choice(sv.ALLERGIES)),
            T("过敏。请推荐轻松路线。")]


def trav3(r):
    return [T("出差报销：出差人"), X("name", sv.person_name(r)),
            T("，单位"), Q("travel", "employer", r.choice(sv.COMPANIES)),
            T("，航班"), Q("travel", "flight_no", sv.flight_no(r)),
            T("，住宿发票金额"), Q("travel", "amount", sv.money(r, 600, 3000)),
            T("，银行卡号"), X("bank_card", sv.bank_card(r)),
            T("，入住"), Q("travel", "hotel", r.choice(sv.HOTELS)),
            T("。超标住宿能否报销？")]


def trav4(r):
    return [T("景区遗失物品\n游客（"), X("name", sv.person_name(r)),
            T("）：身份证"), X("id_card", sv.id_card(r)),
            T("和钱包丢失，住在"), Q("travel", "hotel", r.choice(sv.HOTELS)),
            T("，房号"), Q("travel", "room_no", str(r.randint(301, 1200))),
            T("，接驳车牌"), X("plate", r.choice("京津沪渝冀豫云辽黑湘皖鲁新苏浙赣鄂桂甘晋蒙陕吉闽贵粤青藏川宁琼") + r.choice("ABCDEF") + "".join(r.choice("0123456789") for _ in range(5))),
            T("，电话"), X("phone", sv.phone(r)),
            T("。\n工作人员：请先报警并联系前台。")]


def legal1(r):
    return [T("案件摘要\n当事人："), X("name", sv.person_name(r)),
            T("\n身份证号："), X("id_card", sv.id_card(r)),
            T("\n案件类型："), Q("legal", "case_type", r.choice(sv.CASE_TYPES)),
            T("\n受理法院为"), Q("legal", "court", r.choice(sv.COURTS)),
            T("\n争议金额："), Q("legal", "amount", sv.money(r, 50000, 800000)),
            T("\n立案日期："), Q("legal", "date", sv.date_str(r)),
            T("\n住址："), X("address", sv.address(r)),
            T("\n请整理证据清单。")]


def legal2(r):
    return [T("劳动争议：我是"), Q("legal", "occupation", r.choice(sv.OCCUPATIONS)),
            T("，在"), Q("legal", "employer", r.choice(sv.COMPANIES)),
            T("工作"), Q("legal", "work_years", f"{r.randint(1, 20)}年"),
            T("，"), Q("legal", "income", sv.income(r)),
            T("，被拖欠金额"), Q("legal", "amount", sv.money(r, 10000, 200000)),
            T("，住在"), Q("legal", "city", r.choice(sv.CITIES)),
            T("，电话"), X("phone", sv.phone(r)),
            T("。请问仲裁时效如何计算？")]


def legal3(r):
    return [T("家事案件：申请人"), X("name", sv.person_name(r)),
            T("，婚龄"), Q("legal", "marriage_years", f"{r.randint(2, 30)}年"),
            T("，子女数量"), Q("legal", "children_count", f"{r.randint(0, 3)}个"),
            T("，共同财产争议金额"), Q("legal", "amount", sv.money(r, 100000, 1000000)),
            T("，银行卡号"), X("bank_card", sv.bank_card(r)),
            T("，代理律所"), Q("legal", "lawfirm", r.choice(sv.LAWFIRMS)),
            T("。请说明财产分割的一般原则。")]


def legal4(r):
    return [T("交通事故咨询：当事人"), X("name", sv.person_name(r)),
            T("，车牌"), X("plate", r.choice("京津沪渝冀豫云辽黑湘皖鲁新苏浙赣鄂桂甘晋蒙陕吉闽贵粤青藏川宁琼") + r.choice("ABCDEF") + "".join(r.choice("0123456789") for _ in range(5))),
            T("，案件类型"), Q("legal", "case_type", r.choice(sv.CASE_TYPES)),
            T("，事故日期"), Q("legal", "date", sv.date_str(r)),
            T("，医疗费用"), Q("legal", "amount", sv.money(r, 5000, 100000)),
            T("，就诊于"), Q("legal", "hospital", r.choice(sv.HOSPITALS)),
            T("，保单号"), X("insurance_id", "BX" + "".join(r.choice("0123456789") for _ in range(10))),
            T("。请说明理赔材料。")]


TEMPLATES = {
    "medical": [med1, med2, med3, med4],
    "banking": [bank1, bank2, bank3, bank4],
    "travel": [trav1, trav2, trav3, trav4],
    "legal": [legal1, legal2, legal3, legal4],
}


def load_existing_texts():
    texts = []
    out = Path(__file__).resolve().parent / "output"
    for name in ("dr_sl_dataset_v2.jsonl", "dr_sl_expansion_v1.jsonl",
                 "dr_sl_stage2_stream.jsonl", "dr_sl_mixed.jsonl",
                 "dr_sl_holdout_v1.jsonl"):
        p = out / name
        if p.exists():
            for line in p.open(encoding="utf-8"):
                texts.append(json.loads(line)["prompt"])
    return texts


def main():
    import difflib
    sv.assert_disjoint()
    rng = random.Random(SEED)
    seen = load_existing_texts()
    items = []
    template_counts = Counter()
    for domain in DOMAINS:
        accepted = []
        attempts = 0
        while len(accepted) < PER_DOMAIN and attempts < PER_DOMAIN * 50:
            attempts += 1
            fn = TEMPLATES[domain][attempts % len(TEMPLATES[domain])]
            text, ents = assemble(fn(rng))
            rel = [e for e in ents if e.get("task_relevant")]
            if rel:
                v = rel[attempts % len(rel)]["value"]
                text += f"补充说明：前述{v}情况请以本记录为准。"
            if text in seen:
                continue
            if any(difflib.SequenceMatcher(None, text, s).ratio() >= 0.95 for s in seen[-400:]):
                continue
            seen.append(text)
            accepted.append((text, ents, fn.__name__))
        assert len(accepted) == PER_DOMAIN, domain
        for i, (text, ents, tid) in enumerate(accepted, 1):
            template_counts[f"{domain}/{tid}"] += 1
            ann = {
                "explicit_identifiers": [e for e in ents if e["category"] == "explicit"],
                "quasi_identifiers": [e for e in ents if e["category"] == "quasi"],
                "combos": [],
                "has_quasi_identifier": any(e["category"] == "quasi" for e in ents),
            }
            n_qi = len(ann["quasi_identifiers"])
            n_crit = sum(1 for e in ann["quasi_identifiers"] if e["task_relevant"])
            items.append({
                "id": f"DRSL-H2-{domain[:3].upper()}-{i:04d}",
                "domain": domain,
                "split": "holdout2_frozen",
                "prompt": text,
                "template_id": f"holdout2_{tid}",
                "annotations": ann,
                "coupling_ratio": round(n_crit / n_qi, 3) if n_qi else 0.0,
                "source": "synthetic_disjoint_vocabulary_v2",
                "license": "synthetic-fictional",
                "annotation_meta": {"annotator": "rule_based_task_critical",
                                     "needs_human_review": True,
                                     "frozen_before_evaluation": True},
            })
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", encoding="utf-8") as f:
        for item in items:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")
    print(json.dumps({"total": len(items),
                      "by_domain": dict(Counter(i["domain"] for i in items)),
                      "template_distribution": dict(template_counts),
                      "seed": SEED, "output": str(OUT)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
