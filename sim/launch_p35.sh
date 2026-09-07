#!/bin/bash
cd /home/worker06/20260825tuoshuipaper/sim
setsid -f bash -c "python3 stage4.py p35 >> ../results/stage4_20260907/online2.log 2>&1"
