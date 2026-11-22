"""Holdout-4 generator (round 5, seed 20261125): natural vocabulary mix,
NEW template family #4.

Pre-registered in revision_protocol_v5.md §4 BEFORE any h4 result is inspected.
80 instances (20/domain, 2 templates/domain x 10 accepted draws).  Values are
drawn from the v2 pools through MixRng(p_old=0.5) — the same natural-drift
mechanism as holdout-3.  The templates deliberately include the three gold types
omitted by the round-4 neural taxonomy (room_no, work_years, marriage_years) so
that the complete-taxonomy validation is non-vacuous, plus income phrasings and
city mentions.  Explicit verbatim task field; annotations for external scoring
only.  Validation set for the taxonomy-completion contrast (protocol v5 §4);
NOT used to design or amend any prompt.
"""
import json
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import synth_values_v2 as sv
from vocab_mix import MixRng, is_old_lexicon_value, LEXICON_TYPES

SEED = 20261125
P_OLD = 0.5
OUT = Path(__file__).resolve().parent / "output" / "dr_sl_holdout_v4.jsonl"
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


def h4med1(r):
    return [T("复诊评估备忘：患者"), X("name", sv.person_name(r)),
            T("，"), Q("medical", "age", f"{sv.age(r)}岁"),
            T("，家住"), Q("medical", "city", r.choice(sv.CITIES)),
            T("，确诊"), Q("medical", "disease", r.choice(sv.DISEASES_COMMON)),
            T("，长期服用"), Q("medical", "drug", r.choice(sv.DRUGS)),
            T("，过敏史："), Q("medical", "allergy", r.choice(sv.ALLERGIES)),
            T("，最近一次就诊"), Q("medical", "visit_date", sv.date_str(r)),
            T("于"), Q("medical", "hospital", r.choice(sv.HOSPITALS)),
            T("，联系电话"), X("phone", sv.phone(r)),
            T("。请评估当前用药方案是否需要调整。")]


def h4med2(r):
    return [T("在线复诊对话\n患者：医生您好，我是"), X("name", sv.person_name(r)),
            T("，今年"), Q("medical", "age", f"{r.randint(25, 80)}岁"),
            T("，住在"), Q("medical", "city", r.choice(sv.CITIES)),
            T("，确诊"), Q("medical", "disease", r.choice(sv.DISEASES_RARE)),
            T("，职业是"), Q("medical", "occupation", r.choice(sv.OCCUPATIONS)),
            T("，目前在服"), Q("medical", "drug", r.choice(sv.DRUGS)),
            T("，邮箱"), X("email", sv.email(r)),
            T("。\n医生：收到，请说明诉求。\n患者：请给出后续复查和用药的建议。")]


def h4bank1(r):
    return [T("授信调查备忘：客户"), X("name", sv.person_name(r)),
            T("，证件号"), X("id_card", sv.id_card(r)),
            T("，任职于"), Q("banking", "employer", r.choice(sv.COMPANIES)),
            T("，工作年限"), Q("banking", "work_years", f"{r.randint(1, 20)}年"),
            T("，收入情况"), Q("banking", "income", sv.income(r)),
            T("，申请经营贷"), Q("banking", "amount", sv.money(r, 50000, 500000)),
            T("，常住"), Q("banking", "city", r.choice(sv.CITIES)),
            T("，预留手机"), X("phone", sv.phone(r)),
            T("。请评估这笔经营贷的通过率。")]


def h4bank2(r):
    return [T("电话银行记录\n客户：我是"), X("name", sv.person_name(r)),
            T("，账号"), X("bank_card", sv.bank_card(r)),
            T("，卡尾号"), X("card_tail", "".join(r.choice("0123456789") for _ in range(4))),
            T("，"), Q("banking", "date", sv.date_str(r)),
            T("转了"), Q("banking", "amount", sv.money(r, 10000, 300000)),
            T("，开户行"), Q("banking", "bank", r.choice(sv.BANKS)),
            T("，被收了"), Q("banking", "charge", sv.money(r, 5, 200)),
            T("手续费。\n客服：请问有什么可以帮您？\n客户：请帮我核对这笔转账的风控要求。")]


def h4trav1(r):
    return [T("行程核验备忘：旅客"), X("name", sv.person_name(r)),
            T("，护照号"), X("passport", sv.passport(r)),
            T("，"), Q("travel", "date", sv.date_str(r)),
            T("自"), Q("travel", "city", r.choice(sv.CITIES)),
            T("出发，航班"), Q("travel", "flight_no", sv.flight_no(r)),
            T("，入住"), Q("travel", "hotel", r.choice(sv.HOTELS)),
            T("，房号"), Q("travel", "room_no", str(r.randint(301, 1200))),
            T("，联系电话"), X("phone", sv.phone(r)),
            T("。请检查行程衔接是否合理。")]


def h4trav2(r):
    return [T("家庭出游需求：打算从"), Q("travel", "city", r.choice(sv.CITIES)),
            T("出发玩"), Q("travel", "duration", f"{r.randint(3, 8)}天"),
            T("，孩子"), Q("travel", "age", f"{r.randint(3, 12)}岁"),
            T("，共"), Q("travel", "children_count", f"{r.randint(1, 3)}个"),
            T("孩子，预算"), Q("travel", "amount", sv.money(r, 8000, 30000)),
            T("，孩子对"), Q("travel", "allergy", r.choice(sv.ALLERGIES)),
            T("过敏。请推荐轻松路线。")]


def h4legal1(r):
    return [T("案件办理备忘：当事人"), X("name", sv.person_name(r)),
            T("，身份证号"), X("id_card", sv.id_card(r)),
            T("，案由"), Q("legal", "case_type", r.choice(sv.CASE_TYPES)),
            T("，由"), Q("legal", "court", r.choice(sv.COURTS)),
            T("受理，争议金额"), Q("legal", "amount", sv.money(r, 50000, 800000)),
            T("，立案日期"), Q("legal", "date", sv.date_str(r)),
            T("，住址"), X("address", sv.address(r)),
            T("。请整理本案证据清单。")]


def h4legal2(r):
    return [T("家事咨询对话\n当事人：我是"), X("name", sv.person_name(r)),
            T("，婚龄"), Q("legal", "marriage_years", f"{r.randint(2, 30)}年"),
            T("，子女数量"), Q("legal", "children_count", f"{r.randint(0, 3)}个"),
            T("，共同财产争议金额"), Q("legal", "amount", sv.money(r, 100000, 1000000)),
            T("，银行卡号"), X("bank_card", sv.bank_card(r)),
            T("，代理律所"), Q("legal", "lawfirm", r.choice(sv.LAWFIRMS)),
            T("，住在"), Q("legal", "city", r.choice(sv.CITIES)),
            T("。\n律师：请说明诉求。\n当事人：请说明财产分割的一般原则。")]


TEMPLATES = {
    "medical": [h4med1, h4med2],
    "banking": [h4bank1, h4bank2],
    "travel": [h4trav1, h4trav2],
    "legal": [h4legal1, h4legal2],
}

TASKS = {
    "h4med1": "请评估当前用药方案是否需要调整。",
    "h4med2": "请给出后续复查和用药的建议。",
    "h4bank1": "请评估这笔经营贷的通过率。",
    "h4bank2": "请帮我核对这笔转账的风控要求。",
    "h4trav1": "请检查行程衔接是否合理。",
    "h4trav2": "请推荐轻松路线。",
    "h4legal1": "请整理本案证据清单。",
    "h4legal2": "请说明财产分割的一般原则。",
}


def check_task(task, text, ents, tid):
    assert task and task != text, f"task equals prompt for {tid}"
    assert len(task) <= 0.5 * len(text), f"task too long for {tid}"
    for e in ents:
        assert e["value"] not in task, f"task leaks gold value for {tid}"
    assert task in text, f"task not verbatim in prompt for {tid}"


def load_existing_texts():
    texts = []
    out = Path(__file__).resolve().parent / "output"
    for name in ("dr_sl_dataset_v2.jsonl", "dr_sl_expansion_v1.jsonl",
                 "dr_sl_stage2_stream.jsonl", "dr_sl_mixed.jsonl",
                 "dr_sl_holdout_v1.jsonl", "dr_sl_holdout_v2.jsonl",
                 "dr_sl_holdout_v3.jsonl",
                 "dr_sl_drift_p000.jsonl", "dr_sl_drift_p025.jsonl",
                 "dr_sl_drift_p050.jsonl", "dr_sl_drift_p075.jsonl",
                 "dr_sl_drift_p100.jsonl"):
        p = out / name
        if p.exists():
            for line in p.open(encoding="utf-8"):
                texts.append(json.loads(line)["prompt"])
    return texts


def main():
    import difflib
    rng = MixRng(SEED, P_OLD)
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
            task = TASKS[tid]
            check_task(task, text, ents, tid)
            template_counts[f"{domain}/{tid}"] += 1
            ann = {
                "explicit_identifiers": [e for e in ents if e["category"] == "explicit"],
                "quasi_identifiers": [e for e in ents if e["category"] == "quasi"],
                "combos": [],
                "has_quasi_identifier": any(e["category"] == "quasi" for e in ents),
            }
            n_qi = len(ann["quasi_identifiers"])
            n_crit = sum(1 for e in ann["quasi_identifiers"] if e["task_relevant"])
            lex = [e for e in ann["quasi_identifiers"] + ann["explicit_identifiers"]
                   if e["type"] in LEXICON_TYPES]
            realized = (sum(1 for e in lex if is_old_lexicon_value(e["type"], e["value"]))
                        / len(lex)) if lex else None
            items.append({
                "id": f"DRSL-H4-{domain[:3].upper()}-{i:04d}",
                "domain": domain,
                "split": "holdout4_frozen",
                "prompt": text,
                "task": task,
                "task_meta": {"source": "verbatim_request"},
                "template_id": f"holdout4_{tid}",
                "annotations": ann,
                "coupling_ratio": round(n_crit / n_qi, 3) if n_qi else 0.0,
                "nominal_old_vocab_prob": P_OLD,
                "realized_old_vocab_fraction": round(realized, 3) if realized is not None else None,
                "source": "synthetic_natural_vocab_mix_v4",
                "license": "synthetic-fictional",
                "annotation_meta": {"annotator": "rule_based_task_critical",
                                     "needs_human_review": True,
                                     "frozen_before_evaluation": True},
            })
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", encoding="utf-8") as f:
        for item in items:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")
    lex_all = [e for it in items
               for e in it["annotations"]["quasi_identifiers"] + it["annotations"]["explicit_identifiers"]
               if e["type"] in LEXICON_TYPES]
    overall = sum(1 for e in lex_all if is_old_lexicon_value(e["type"], e["value"])) / len(lex_all)
    type_counts = Counter(e["type"] for it in items
                          for e in it["annotations"]["quasi_identifiers"] + it["annotations"]["explicit_identifiers"])
    print(json.dumps({"total": len(items),
                      "by_domain": dict(Counter(i["domain"] for i in items)),
                      "template_distribution": dict(template_counts),
                      "nominal_p_old": P_OLD,
                      "realized_old_vocab_fraction": round(overall, 3),
                      "previously_omitted_type_counts": {t: type_counts[t]
                                                         for t in ("room_no", "work_years", "marriage_years")},
                      "seed": SEED, "output": str(OUT)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
