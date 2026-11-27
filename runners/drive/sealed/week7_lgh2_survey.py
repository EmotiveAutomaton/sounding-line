"""CANDOR survey-only input to LGH2, using a separately reviewed numeric legend.

DESIGN CHECK (LESSONS 2–5). A reverse-coded response must still point toward
own laughter or pleasant mood. Unrecognized codes must fail before fitting.
No production legend is supplied by this module. No row leaves the sealed job.
"""
import math
import re
import numpy as np
import pandas as pd
import pyarrow.parquet as pq

from .week7_lgh2 import run
from .week6_sc1_counts_v1 import source_layout, Unavailable
from .week6_sc2_source_v1 import PINS


def survey_frame(frame, legends):
    """Apply explicit numeric code -> oriented score maps; None means missing."""
    fields = {'laughter':'reported_own_relative_laughter', 'pre_affect':'pre_affect', 'affect':'affect'}
    if set(legends) != set(fields) or not frame.columns.is_unique:
        raise ValueError('Expected exactly the three bound survey legends')
    result = frame[['conversation_id','user_id']].rename(columns={'conversation_id':'conversation','user_id':'speaker'}).copy()
    for field, target in fields.items():
        codes = legends[field]
        if not all(isinstance(k,(int,float)) and math.isfinite(k) for k in codes):
            raise ValueError('Invalid provider code')
        scores = [v for v in codes.values() if v is not None]
        if len(set(scores)) < 2 or not all(isinstance(v,(int,float)) and math.isfinite(v) for v in scores):
            raise ValueError('Expected at least two finite oriented scores')
        raw = pd.to_numeric(frame[field], errors='raise')
        if not raw.dropna().isin(codes).all():
            raise ValueError('Unbound survey response')
        result[target] = raw.map({k: np.nan if v is None else v for k,v in codes.items()})
    return result


def run_survey(frame, legends, out, *, draws=2000):
    """Run the existing whole-conversation analysis and its aggregate writer."""
    return run(survey_frame(frame, legends), out, marked=False, draws=draws)


def run_from_mount(root, out, legends, *, survey_pin=PINS['survey'], draws=2000):
    """Read the five approved columns only after verifying the survey file."""
    base = source_layout(root, {'survey': survey_pin})
    survey = base / survey_pin[0]
    if not survey.is_file():
        raise Unavailable(21)
    columns = ['conversation_id', 'user_id', 'laughter', 'pre_affect', 'affect']
    table = pq.read_table(survey, columns=columns)
    # Check Arrow values before pandas can collapse a valid IEEE NaN and a
    # native null into the same value. An unbound sentinel stops both fits.
    for field, codes in legends.items():
        for value in table[field].to_pylist():
            if value is None:
                continue
            if isinstance(value, str) and re.fullmatch(r'[0-9]+(?:\.0+)?', value):
                value = float(value)
            if type(value) not in (int, float) or value not in codes:
                raise Unavailable(24)
    frame = table.to_pandas()
    return run_survey(frame, legends, out, draws=draws)

