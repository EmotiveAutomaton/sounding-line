"""Period-specific Form L adapter for the commissioned clinical diary."""
from pathlib import Path

import numpy as np
import pandas as pd

from . import week6_person_small_v1 as pbk
from . import week6_ld12_common_v1 as core
from .batch_runtime import filehash, read

COLUMNS = ('id', 'study_period', 'fearful', 'sad', 'cheerful')
SHA = '811f41aeaeb8dbfaa67ca8f8a5387d222701c42fc316f9eb3d61326d138bc8ee'
MEMBER_MANIFEST = 'f44315ac9223f0c32cfecafe19a036aca19ec9e417f9bbbe2c173703188f78e8'


def local_source(pointer):
    root = Path(pointer['root'])
    if not pointer['repair_hold'] or root.drive.lower() != 'c:' or root.name != pbk.ROOT_NAME:
        raise ValueError('Clinical diary requires the temporary workstation root')
    if filehash(root/'DRT1_MANIFEST.json') != pbk.MANIFEST:
        raise ValueError('Temporary root manifest changed')
    member = root/'incoming'/'openesm-0010'
    manifest = member/'MANIFEST.json'
    if filehash(manifest) != MEMBER_MANIFEST or read(manifest)['licence'] != 'cc-by-nc-4.0':
        raise ValueError('Release manifest changed')
    source = member/'0010_geschwind_ts.tsv'
    if filehash(source) != SHA:
        raise ValueError('Time series changed')
    return source


def prepare(frame, period):
    source = frame.loc[frame.id.notna() & frame.id.ne('')].copy()
    phases = pd.to_numeric(source.study_period, errors='raise')
    if not phases.dropna().isin((0, 1)).all():
        raise ValueError('Undocumented period')
    source = source.loc[phases.eq(period)]
    people, ids = np.unique(source.id.astype(str), return_inverse=True)
    values = source.loc[:, list(COLUMNS[2:])].apply(pd.to_numeric, errors='raise')
    if (~values.isin(range(1, 8)) & values.notna()).any().any():
        raise ValueError('Undocumented feeling code')
    keep = values.notna().all(axis=1).to_numpy()
    v = values.to_numpy(dtype=float)[keep]
    support = dict(people=int(np.unique(ids[keep]).size), rows=int(keep.sum()), eligible=len(source))
    data = core.Prepared(len(people), dict(period=period, panels={'L': support}))
    data.panels['L'] = pbk.Panel(ids[keep], v[:, :2], v[:, 2:], ('fearful', 'sad'), ('cheerful',))
    for name in ('fearful', 'sad'):
        core.metric(data, 'L/cheerful/'+name, 'Cheerful on '+name, support)
    core.metric(data, 'L/contrast', 'Fear minus sadness for cheerful mood', support, role='registered')
    return data

