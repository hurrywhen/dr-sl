import json
import sys
from collections import Counter

LOCALIZERS = {"city", "employer", "school", "hospital", "detention"}
ATTRIBUTES = {"age", "gender", "occupation", "disease", "income", "charge", "case_type"}
CONTACT_TYPES = {"phone", "id_card", "email", "address", "bank_card", "passport",
                 "medical_record_no", "insurance_id", "case_no", "order_no", "ticket_no",
                 "deposit_no", "fund_account", "card_tail", "plate"}
CLINICAL_TYPES = {"disease", "drug", "allergy", "age", "gender"}
INITIALS_TYPES = {"name_initials", "name_pinyin", "surname_only"}
INSTITUTION_TYPES = {"bank", "hospital", "hotel", "airline", "court", "lawfirm"}
GENERIC_TEMPLATES = {"med_t11", "bank_t07", "legal_t08"}


def audit_item(it, issues):
    iid = it["id"]
    ann = it["annotations"]
    explicits = ann["explicit_identifiers"]
    quasis = ann["quasi_identifiers"]
    allents = explicits + quasis

    spans = sorted((e["span"][0], e["span"][1], e["type"]) for e in allents)
    for (s1, t1, ty1), (s2, t2, ty2) in zip(spans, spans[1:]):
        if s2 < t1:
            issues.append(f"[{iid}] span 重叠: {ty1}@{s1}-{t1} 与 {ty2}@{s2}-{t2}")

    for e in explicits:
        if e["type"] in CONTACT_TYPES and e["task_relevant"]:
            issues.append(f"[{iid}] 联系/证件类 {e['type']} 不应 task_relevant=true（手册§三）")
        if e["type"] in INITIALS_TYPES:
            issues.append(f"[{iid}] {e['type']} 判 explicit 需组合定级依据（手册§2.3.1）")

    adv = it["annotation_meta"].get("adversarial_type")
    if it["domain"] == "medical" and adv != "over_disclosure_request":
        for e in quasis:
            if e["type"] in CLINICAL_TYPES and not e["task_relevant"] and e["type"] in {"disease", "drug", "allergy"}:
                issues.append(f"[{iid}] 临床实体 {e['type']} 应 task_relevant=true（手册§三）")

    if adv == "over_redaction_trap" and not any(e["task_relevant"] for e in allents):
        issues.append(f"[{iid}] over_redaction_trap 缺少 task_relevant=true 实体（手册§五）")

    if it["template_id"] in GENERIC_TEMPLATES and ann["combos"]:
        issues.append(f"[{iid}] 泛化知识问答不应标 combo（手册§4.4）")

    qtypes = {e["type"] for e in quasis}
    expect_combo = len(quasis) >= 2 and qtypes & LOCALIZERS and qtypes & ATTRIBUTES \
        and it["template_id"] not in GENERIC_TEMPLATES
    if expect_combo and not ann["combos"]:
        issues.append(f"[{iid}] 应标 combo 而未标（定位性+属性类准标识符 ≥2）")
    if not expect_combo and ann["combos"]:
        issues.append(f"[{iid}] 不应标 combo 而标了（缺定位性/属性组合或为泛化问答）")

    seen_sets = set()
    for c in ann["combos"]:
        key = tuple(sorted(tuple(m) for m in c["members"]))
        if key in seen_sets:
            issues.append(f"[{iid}] combo 成员集合重复（手册§4.5）")
        seen_sets.add(key)
        member_spans = {tuple(m) for m in c["members"]}
        entity_spans = {tuple(e["span"]) for e in quasis}
        if not member_spans <= entity_spans:
            issues.append(f"[{iid}] combo 成员 span 不在准标识符列表中")

    for e in quasis:
        if e["type"] in INSTITUTION_TYPES and not explicits and len(quasis) == 1:
            issues.append(f"[{iid}] 孤立机构名 {e['type']} 是否与个人事件绑定存疑（手册§2.3.2）")

    if not allents:
        issues.append(f"[{iid}] 无任何敏感实体标注")


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else "output/dr_sl_dataset_v2.jsonl"
    items, issues = [], []
    with open(path, encoding="utf-8") as f:
        for line in f:
            if line.strip():
                items.append(json.loads(line))
    for it in items:
        audit_item(it, issues)
    by_kind = Counter(i.split("] ", 1)[1].split("（")[0].split(":")[0] for i in issues)
    print(f"审计 {len(items)} 条，发现 {len(issues)} 个问题")
    for k, c in by_kind.most_common():
        print(f"  {c:4d}  {k}")
    if "--verbose" in sys.argv:
        for i in issues:
            print(" -", i)
    sys.exit(1 if issues else 0)


if __name__ == "__main__":
    main()
