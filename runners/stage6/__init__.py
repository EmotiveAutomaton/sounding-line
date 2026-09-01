"""Stage 6 package (brief: docs/design/PHASE_2_4_STAGE_6_CONTEXT.md, §12): the namespaced
implementation of the 104 cards, 24 attacks, nine architecture arms, worlds, records,
realization, prediction, scheduler, and report. Stage 1-5 code and results are immutable;
this package only imports them. Module names deliberately avoid Ghost's historical
`runners/run_*` match class (§11.5)."""

from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))
