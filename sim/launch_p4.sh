#!/bin/bash
cd /home/worker06/20260825tuoshuipaper/sim
setsid -f bash -c "PILOT_TAU_L=0.20 python3 run_experiments.py p4 >> ../results/pilot_20260829/p4.log 2>&1"
