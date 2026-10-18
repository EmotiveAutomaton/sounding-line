"""D14 schema-only repair: carry authenticated parent session end times.

The prepared source deliberately omits session_end on individual rows. P4's
execute wrapper derives it from parent end_at before prefix_features. Reproduce
that exact operation without changing source dictionaries or scientific features.
"""
from .events_d14_features import pilot_writers, spacy_pins, ParagraphEncoder, extract_writer
from . import events_d14_features as original


def prepared_sessions(sessions):
    normalized = []
    for session in sessions:
        if session['end_at'] < session['timestamp']:
            raise ValueError('negative authenticated session duration')
        rows = []
        for row in session['rows']:
            if row['session'] != session['session'] or row['writer'] != session['writer'] or row['session_time'] != session['timestamp']:
                raise ValueError('row and authenticated parent session differ')
            if 'session_end' in row and row['session_end'] != session['end_at']:
                raise ValueError('row end time conflicts with authenticated parent')
            rows.append(dict(row, session_end=session['end_at']))
        normalized.append(dict(session, rows=rows))
    return normalized


def nuisance_matrix(rows, sessions, records, vectors, p8_rows, seed, pca_dimensions=16):
    return original.nuisance_matrix(rows, prepared_sessions(sessions), records, vectors, p8_rows, seed, pca_dimensions)
