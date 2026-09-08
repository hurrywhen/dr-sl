#!/bin/bash
cd /home/worker06/20260825tuoshuipaper/sim
OUT=../results/stage5_20260907
mkdir -p $OUT
setsid -f bash -c "python3 stage5.py p36b >> $OUT/online.log 2>&1 && python3 stage5.py p37 >> $OUT/online.log 2>&1 && python3 stage5.py p38 >> $OUT/online.log 2>&1"
setsid -f bash -c "python3 stage5.py p39 >> $OUT/local.log 2>&1"
