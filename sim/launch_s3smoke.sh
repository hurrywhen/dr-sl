#!/bin/bash
cd /home/worker06/20260825tuoshuipaper/sim
setsid -f bash -c "STAGE3_OUT=stage3_smoke STAGE3_SMOKE=1 python3 stage3.py p22 >> ../results/stage3_smoke/smoke.log 2>&1; STAGE3_OUT=stage3_smoke STAGE3_SMOKE=1 python3 stage3.py p23 >> ../results/stage3_smoke/smoke.log 2>&1"
