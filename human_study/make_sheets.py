import csv
import json
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "sim"))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "dataset"))

from pipeline import det_dehydrate
from stage4 import placeholder_D, ldp_D
from qi import load_dataset

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "human_study"
OUT.mkdir(exist_ok=True)
SEED = 20260908


def main():
    v2 = load_dataset(str(ROOT / "dataset" / "output" / "dr_sl_dataset_v2.jsonl"))
    test = [r for r in v2 if r["split"] == "test"]
    rng = random.Random(SEED)
    sample = []
    for dom in ("medical", "banking", "travel", "legal"):
        sample.extend(rng.sample([r for r in test if r["domain"] == dom], 10))

    rows_u, key = [], {}
    for item in sample:
        points = {"direct": item["prompt"], "generalized": det_dehydrate(item)["D"],
                  "placeholder": placeholder_D(item), "ldp": ldp_D(item, seed=20260907)}
        order = list(points.keys())
        rng.shuffle(order)
        for label, point_key in zip("ABCD", order):
            row_id = f"{item['id']}_{label}"
            key[row_id] = point_key
            rows_u.append({
                "row_id": row_id,
                "domain": item["domain"],
                "original_text": item["prompt"],
                "processed_text": points[point_key],
                "score_0_or_0.5_or_1": "",
                "confidence_1_to_5": "",
                "note": "",
            })
    with open(OUT / "utility_scoring_sheet.csv", "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows_u[0].keys()))
        w.writeheader()
        w.writerows(rows_u)
    with open(OUT / "utility_variant_key.json", "w", encoding="utf-8") as f:
        json.dump(key, f, ensure_ascii=False, indent=1)

    rng2 = random.Random(SEED + 1)
    ann_sample = rng2.sample(test, 50)
    with open(OUT / "annotation_sheet.csv", "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["instance_id", "domain", "text",
                                          "sensitive_items(type=value;...)", "combo_risk(y/n)", "note"])
        w.writeheader()
        for item in ann_sample:
            w.writerow({"instance_id": item["id"], "domain": item["domain"],
                        "text": item["prompt"], "sensitive_items(type=value;...)": "",
                        "combo_risk(y/n)": "", "note": ""})
    print(f"utility sheet: {len(rows_u)} rows (40 instances x 4 blinded points); key saved")
    print(f"annotation sheet: {len(ann_sample)} rows")


if __name__ == "__main__":
    main()
