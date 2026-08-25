import json
import random
import re
import difflib
from collections import Counter

import synth_values as sv

SEED = 20260826
INPUT_DEFAULT = "data_raw/medqa_zh_4options_train.jsonl"
MAIN_DATASET = "output/dr_sl_dataset_v1.jsonl"
OUTPUT = "output/dr_sl_dataset_v2.jsonl"
REWRITE_ONLY = "output/medqa_rewrite.jsonl"
DUP_THRESHOLD = 0.85

N_CALIBRATION = 90
N_TRAIN = 160

NARRATIVE_PAT = re.compile(r"岁|患儿|患者|男婴|女婴|孕妇|新生儿|婴儿|幼儿")
EXAM_TAIL_PAT = re.compile(r"[（(]\s*[　 ]*\s*[）)]")
EXAM_SENT_PAT = re.compile(
    r"[^。；;]*?(最可能|首选|最适当|最适宜|诊断是|诊断考虑|处理措施|治疗方法|治疗方案|"
    r"应诊断为|应考虑|最恰当|最合理|最佳|检查是|药物是|疾病是|病变应为|原因是|"
    r"为进一步|确诊|鉴别诊断)[^。；;]*[。？?]?")
AGE_PAT = re.compile(r"(\d{1,3})\s*岁(半)?|(\d{1,2})\s*个?月(龄|大)?|出生(\d{1,3})\s*天|孕(\d{1,2})\s*周")
GENDER_PAT = re.compile(r"(?:患者[，,]?|^|^\d+[．.、]\s*)(男|女)[，,。岁\d]")

DISEASE_DICT = sorted([
    "糖尿病酮症酸中毒", "特发性血小板减少性紫癜", "系统性红斑狼疮", "再生障碍性贫血",
    "缺铁性贫血", "巨幼细胞贫血", "地中海贫血", "溶血性贫血", "弥漫性血管内凝血",
    "蛛网膜下腔出血", "腰椎间盘突出", "甲状腺功能亢进", "支气管扩张", "肾病综合征",
    "消化性溃疡", "胃食管反流", "房间隔缺损", "室间隔缺损", "动脉导管未闭",
    "法洛四联症", "视网膜脱离", "神经母细胞瘤", "肾母细胞瘤", "过敏性紫癜",
    "妊娠高血压", "心肌梗死", "心律失常", "脑出血", "脑梗死", "脑膜炎", "脑震荡",
    "硬膜外血肿", "颅内出血", "肺心病", "慢阻肺", "胸腔积液", "肺脓肿",
    "肺炎", "肺结核", "高血压", "糖尿病", "冠心病", "心衰", "哮喘", "贫血",
    "白血病", "淋巴瘤", "肺癌", "胃癌", "肝癌", "结肠癌", "直肠癌", "乳腺癌",
    "宫颈癌", "子宫肌瘤", "卵巢囊肿", "阑尾炎", "胆囊炎", "胆结石", "胰腺炎",
    "肝炎", "肝硬化", "肾炎", "尿路感染", "甲亢", "甲减", "癫痫", "帕金森病",
    "骨折", "关节脱位", "颈椎病", "关节炎", "类风湿关节炎", "川崎病", "手足口病",
    "水痘", "麻疹", "猩红热", "百日咳", "流行性腮腺炎", "支气管炎", "急性胃肠炎",
    "胃溃疡", "痔疮", "败血症", "休克", "中暑", "中毒", "烧伤", "湿疹", "荨麻疹",
    "银屑病", "抑郁症", "焦虑症", "精神分裂症", "躁狂症", "子痫", "宫外孕",
    "前置胎盘", "低血糖", "痛风", "高脂血症", "动脉粥样硬化", "深静脉血栓",
    "肺栓塞", "气胸", "心肌炎", "心包炎", "先天性心脏病", "脑积水", "白内障",
    "青光眼", "中耳炎", "鼻窦炎", "扁桃体炎", "龋齿", "牙周炎", "口腔溃疡",
    "食管癌", "胰腺癌", "肾癌", "膀胱癌", "前列腺癌", "卵巢癌", "子宫内膜癌",
    "甲状腺癌", "胶质瘤", "脑膜瘤", "骨肉瘤", "霍奇金淋巴瘤", "血友病",
    "新生儿黄疸", "新生儿窒息", "早产儿", "佝偻病", "营养不良",
], key=len, reverse=True)

QUESTION_POOLS = {
    "self": ["请问我的情况严重吗，下一步该怎么办？", "请问我该如何治疗和日常调理？",
             "请问我这种情况需要尽快就医吗？"],
    "family": ["作为家属我们很担心，请问这种情况该怎么处理？", "请问我家人的情况严重吗，需要注意什么？",
               "请问接下来该怎么配合治疗？"],
    "doctor": ["想请各位专家指点下一步的诊疗方案。", "请问这个病例的处理上有什么需要注意的？",
               "请帮忙分析下一步的检查和治疗思路。"],
}

FRAMES = ["self", "family", "doctor"]
FRAME_TEMPLATE = {
    "self": "我今年{age_txt}{core}{question}",
    "family": "这是我亲人的就诊情况：{core}{question}",
    "doctor": "我接诊的一位患者情况如下：{core}{question}",
}
CAL_TIDS = ["med_rw01", "med_rw02", "med_rw03"]
TRAIN_TIDS = ["med_rw04", "med_rw05", "med_rw06"]


def strip_exam_tail(question):
    parts = re.split(r"(?<=[。；;])", question)
    kept = []
    for p in parts:
        if EXAM_TAIL_PAT.search(p) or EXAM_SENT_PAT.search(p):
            continue
        p = p.strip()
        if p:
            kept.append(p)
    text = "".join(kept)
    text = re.sub(r"^\d+[．.、]\s*", "", text).strip()
    return text


def extract_entities(text):
    ents = []
    m = AGE_PAT.search(text)
    age_txt = None
    if m:
        age_txt = m.group(0)
        ents.append({"category": "quasi", "type": "age", "value": age_txt,
                     "task_relevant": True, "span_hint": m.span()})
    m = GENDER_PAT.search(text)
    if m:
        ents.append({"category": "quasi", "type": "gender", "value": m.group(1),
                     "task_relevant": True, "span_hint": (m.start(1), m.end(1))})
    hits = 0
    for d in DISEASE_DICT:
        idx = text.find(d)
        if idx >= 0:
            ents.append({"category": "quasi", "type": "disease", "value": d,
                         "task_relevant": True, "span_hint": (idx, idx + len(d))})
            hits += 1
            if hits >= 2:
                break
    return ents, age_txt


def locate(text, value, used):
    start = 0
    while True:
        i = text.find(value, start)
        if i < 0:
            return None
        if all(not (i < u[1] and i + len(value) > u[0]) for u in used):
            used.append((i, i + len(value)))
            return [i, i + len(value)]
        start = i + 1


def build_sample(src_idx, core, quasis, frame, tid, split, idx, rng):
    segs = [("text", FRAME_TEMPLATE[frame].format(
        age_txt="", core=core, question=rng.choice(QUESTION_POOLS[frame])))]
    n_quasi = len(quasis)
    pool = ["name", "phone", "id_card", "medical_record_no", "email", "hospital"]
    if n_quasi <= 1:
        inject = rng.sample(pool, 1 if rng.random() < 0.6 else 2)
    elif n_quasi == 2:
        inject = rng.sample(pool, 0 if rng.random() < 0.5 else 1)
    else:
        inject = rng.sample(pool, rng.choice([0, 1]))
    entities = []
    text = segs[0][1]
    used = []
    for q in quasis:
        span = locate(text, q["value"], used)
        if span:
            entities.append({**q, "span": span})
    extras = []
    for k in inject:
        if k == "name":
            extras.append((f"我叫{sv.person_name(rng)}，", "name", None))
        elif k == "phone":
            v = sv.phone(rng)
            extras.append((f"联系电话{v}，", "phone", v))
        elif k == "id_card":
            v = sv.id_card(rng)
            extras.append((f"身份证号{v}，", "id_card", v))
        elif k == "medical_record_no":
            v = sv.mrn(rng)
            extras.append((f"门诊号{v}，", "medical_record_no", v))
        elif k == "email":
            v = sv.email(rng)
            extras.append((f"邮箱{v}，", "email", v))
        elif k == "hospital":
            v = rng.choice(sv.HOSPITALS)
            extras.append((f"目前在{v}就诊，", "hospital", v))
    for s, typ, v in extras:
        if v is None:
            name = re.search(r"我叫(.+?)，", s).group(1)
            text = s + text
            shift = len(s)
            for e in entities:
                e["span"] = [e["span"][0] + shift, e["span"][1] + shift]
            used = [(u[0] + shift, u[1] + shift) for u in used]
            i = text.find(name)
            entities.append({"category": "explicit", "type": typ, "value": name,
                             "task_relevant": False, "span": [i, i + len(name)]})
        else:
            text = s + text
            shift = len(s)
            for e in entities:
                e["span"] = [e["span"][0] + shift, e["span"][1] + shift]
            used = [(u[0] + shift, u[1] + shift) for u in used]
            i = text.find(v)
            cat = "quasi" if typ == "hospital" else "explicit"
            entities.append({"category": cat, "type": typ, "value": v,
                             "task_relevant": False, "span": [i, i + len(v)]})
    return text, entities


def build_combos(entities):
    quasis = [e for e in entities if e["category"] == "quasi"]
    localizers = {"city", "employer", "school", "hospital", "detention"}
    attributes = {"age", "gender", "occupation", "disease", "income", "charge", "case_type"}
    types = {e["type"] for e in quasis}
    combos = []
    if len(quasis) >= 2 and types & localizers and types & attributes:
        combos.append({
            "members": [e["span"] for e in quasis],
            "member_types": [e["type"] for e in quasis],
            "risk": "reidentification",
            "note": "准标识符组合可在小范围群体内唯一化个体",
        })
    return combos


def main():
    import os
    rng = random.Random(SEED)
    path = INPUT_DEFAULT
    if not os.path.exists(path):
        raise SystemExit(f"缺少 {path}，请先放入 MedQA 中文 4-options jsonl")

    with open(MAIN_DATASET, encoding="utf-8") as f:
        main_items = [json.loads(l) for l in f if l.strip()]
    seen_texts = [i["prompt"] for i in main_items]

    out = []
    idx_cal, idx_train = 0, 0
    stats = Counter()
    with open(path, encoding="utf-8") as f:
        lines = f.readlines()
    rng.shuffle(lines)
    for ln, line in enumerate(lines):
        if idx_cal >= N_CALIBRATION and idx_train >= N_TRAIN:
            break
        d = json.loads(line)
        q = d["question"].strip()
        if not NARRATIVE_PAT.search(q) or not (40 <= len(q) <= 260):
            stats["reject_filter"] += 1
            continue
        core = strip_exam_tail(q)
        if len(core) < 25 or EXAM_TAIL_PAT.search(core):
            stats["reject_tail"] += 1
            continue
        quasis, _ = extract_entities(core)
        if not quasis:
            stats["reject_no_quasi"] += 1
            continue
        split = "calibration" if idx_cal < N_CALIBRATION else "train"
        tids = CAL_TIDS if split == "calibration" else TRAIN_TIDS
        frame = FRAMES[len(out) % 3]
        tid = tids[FRAMES.index(frame)]
        text, entities = build_sample(ln, core, quasis, frame, tid, split, 0, rng)
        if any(difflib.SequenceMatcher(None, text, s).ratio() >= DUP_THRESHOLD for s in seen_texts):
            stats["reject_dup"] += 1
            continue
        seen_texts.append(text)
        if split == "calibration":
            idx_cal += 1
            idx = idx_cal
        else:
            idx_train += 1
            idx = idx_train
        has_quasi = any(e["category"] == "quasi" for e in entities)
        n_ent = len(entities)
        n = len(text)
        quasi_n = sum(1 for e in entities if e["category"] == "quasi")
        difficulty = "hard" if quasi_n >= 3 else ("medium" if quasi_n >= 1 or n_ent >= 4 else "easy")
        item = {
            "id": f"DRSL-MED-{'CAL' if split == 'calibration' else 'TRN'}-R{idx:03d}",
            "domain": "medical",
            "split": split,
            "prompt": text,
            "template_id": tid,
            "structure": "statement",
            "length_bucket": "short" if n < 150 else ("medium" if n < 400 else "long"),
            "sensitivity_density": "low" if n_ent <= 2 else ("medium" if n_ent <= 5 else "high"),
            "difficulty": difficulty,
            "annotations": {
                "explicit_identifiers": [e for e in entities if e["category"] == "explicit"],
                "quasi_identifiers": [e for e in entities if e["category"] == "quasi"],
                "combos": build_combos(entities),
                "has_quasi_identifier": has_quasi,
            },
            "source": "open_dataset_rewrite",
            "source_id": f"medqa_zh_4options_train#{ln}",
            "license": "MedQA (MIT License); rewritten, PII fully synthetic",
            "annotation_meta": {
                "annotator": "auto_v1",
                "needs_human_review": True,
                "adversarial_type": None,
            },
        }
        for cat in ("explicit_identifiers", "quasi_identifiers"):
            for e in item["annotations"][cat]:
                s, t = e["span"]
                assert item["prompt"][s:t] == e["value"], f"span mismatch {item['id']}"
                e.pop("span_hint", None)
        out.append(item)
        stats[f"accept_{split}"] += 1

    os.makedirs("output", exist_ok=True)
    with open(REWRITE_ONLY, "w", encoding="utf-8") as f:
        for i in out:
            f.write(json.dumps(i, ensure_ascii=False) + "\n")
    combined = main_items + out
    with open(OUTPUT, "w", encoding="utf-8") as f:
        for i in combined:
            f.write(json.dumps(i, ensure_ascii=False) + "\n")

    report = {
        "rewrite_total": len(out),
        "by_split": dict(Counter(i["split"] for i in out)),
        "density": dict(Counter(i["sensitivity_density"] for i in out)),
        "difficulty": dict(Counter(i["difficulty"] for i in out)),
        "combined_total": len(combined),
        "combined_density": dict(Counter(i["sensitivity_density"] for i in combined)),
        "filter_stats": dict(stats),
    }
    with open("output/medqa_rewrite_report.json", "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
