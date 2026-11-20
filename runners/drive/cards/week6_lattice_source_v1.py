"""Prospective LD source projection; no file is opened at import.

DESIGN CHECK: LESSONS 2-5 reread. Under either a null or an alternative,
unchanged admitted bytes and literal column meanings must survive projection.
Changed hashes, missing declared columns and undocumented encodings refuse;
missing ratings remain missing rather than becoming floor values. These gates
protect source identity, not a scientific sign. LD2's role-support projection
cannot materialize feelings. A counted caller still owes source admission,
support-first ordering, full diagnostics, every draw and independent replay.
"""
from pathlib import Path

import numpy as np
import pandas as pd

from .es_core_v1 import FEELINGS, need
from .es_source_v1 import rating, sha256, study_day
from .week6_lattice_bindings_v1 import ACTIVITY, STATUS, FEAR_LIKE


ROUTES = ('LD1', 'LD2-support', 'LD2-product', 'LD3')


def feeling_names(member):
    need(member in ('0056', '0057'), 'unreviewed diary member')
    return tuple(n for n in FEELINGS
                 if member == '0057' or n not in ('lonely', 'excluded'))


def columns(member, route):
    feelings = feeling_names(member)
    need(route in ROUTES, 'unreviewed lattice source route')
    base = ('id', 'day', 'interaction')
    if route == 'LD1':
        return base + tuple(prefix + n for prefix in ('int_', 'occup_')
                            for n in feelings)
    if route == 'LD2-support':
        return base + ('no_interactionpartner', 'interaction_partner1',
                       'status_criticised', 'beh_leadership')
    if route == 'LD2-product':
        return (base + tuple('status_' + n for n in STATUS)
                + ('beh_leadership', 'beh_selfesteem', 'int_superior')
                + tuple('int_' + n for n in ('angry', *FEAR_LIKE)))
    return (base + tuple('occup_' + n for n in ACTIVITY)
            + tuple('occup_' + n for n in feelings))


def selected_frames(path, pin, member, route, guard):
    """Authenticate and materialize only a fixed whitelist in a counted caller.

    Complete iterator consumption is mandatory. A final hash check rejects
    mutation during parsing; an interrupted iterator is not an admitted source.
    The callback is required so a runtime cannot accidentally omit its guards.
    """
    need(callable(guard), 'counted caller guard required')
    wanted = columns(member, route)
    path = Path(path)
    guard()
    need(path.is_file() and path.stat().st_size == pin['bytes'],
         'source size mismatch')
    need(sha256(path, guard) == pin['sha256'], 'source digest mismatch')
    for frame in pd.read_csv(path, sep='\t', usecols=list(wanted), dtype=str,
                             keep_default_na=False, na_filter=False,
                             chunksize=20000):
        need(tuple(frame.loc[:, list(wanted)].columns) == wanted,
             'source whitelist mismatch')
        guard()
        yield frame.loc[:, list(wanted)]
    need(path.stat().st_size == pin['bytes']
         and sha256(path, guard) == pin['sha256'], 'source changed during read')


def _positive_code(value, missing_tokens):
    if value in missing_tokens:
        return np.nan
    try:
        number = float(value)
    except (TypeError, ValueError):
        raise ValueError('invalid relationship code') from None
    need(np.isfinite(number) and number >= 1 and number == int(number),
         'invalid relationship code')
    return number


def prepare_people(frames, member, route, missing_tokens, guard):
    """Keep every selected prompt and its missingness; remove literal IDs.

    Each person is ordered by the literal source identity before IDs are
    discarded. Rows stay in original source order, not an inferred time order.
    Day is retained for later diagnostics but is not an extra fit exclusion.
    Separate member populations are never merged here.
    """
    need(type(missing_tokens) is list and all(type(x) is str for x in missing_tokens),
         'explicit reviewed missing tokens required')
    need(callable(guard), 'counted caller guard required')
    wanted = columns(member, route)
    feelings = feeling_names(member)
    grouped = {}
    counts = dict(source_rows=0, missing_id_rows=0, missing_context_rows=0,
                  other_context_rows=0, selected_rows=0, missing_day_rows=0)
    for frame in frames:
        need(len(frame.columns) == len(wanted) and set(frame.columns) == set(wanted),
             'unexpected source columns')
        guard()
        for row in frame.to_dict('records'):
            ordinal = counts['source_rows']
            counts['source_rows'] += 1
            if row['id'] in missing_tokens:
                counts['missing_id_rows'] += 1
                continue
            need(type(row['id']) is str, 'literal source identity required')
            context_text = row['interaction']
            if context_text in missing_tokens:
                counts['missing_context_rows'] += 1
                continue
            try:
                context = float(context_text)
            except (TypeError, ValueError):
                raise ValueError('unknown interaction code') from None
            need(context in (1., 2.), 'unknown interaction code')
            if ((route.startswith('LD2') and context != 1)
                    or (route == 'LD3' and context != 2)):
                counts['other_context_rows'] += 1
                continue
            day = study_day(row['day'], missing_tokens)
            counts['missing_day_rows'] += int(not np.isfinite(day))
            if route == 'LD1':
                prefix = 'int_' if context == 1 else 'occup_'
                values = {n: rating(row[prefix + n], 6, missing_tokens)
                          for n in feelings}
                values.update(failure=7 - values['success'], company=float(context == 1))
            elif route == 'LD2-support':
                values = dict(
                    partner_count=_positive_code(row['no_interactionpartner'], missing_tokens),
                    role=_positive_code(row['interaction_partner1'], missing_tokens),
                    criticised=rating(row['status_criticised'], 6, missing_tokens),
                    leadership=rating(row['beh_leadership'], 6, missing_tokens))
            elif route == 'LD2-product':
                values = {n: rating(row['status_' + n], 6, missing_tokens) for n in STATUS}
                values.update({n: rating(row['int_' + n], 6, missing_tokens)
                               for n in ('angry', *FEAR_LIKE, 'superior')})
                values.update({n: rating(row['beh_' + n], 6, missing_tokens)
                               for n in ('leadership', 'selfesteem')})
            else:
                values = {n: rating(row['occup_' + n], 6, missing_tokens)
                          for n in (*ACTIVITY, *feelings)}
            person = grouped.setdefault(row['id'], dict(days=[], source_ordinals=[], ratings={}))
            person['days'].append(day)
            person['source_ordinals'].append(ordinal)
            for name, value in values.items():
                person['ratings'].setdefault(name, []).append(value)
            counts['selected_rows'] += 1
    people = [grouped[k] for k in sorted(grouped)]
    counts.update(source_people=len(people), identity_fields_exported=False,
                  member=member, route=route, temporal_order_inferred=False)
    return people, counts


def complete_panel(people, names):
    """Literal common-row mask for a caller's frozen predictor/outcome names.

    This applies no hidden minimum-per-person, day or variance filter. Required
    support gates belong to the complete card. Private unit ordinals are the
    bootstrap cluster, never a public participant roster or a cross-member ID.
    """
    names = tuple(names)
    need(names and len(set(names)) == len(names), 'unique declared panel names required')
    units, chunks = [], []
    total = dropped = absent_people = 0
    for unit, person in enumerate(people):
        ratings = person['ratings']
        need(all(n in ratings for n in names), 'required panel item absent')
        nrows = len(person['source_ordinals'])
        need(all(len(v) == nrows for v in ratings.values()), 'person row alignment differs')
        matrix = np.column_stack([ratings[n] for n in names]).astype(float)
        keep = np.isfinite(matrix).all(axis=1)
        total += nrows
        dropped += int((~keep).sum())
        absent_people += int(not keep.any())
        chunks.append(matrix[keep])
        units.extend([unit] * int(keep.sum()))
    matrix = np.concatenate(chunks) if chunks else np.empty((0, len(names)))
    return (np.asarray(units, dtype=np.int64),
            {name: matrix[:, i] for i, name in enumerate(names)},
            dict(rows_before=total, missing_rows=dropped, retained_rows=len(units),
                 people_before=len(people), people_without_complete_rows=absent_people,
                 retained_people=len(set(units)), support_not_yet_adjudicated=True))
