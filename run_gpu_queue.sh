#!/bin/bash
# GPU queue, 2026-08-04. Serial. Each stage checks whether its output already exists.
cd "e:/EmotiveAutomaton/Projects/SoundingLine/sounding-line"
P=./.venv/Scripts/python.exe

if [ ! -f corpora/nomaker/manifest.json ]; then
  echo "=== no-maker control set: 36 artifacts, length-matched, 3 kinds ==="
  $P -u runners/make_nomaker_set.py --per-kind 12 > results/nomaker_run.log 2>&1
  echo "NOMAKER_EXIT=$?"
fi

if [ ! -f results/wall/wall_instruct.json ]; then
  echo "=== wall test on an INSTRUCT model, which has a persona ==="
  $P -u runners/run_wall.py --model Qwen/Qwen2.5-1.5B-Instruct --device cuda --artifacts 30 \
     > results/wall_instruct.log 2>&1
  echo "WALL_EXIT=$?"
fi
echo "QUEUE DONE"
