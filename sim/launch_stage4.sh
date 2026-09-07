#!/bin/bash
cd /home/worker06/20260825tuoshuipaper/sim
OUT=../results/stage4_20260907
mkdir -p $OUT
setsid -f bash -c "python3 stage4.py p34 >> $OUT/online.log 2>&1 && python3 stage4.py p31 >> $OUT/online.log 2>&1 && python3 stage4.py p33 >> $OUT/online.log 2>&1"
setsid -f bash -c "python3 stage4.py p32 >> $OUT/local.log 2>&1"
