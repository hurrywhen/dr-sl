#!/bin/bash
cd /home/worker06/20260825tuoshuipaper/sim
setsid -f bash -c "STAGE2_OUT=stage2_smoke STAGE2_SMOKE=1 python3 stage2.py p13 >> ../results/stage2_smoke/p13.log 2>&1"
