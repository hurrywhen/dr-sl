import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
os.environ["PILOT_OUT"] = "smoke_20260831"

import run_experiments as rx

v2, exp = rx.load_all()
test_rows = [r for r in v2 if r["split"] == "test"][:2]
cal_rows = [r for r in v2 if r["split"] == "calibration"][:2]
train_rows = [r for r in v2 if r["split"] == "train"][:2]
adv_rows = [r for r in v2 if r["split"] == "adversarial"][:1]

stage = sys.argv[1] if len(sys.argv) > 1 else "all"

if stage in ("all", "p6"):
    rx.load_all = lambda: (test_rows + adv_rows, [])
    rx.p6_extractor()
if stage in ("all", "p5"):
    rx.load_all = lambda: (cal_rows, [])
    rx.p5_full()
if stage in ("all", "p2"):
    rx.load_all = lambda: (test_rows, [])
    rx.p2_local()
if stage in ("all", "p7"):
    rx.load_all = lambda: (train_rows, [])
    rx.p7_train_loop()
print("SMOKE DONE:", stage)
