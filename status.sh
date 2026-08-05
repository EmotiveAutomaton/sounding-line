#!/bin/bash
# What is running right now. Run: bash status.sh
cd "e:/EmotiveAutomaton/Projects/SoundingLine/sounding-line"
echo "=== GPU ==="
nvidia-smi --query-gpu=utilization.gpu,memory.used,memory.total --format=csv,noheader
echo
echo "=== python processes ==="
tasklist //FI "IMAGENAME eq python.exe" 2>/dev/null | tail -n +4 | head -5
echo
echo "=== most recent lines from every live log ==="
for f in results/*.log; do
  [ -f "$f" ] || continue
  age=$(( ($(date +%s) - $(date -r "$f" +%s)) / 60 ))
  if [ $age -lt 90 ]; then
    echo "--- $f  (${age}m ago) ---"
    grep -av "Loading weights\|HF_TOKEN" "$f" | tail -3
  fi
done
