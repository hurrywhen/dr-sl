#!/bin/bash
cd /home/worker06/20260825tuoshuipaper/sim
setsid -f bash -c "python3 run_experiments.py p2_strong >> ../results/pilot_20260829/p2_strong.log 2>&1"
