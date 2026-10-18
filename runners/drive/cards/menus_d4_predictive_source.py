"""Canonical-source successor to the unchanged D4 correction predictor.

DESIGN CHECK: LESSONS3-5. Canonical unique choice and exact feature text must
agree before eligibility. The original P5 deterministic classes, training
support and correction vectors remain. Changed population/source refuses.
"""
import copy
from pathlib import Path
from . import events_d4_sources as original
from . import menus_canonical_selection as canonical
from .menus_io import read,sha256,input_hashes
from runners.stage14.common import digest

INPUTS=original.INPUTS|{'selection_reader','selection_complete','visibility'}


def load(inputs):
    if set(inputs)!=INPUTS:raise ValueError('canonical D4 input roster differs')
    data=original.source({k:inputs[k] for k in original.INPUTS});audit=canonical.load(inputs)
    path=Path(inputs['visibility']);complete=read(inputs['content_complete'])
    name=path.resolve().relative_to(Path(inputs['content_complete']).parent.resolve()).as_posix()
    if complete['outputs'].get(name)!=sha256(path):raise ValueError('D4 visibility source changed')
    ledger=read(path)
    if len(ledger)!=len(data['vectors']):raise ValueError('D4 visibility/vector coverage differs')
    sessions=copy.deepcopy(list(data['sessions'].values()));proofs=[]
    for session in sessions:
        for row in session['rows']:
            proof=audit.join(row);positions=proof['canonical_positions'];selected=row['handling'] in ('accept','edit')
            if selected and (len(positions)!=1 or not proof['verified_insertion'] or not proof['canonical_usable']):
                raise ValueError('D4 canonical choice not uniquely supported')
            old=[i for i,text in enumerate(row['menu']) if text==row['inserted']]
            if selected and len(old)!=1:raise ValueError('D4 canonical source changes original support')
            if not selected and positions:raise ValueError('D4 unselected row has choice')
            feature=data['records'][row['key']]
            if len(feature['options'])!=len(row['menu']):raise ValueError('D4 offer coverage differs')
            for index,text in zip(feature['options'],row['menu']):
                scope=ledger[index]
                if scope['role']!='suggestion' or scope['text_sha256']!=digest(text):raise ValueError('D4 offer vector/text association differs')
            if selected:row['inserted']=row['menu'][positions[0]]
            proofs.append(dict(key=row['key'],writer=row['writer'],session=row['session'],ordinal=row['ordinal'],
                canonical_positions=positions,prepared_positions=proof['prepared_positions'],
                choice_changed=proof['index_status']=='proven_disjoint_choice',
                canonical_sha256=proof['canonical_sha256'],raw_source_sha256=proof['raw_source_sha256']))
    data['sessions']={s['session']:s for s in sessions}
    data['splits'],data['excluded']=original.chronological_partitions(sessions)
    data['choice_proofs']=proofs;data['identity']=input_hashes(inputs)
    return data


def writer_data(writer,data,config):
    metadata,units=original.writer_data(writer,data,config)
    by_key={r['key']:r for r in data['choice_proofs']}
    metadata['canonical_choice_audit']={phase:[by_key[r['key']] for r in metadata[phase]] for phase in ('calibration','test')}
    return metadata,units
