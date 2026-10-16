"""Versioned destination for exact-source-byte notice repair.

DESIGN CHECK: LESSONS 2-5 read 2026-10-14. NULL: mismatched bytes still refuse.
ALTERNATIVE: the unchanged tested transport accepts independently verified pins.
This dedicated child process has no shared module state with the ended v1 owner.
"""
from pathlib import Path
import sys
from . import intake_jsonl

if __name__ == '__main__':
    intake_jsonl.ROOT = intake_jsonl.REPO / 'results/phase_2_4_stage_15/raw/public-jsonl-v2'
    intake_jsonl.run(Path(sys.argv[1]))
