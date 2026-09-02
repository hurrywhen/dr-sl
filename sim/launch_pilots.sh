#!/bin/bash
cd /home/worker06/20260825tuoshuipaper/sim
OUT=../results/pilot_20260829
setsid -f bash -c "python3 run_experiments.py p2 >> $OUT/p2.log 2>&1; python3 run_experiments.py p3 >> $OUT/p3.log 2>&1"
setsid -f bash -c "python3 run_experiments.py p5 >> $OUT/p5.log 2>&1; python3 run_experiments.py p4 >> $OUT/p4.log 2>&1"
