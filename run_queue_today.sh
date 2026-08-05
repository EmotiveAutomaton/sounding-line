#!/bin/bash
# Today's queue. Each stage skips if its output already exists. Run: bash run_queue_today.sh
cd "e:/EmotiveAutomaton/Projects/SoundingLine/sounding-line"
P=./.venv/Scripts/python.exe

if [ ! -f results/layer_ratio/control.json ]; then
  echo "=== [1] layer-ratio controls: shuffle, length, register ==="
  $P -u runners/run_lr_control.py > results/lr_control.log 2>&1; echo "EXIT=$?"
fi

# Only worth running if the controls held. The gate is checked in-script.
if [ -f results/layer_ratio/control.json ] && [ ! -f results/layer_ratio/lr_7b.json ]; then
  SURV=$($P -c "import json;print(json.load(open('results/layer_ratio/control.json'))['survival'])")
  echo "=== [2] control survival was $SURV ==="
  if $P -c "import json,sys; sys.exit(0 if json.load(open('results/layer_ratio/control.json'))['survival'] < 0.5 else 1)"; then
    echo "=== [2] layer ratio on a 7B — the controls held ==="
    $P -u runners/run_layer_ratio.py --model Qwen/Qwen2.5-7B --device cuda --gate3 30 \
       > results/lr_7b.log 2>&1; echo "EXIT=$?"
    cp results/layer_ratio/layer_ratio.json results/layer_ratio/lr_7b.json 2>/dev/null
  else
    echo "    SKIPPED — the gap survived shuffling, so a bigger model measures the same confound"
  fi
fi

if [ ! -f results/breadth_books.json ]; then
  echo "=== [3] purpose_breadth, early vs late works ==="
  $P -u runners/run_breadth_books.py > results/breadth_books.log 2>&1; echo "EXIT=$?"
fi
echo "QUEUE DONE"
