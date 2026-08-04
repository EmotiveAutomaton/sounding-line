#!/bin/bash
# GPU queue, 2026-08-04. Serial so nothing contends; the card should not idle.
cd "e:/EmotiveAutomaton/Projects/SoundingLine/sounding-line"
P=./.venv/Scripts/python.exe

echo "=== [1/3] D-0b: powered rerun, 2000+ words, k=10 ==="
$P -u runners/run_d0b.py --k 10 > results/d0b_run.log 2>&1
echo "D0B_EXIT=$?"

echo "=== [2/3] no-maker control set: 36 artifacts, length-matched ==="
$P -u runners/make_nomaker_set.py --per-kind 12 > results/nomaker_run.log 2>&1
echo "NOMAKER_EXIT=$?"

echo "=== [3/3] wall test on an INSTRUCT model, which has a persona to be displaced from ==="
$P -u runners/run_wall.py --model Qwen/Qwen2.5-1.5B-Instruct --device cuda --artifacts 30 \
   > results/wall_instruct.log 2>&1
echo "WALL_EXIT=$?"
echo "QUEUE DONE"
