import json
import re
import sys
from collections import Counter

SCHEMA_PATH = "schema.json"

ID_RE = re.compile(r"^DRSL-(MED|BNK|TRV|LEG)-(CAL|TRN|TST|ADV)-([0-9]{4}|R[0-9]{3})$")
TID_RE = re.compile(r"^(med|bank|travel|legal)_(t|a|rw)[0-9]{2}$")
ENUMS = {
    "domain": {"medical", "banking", "travel", "legal"},
    "split": {"calibration", "train", "test", "adversarial"},
    "structure": {"statement", "dialogue", "list", "longform"},
    "length_bucket": {"short", "medium", "long"},
    "sensitivity_density": {"low", "medium", "high"},
    "difficulty": {"easy", "medium", "hard"},
    "category": {"explicit", "quasi"},
}
SPLIT_DOMAIN_TARGET = {
    ("calibration",): 50, ("train",): 60, ("test",): 40, ("adversarial",): 20,
}


def fail(errors, item_id, msg):
    errors.append(f"[{item_id}] {msg}")


def validate_entity(e, item_id, prompt, errors, path):
    for k in ("type", "category", "value", "span", "task_relevant"):
        if k not in e:
            fail(errors, item_id, f"{path} 缺字段 {k}")
            return
    if e["category"] not in ENUMS["category"]:
        fail(errors, item_id, f"{path} category 非法: {e['category']}")
    s, t = e["span"]
    if not (0 <= s < t <= len(prompt)):
        fail(errors, item_id, f"{path} span 越界 {e['span']}")
    elif prompt[s:t] != e["value"]:
        fail(errors, item_id, f"{path} span 与 value 不一致: {prompt[s:t]!r} != {e['value']!r}")
    if not isinstance(e["task_relevant"], bool):
        fail(errors, item_id, f"{path} task_relevant 非布尔")


def validate_item(it, errors):
    iid = it.get("id", "<no-id>")
    if not ID_RE.match(iid):
        fail(errors, iid, "id 格式非法")
    if not TID_RE.match(it.get("template_id", "")):
        fail(errors, iid, f"template_id 格式非法: {it.get('template_id')}")
    for k, allowed in ENUMS.items():
        if k in it and it[k] not in allowed:
            fail(errors, iid, f"{k} 非法: {it[k]}")
    prompt = it.get("prompt", "")
    if len(prompt) < 10:
        fail(errors, iid, "prompt 过短")
    n = len(prompt)
    expect = "short" if n < 150 else ("medium" if n < 400 else "long")
    if it.get("length_bucket") != expect:
        fail(errors, iid, f"length_bucket={it.get('length_bucket')} 与实际({expect})不符")
    ann = it.get("annotations", {})
    for cat in ("explicit_identifiers", "quasi_identifiers"):
        for j, e in enumerate(ann.get(cat, [])):
            validate_entity(e, iid, prompt, errors, f"{cat}[{j}]")
            if e.get("category") != cat.split("_")[0]:
                fail(errors, iid, f"{cat}[{j}] category 与所在数组不符")
    for c in ann.get("combos", []):
        if len(c.get("members", [])) < 2:
            fail(errors, iid, "combo 成员少于 2")
    has_q = any(True for _ in ann.get("quasi_identifiers", []))
    if ann.get("has_quasi_identifier") != has_q:
        fail(errors, iid, "has_quasi_identifier 与实际不符")
    density = len(ann.get("explicit_identifiers", [])) + len(ann.get("quasi_identifiers", []))
    expect_d = "low" if density <= 2 else ("medium" if density <= 5 else "high")
    if it.get("sensitivity_density") != expect_d:
        fail(errors, iid, f"density={it.get('sensitivity_density')} 与实际({expect_d})不符")


def validate_dataset(items, errors):
    ids = Counter(i["id"] for i in items)
    for iid, c in ids.items():
        if c > 1:
            fail(errors, iid, f"id 重复 x{c}")
    synthetic = [i for i in items if i.get("source") == "synthetic_template"]
    counts = Counter((i["split"], i["domain"]) for i in synthetic)
    targets = {"calibration": 50, "train": 60, "test": 40, "adversarial": 20}
    for split, tgt in targets.items():
        for dom in ENUMS["domain"]:
            got = counts.get((split, dom), 0)
            if got != tgt:
                errors.append(f"[dataset] 合成样本 {split}/{dom} 数量 {got} != {tgt}")
    test_src = {i.get("source") for i in items if i["split"] == "test"}
    if test_src - {"synthetic_template"}:
        errors.append(f"[dataset] 测试集混入非合成来源: {test_src}")
    qr = sum(1 for i in items if i["annotations"]["has_quasi_identifier"]) / len(items)
    if qr < 0.40:
        errors.append(f"[dataset] 准标识符样本占比 {qr:.2%} < 40%")
    templates_by_split = {}
    for i in items:
        for s, tids in templates_by_split.items():
            if s != i["split"] and i["template_id"] in tids:
                errors.append(f"[dataset] 模板 {i['template_id']} 跨集出现于 {s} 与 {i['split']}")
        templates_by_split.setdefault(i["split"], set()).add(i["template_id"])


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else "output/dr_sl_dataset_v1.jsonl"
    items, errors = [], []
    with open(path, encoding="utf-8") as f:
        for ln, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                items.append(json.loads(line))
            except json.JSONDecodeError as ex:
                errors.append(f"[line {ln}] JSON 解析失败: {ex}")
    for it in items:
        validate_item(it, errors)
    validate_dataset(items, errors)
    if errors:
        print(f"校验失败：{len(errors)} 个问题")
        for e in errors[:50]:
            print(" -", e)
        sys.exit(1)
    print(f"校验通过：{len(items)} 条样本全部符合 schema 与配额约束")


if __name__ == "__main__":
    main()
