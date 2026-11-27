"""First-wave MIDUS source binding and the original SLD3 single-item analysis."""
from hashlib import sha256
from itertools import combinations
from pathlib import Path

from week6_sealed_support_v1 import ReadBudget, SealedFailure, write_tables

SINGLE = (2, 4, 6, 7, 9, 10)
TRAITS = ('A1SNEURO', 'A1SEXTRA', 'A1SAGREE', 'A1SCONS', 'A1SOPEN')
KEYS = ('M2ID', 'M2FAMNUM')
EVENTS = tuple('A2DF' + str(i) for i in range(1, 8))
AFFECT = tuple('A2DC' + str(i) for i in SINGLE)


def files(root, manifest):
    if set(manifest) != {'diary', 'survey'}:
        raise SealedFailure(13, 'Missing source role')
    limit = sum(item['bytes'] for item in manifest.values())
    reader = ReadBudget(root, maximum=limit)
    paths = {}
    for role, item in manifest.items():
        name = item['filename']
        if Path(name).name != name:
            raise SealedFailure(13, 'Invalid source role')
        path = reader.reserve(Path(root) / name)
        digest = sha256()
        if path.stat().st_size != item['bytes']:
            raise SealedFailure(13, 'Source size differs')
        with path.open('rb') as stream:
            for block in iter(lambda: stream.read(1 << 20), b''):
                digest.update(block)
        if digest.hexdigest() != item['sha256']:
            raise SealedFailure(13, 'Source identity differs')
        paths[role] = path
    return paths


def get(path, names):
    import pyreadstat
    frame, _ = pyreadstat.read_sav(str(path), usecols=list(names), user_missing=False,
                                   apply_value_formats=False, disable_datetime_conversion=True)
    if set(frame.columns) != set(names) or len(frame) > 25000:
        raise SealedFailure(22, 'Source projection differs')
    return frame


def keys(frame, name):
    import numpy as np
    col = frame[name]
    if col.isna().any() or (col <= 0).any() or not np.equal(col, np.floor(col)).all():
        raise SealedFailure(22, 'Person key is incomplete or ambiguous')


def structure(paths, expected):
    import pyreadstat
    survey = get(paths['survey'], KEYS)
    diary = get(paths['diary'], [*KEYS, 'A2DDAY'])
    for frame in (survey, diary):
        keys(frame, 'M2ID')
    if len(survey) != expected or survey.M2ID.duplicated().any():
        raise SealedFailure(22, 'Survey person roster differs')
    days = diary[diary.A2DDAY.between(1, 8)]
    if days.duplicated(['M2ID', 'A2DDAY']).any():
        raise SealedFailure(22, 'Repeated person-day')
    group = survey.set_index('M2ID').M2FAMNUM
    linked = diary.M2ID.isin(group.index)
    if not linked.all():
        raise SealedFailure(22, 'Unlinked diary person')
    first = diary.M2ID.map(group)
    second = diary.M2FAMNUM
    valid = first.gt(0) & second.gt(0)
    if not valid.any() or first[valid].ne(second[valid]).any():
        raise SealedFailure(22, 'Inconsistent person to family link')
    _, sm = pyreadstat.read_sav(str(paths['survey']), metadataonly=True)
    _, dm = pyreadstat.read_sav(str(paths['diary']), metadataonly=True)
    if any(dm.column_names.count(k) != 1 for k in (*KEYS, 'A2DDAY', *EVENTS, *AFFECT)):
        raise SealedFailure(22, 'Diary header differs')
    flags = [int(sm.column_names.count(k) == 1) for k in TRAITS]
    if not flags[0]:
        raise SealedFailure(22, 'Neuroticism unavailable')
    if len(survey) < 11:
        raise SealedFailure(12, 'Source below release floor')
    return {'structure':[dict(neuroticism=flags[0], extraversion=flags[1], agreeableness=flags[2],
                         conscientiousness=flags[3], openness=flags[4], matched=6, n=len(survey))]}


def projected(paths):
    import numpy as np
    import pandas as pd
    import week7_sld3 as original
    survey = get(paths['survey'], [*KEYS, TRAITS[0]]).rename(columns={TRAITS[0]:'B1SNEURO'})
    diary = get(paths['diary'], ['M2ID', 'A2DDAY', *EVENTS, *AFFECT])
    frame = pd.DataFrame({'M2ID':diary.M2ID, 'B2DDAY':diary.A2DDAY})
    for i, name in enumerate(EVENTS, 1):
        observed = diary[name]
        if (~observed.dropna().isin([1, 2, 7, 8, 9])).any():
            raise SealedFailure(24, 'Unbound occurrence code')
        frame['B2DF'+str(i)] = observed
    for i, name in enumerate(AFFECT, 1):
        observed = diary[name]
        if (~observed.dropna().isin([1, 2, 3, 4, 5, 7, 8, 9])).any():
            raise SealedFailure(24, 'Unbound feeling code')
        frame['B2DC'+str(i)] = (5 - observed).where(observed.between(1, 5))
    for i in original.ITEMS[len(AFFECT):]:
        frame['B2DC'+str(i)] = np.nan
    return {'survey':survey.to_dict('records'), 'diary':frame.to_dict('records')}


def study(paths, config):
    import numpy as np
    import week7_sld3 as original
    from independent_release import Entry, decide
    tables = projected(paths)
    universe, ids, _, _, panels = original.prepare(tables, 'M2')
    # The first-wave diary is new. The probe released only the complete main survey roster.
    survey = frozenset(row['M2ID'] for row in tables['survey'])
    pairs = [(i,) for i in range(len(original.GROUPS))]
    pairs += list(combinations(range(len(original.ITEMS)), 2))
    six = {index+1:terms for index, terms in enumerate(pairs) if max(terms) < len(AFFECT)}
    supports = [np.isfinite(a['b']) & np.isfinite(b['b']) for a,b in panels[:len(AFFECT)]]
    raw = original.estimates(tables, config['draws'])
    catalog = []
    for row in raw.get('trait', []):
        k = int(row['contrast'])
        if k not in six:
            raise SealedFailure(14, 'Unbound contrast produced a number')
        mask = np.logical_and.reduce([supports[i] for i in six[k]])
        people = frozenset(p for keep,p in zip(mask,ids) if keep)
        catalog.append((k,'c'+str(k),[Entry(row,people)]))
    allowed,_ = decide(catalog, universe, [survey])
    result = [row for table in allowed.values() for row in table]
    if not result:
        raise SealedFailure(12, 'No eligible disclosable channel')
    return {'trait':sorted(result,key=lambda row:row['contrast'])}


def run(mount, out, config):
    def measure():
        paths = files(mount,config['files'])
        check = structure(paths,config['survey_people'])
        return check if config['mode']=='structure' else study(paths,config)
    first = measure()
    if measure() != first:
        raise SealedFailure(14, 'Independent source replay differs')
    write_tables(out,first)
