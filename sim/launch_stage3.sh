#!/bin/bash
cd /home/worker06/20260825tuoshuipaper/sim
OUT=../results/stage3_20260905
mkdir -p $OUT
setsid -f bash -c "python3 stage3.py p21 >> $OUT/stage3.log 2>&1 && python3 stage3.py p22 >> $OUT/stage3.log 2>&1 && python3 stage3.py p23 >> $OUT/stage3.log 2>&1"
