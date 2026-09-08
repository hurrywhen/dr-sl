#!/bin/bash
cd /home/worker06/20260825tuoshuipaper/sim
setsid -f bash -c "python3 stage5.py p40 >> ../results/stage5_20260907/local2.log 2>&1"
