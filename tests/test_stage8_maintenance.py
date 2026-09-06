"""Run maintenance fixtures in a fresh interpreter with every Stage 8 root isolated."""
import os
from pathlib import Path
import subprocess
import sys


def test_stage8_maintenance(tmp_path):
    repo = Path(__file__).resolve().parents[1]
    env = dict(os.environ, S7_ROOT=str(tmp_path), S7_STAGE="phase_2_4_stage_8",
               S7_SMOKE="1", S7_FAKE_SERVER="1", S8_SKIP_TRAIN="1", PYTHONDONTWRITEBYTECODE="1")
    result = subprocess.run([sys.executable, "-B", "tests/stage8_maintenance_checks.py"],
                            cwd=repo, env=env, capture_output=True, text=True, timeout=120)
    assert result.returncode == 0, result.stdout + result.stderr
