#!/bin/bash
cd /home/worker06/20260825tuoshuipaper/sim
setsid -f bash -c "python3 smoke_stage1.py all >> ../results/smoke_20260831/smoke.log 2>&1"
