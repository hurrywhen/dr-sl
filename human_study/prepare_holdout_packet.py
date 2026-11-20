#!/usr/bin/env python3
"""Prepare a blinded holdout utility scoring packet (prepared, NOT collected).

Real human ratings cannot be collected in this automated revision.  This script
only lays out the blinded materials and empty scoring sheets for the two co-author
raters; no synthetic "human" scores are invented.  The blind key is written to a
separate WITHHELD file and must not be joined until scoring is complete.
"""
import csv
import json
import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "sim"))
sys.path.insert(0, str(ROOT / "dataset"))
from qi import load_dataset

SEED = 20261121
OUT = ROOT / "human_study" / "holdout_utility_packet"
VARIANTS = ("direct", "closed_loop", "generalization_only")


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    offline = [json.loads(l) for l in (ROOT / "results/revision_20261121/offline_runtime.jsonl").open()]
    off = {(r["id"], r["method"]): r for r in offline
           if r["dataset"] == "holdout80" and r["sensitive_set"] == "runtime"}
    items = {r["id"]: r for r in load_dataset(str(ROOT / "dataset/output/dr_sl_holdout_v1.jsonl"))}
    subset = json.loads((ROOT / "results/revision_20261121/audit_subset.json").read_text())

    rows = []
    for iid in subset:
        for v in VARIANTS:
            material = items[iid]["prompt"] if v == "direct" else off[(iid, v)]["D"]
            rows.append({"instance": iid, "variant": v, "material": material})
    rng = random.Random(SEED)
    rng.shuffle(rows)
    for i, r in enumerate(rows, 1):
        r["blind_id"] = f"HU-{i:04d}"

    with (OUT / "scoring_sheet.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["blind_id", "material", "score_rater1", "score_rater2"])
        for r in rows:
            w.writerow([r["blind_id"], r["material"], "", ""])

    key = {r["blind_id"]: {"instance": r["instance"], "variant": r["variant"]} for r in rows}
    (OUT / "blind_key.json").write_text(json.dumps(key, ensure_ascii=False, indent=2))

    (OUT / "README.md").write_text(
        "# Holdout utility scoring packet — PREPARED, NOT COLLECTED\n\n"
        "Status: **prepared but not collected.** No human ratings exist yet for the holdout; "
        "this packet is published so the scoring design is transparent and reproducible. "
        "No synthetic \"human\" scores were invented.\n\n"
        f"- {len(subset)} holdout-1 instances × {len(VARIANTS)} variants "
        "(direct / closed_loop / generalization_only) = "
        f"{len(rows)} blinded rows, shuffled with seed {SEED}.\n"
        "- Raters: the two co-author expert raters (Y. Yu, X. Wang), blinded to variant identity.\n"
        "- Scale: 0 = unusable, 0.5 = partially usable, 1 = fully usable for the embedded task.\n"
        "- `scoring_sheet.csv` has empty score columns to be filled independently by each rater.\n"
        "- `blind_key.json` is included for reproducibility. Because this packet is "
        "prepared-but-not-collected and the shuffle is seed-deterministic, any future real "
        "scoring should regenerate blinding with a fresh seed and withhold the key from raters "
        "until both finish.\n\n"
        "Planned analysis (future work): inter-rater agreement, human vs local-surrogate and "
        "human vs offline-judge correlation with instance-cluster CIs, and threshold confusion. "
        "Until collected, holdout utility claims rest on the offline judge and downstream-task "
        "judge only, both external references with measurement error.\n",
        encoding="utf-8")
    print(f"prepared {len(rows)} blinded rows -> {OUT}")


if __name__ == "__main__":
    main()
