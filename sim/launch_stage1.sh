#!/bin/bash
cd /home/worker06/20260825tuoshuipaper/sim
OUT=../results/pilot_20260829
setsid -f bash -c "python3 run_experiments.py p6 >> $OUT/stage1.log 2>&1 && python3 run_experiments.py p5_full >> $OUT/stage1.log 2>&1 && python3 run_experiments.py p2_local >> $OUT/stage1.log 2>&1 && python3 run_experiments.py p7 >> $OUT/stage1.log 2>&1"
