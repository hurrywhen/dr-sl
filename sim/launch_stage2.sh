#!/bin/bash
cd /home/worker06/20260825tuoshuipaper/sim
OUT=../results/stage2_20260902
mkdir -p $OUT
setsid -f bash -c "python3 stage2.py p12 >> $OUT/online.log 2>&1"
setsid -f bash -c "python3 stage2.py p11 >> $OUT/local.log 2>&1 && python3 stage2.py p13 >> $OUT/local.log 2>&1 && python3 stage2.py p14 >> $OUT/local.log 2>&1 && python3 stage2.py p15 >> $OUT/local.log 2>&1 && python3 stage2.py p16a >> $OUT/local.log 2>&1 && python3 stage2.py p16b >> $OUT/local.log 2>&1"
