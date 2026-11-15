"""Authorized column projection for Week 6 IN14/IN16; no outcome calculations.

DESIGN CHECK: LESSONS 2/3, CONTROLS 6/7. Authenticate the complete predecessor,
retain all surveys for adjacency, and require exact coverage of its real-event
projection. Demographic and narrative columns are never requested or decoded.
"""
from pathlib import Path
import hashlib
import json
import zipfile
import numpy as np
import pandas as pd
from . import week5_in as original
from . import week5_in11_math_v1 as duration
from . import week5_in12_math_v1 as inventory
from . import week5_engine_export_io as seal
from . import week5_qualification_io as io
from . import week6_in14_math_v1 as carry

TABLE_PIN = '196fe2a4f72b36ae91516ee5caf762cb3ba04f7d69b6da4e53958587d44c1638'
ELIGIBILITY = Path(__file__).resolve().parents[3]/'docs/design/stage-15/week6/IN14_QUESTIONNAIRE_ELIGIBILITY_V1.json'
ELIGIBILITY_PIN = 'afe772b9a0f9dcf6e3bd685a7894ae8624c40a6d52e9866d2112c65c4e133ad2'
SCOPES = ('real-event-primary', 'all-report-reference')


def questionnaire_check(archive):
    if io.sha(ELIGIBILITY) != ELIGIBILITY_PIN:
        raise ValueError('Reviewed questionnaire inventory changed')
    document = json.loads(ELIGIBILITY.read_text(encoding='utf8'))
    observed = sorted(n for n in archive.namelist() if n.startswith('questionnaires/generation/') and n.endswith('.pdf'))
    if observed != [r['member'] for r in document['questionnaires']]:
        raise ValueError('Questionnaire coverage differs')
    for row in document['questionnaires']:
        if hashlib.sha256(archive.read(row['member'])).hexdigest() != row['sha256']:
            raise ValueError('Reviewed blank questionnaire changed')
        if row['eligible'] and not (row['current_state_page'] < row['named_prompt_page'] and row['current_state_page'] < row['recall_page']):
            raise ValueError('Current state must precede prompt naming and recall')
    return document['eligible_rounds']


def trait_map(frame):
    """IN12's unique complete two-item pair per writer, without outcome selection."""
    result={}; dispositions={'available':0,'missing':0,'conflicting_source_items':0}
    for key,part in frame.groupby('prolific_id',sort=True):
        pairs=part[['anxious','calm']].dropna().drop_duplicates()
        status='available' if len(pairs)==1 else 'missing' if pairs.empty else 'conflicting_source_items'
        result[key]=float(inventory.item_score(*pairs.iloc[0])) if status=='available' else np.nan
        dispositions[status]+=1
    return result,dispositions


def load(inputs, card, source_scope):
    if set(inputs) != {'source_run'} or source_scope not in SCOPES or card not in ('IN14','IN16'):
        raise ValueError('Exact qualified IN source and declared source scope required')
    root,plan,_=seal.complete(inputs['source_run'],'runners.drive.cards.week5_in')
    if plan['config'].get('phase')!='prepare':
        raise ValueError('Original IN preparation required')
    path=Path(plan['inputs']['source']); salt_path=Path(plan['inputs']['salt'])
    if io.sha(path)!=original.SOURCE_SHA or io.sha(salt_path)!=plan['pins'].get(str(salt_path)) or io.sha(root/'output/generation.parquet')!=TABLE_PIN:
        raise ValueError('Pinned source, salt or qualified table changed')
    salt=salt_path.read_bytes()
    if len(salt)!=32: raise ValueError('Wrong private salt length')
    shared=['text_id','prolific_id','emotion','intensity',*original.APPRAISALS]
    extra=['event_duration','emotion_duration','anxious','calm','did_you_lie?']
    if card=='IN14': extra += ['timestamp','round_number',*carry.PRIOR]
    with zipfile.ZipFile(path) as archive:
        rounds=questionnaire_check(archive) if card=='IN14' else []
        with archive.open('corpus/crowd-enVent_generation.tsv') as stream:
            raw=pd.read_csv(stream,sep='\t',usecols=shared+extra,dtype=str,keep_default_na=False)
    if len(raw)!=6600 or raw.text_id.duplicated().any(): raise ValueError('Original source inventory differs')
    for column,namespace in [('text_id','crowd-text'),('prolific_id','crowd-person')]:
        raw[column]=raw[column].map(lambda v:original.salted(v,salt,namespace))
    numeric=['intensity',*original.APPRAISALS]+(list(carry.PRIOR) if card=='IN14' else [])
    for column in numeric:
        raw[column]=pd.to_numeric(raw[column],errors='raise')
        if not raw[column].isin([1,2,3,4,5]).all(): raise ValueError('Undocumented rating scale')
    for column in ('anxious','calm'):
        raw[column]=pd.to_numeric(raw[column].mask(raw[column].isin(['','--'])),errors='raise')
        if not raw.loc[raw[column].notna(),column].between(1,7).all(): raise ValueError('Undocumented trait scale')
    actual='The event really happened in my life.'
    invented='I never experienced that event, but I really imagined how it would make me feel.'
    if not raw['did_you_lie?'].isin([actual,invented,'--']).all(): raise ValueError('Unmapped truthfulness answer')
    raw['source_qualified']=raw['did_you_lie?'].ne(invented)
    qualified=pd.read_parquet(root/'output/generation.parquet',columns=shared).sort_values('text_id').reset_index(drop=True)
    candidate=raw.loc[raw.source_qualified,shared].sort_values('text_id').reset_index(drop=True)
    pd.testing.assert_frame_equal(candidate,qualified,check_dtype=False,check_exact=True)
    traits,dispositions=trait_map(raw);raw['N']=raw.prolific_id.map(traits)
    raw['event_duration_rank']=raw.event_duration.map(duration.rank)
    raw['emotion_duration_rank']=raw.emotion_duration.map(lambda v:duration.rank(v,True))
    raw['no_emotion_reported']=raw.emotion_duration.eq('I had none')
    support={'all_reports':len(raw),'qualified_real_event_reports':int(raw.source_qualified.sum()),
             'declared_invented_reports':int(raw['did_you_lie?'].eq(invented).sum()),
             'truthfulness_unasked_retained':int(raw['did_you_lie?'].eq('--').sum()),
             'personality_writers':dispositions}
    raw=raw.drop(columns=['anxious','calm','did_you_lie?','event_duration','emotion_duration'])
    if source_scope=='all-report-reference': raw['source_qualified']=True
    if card=='IN16': raw=raw.loc[raw.source_qualified].copy()
    identity={'archive_sha256':original.SOURCE_SHA,'qualified_table_sha256':TABLE_PIN,
              'source_complete_sha256':io.sha(root/'COMPLETE.json'),'source_plan_sha256':io.sha(root/'PLAN.json'),
              'salt_sha256':io.sha(salt_path),'source_scope':source_scope,'source_support':support,
              'eligible_rounds':rounds,'questionnaire_review_sha256':ELIGIBILITY_PIN if card=='IN14' else None,
              'projected_columns':shared+extra,'demographic_columns_read':False,'narrative_columns_read':False,
              'license':'CC BY 4.0','citation':'doi:10.1162/coli_a_00461'}
    return raw.sort_values('text_id').reset_index(drop=True),identity
