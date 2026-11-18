"""Versioned 0062 source-tag/day adapter; original source modules unchanged.

DESIGN CHECK (LESSONS 2, 3, 5): official STECCO codebook p3 defines day0
0..13 as study days 1..14. Preserve source codes; derive analysis day = code+1
only for the pinned 0062 release. Null/alternative numerical results receive
identical mapping. Changed source era, invalid day, unknown table tag or
conflicting duplicate refuses; source/clock identity is never guessed from
participant values. Count excluded source rows and retain missing outcomes.
"""
from copy import deepcopy
from pathlib import Path
import numpy as np
import pandas as pd
if __package__:
    from . import es_source_v1 as original
else:
    import es_source_v1 as original

DAILY_EVENTS=original.DAILY_EVENTS
DAILY_FEELINGS=original.DAILY_FEELINGS
sha256=original.sha256
rating=original.rating
study_day=original.study_day
interaction_people=original.interaction_people
need=original.need

_PROFILE={
    'schema':'ES_0062_STECCO_DAY_MAPPING_V1',
    'member':'0062','dataset_version':'1.0.0','zenodo_record':17347975,
    'raw_ts_sha256':'1c27ae6f25d972f870c836791a9906493cab4ce395c2d70754329750c4019293',
    'raw_ts_bytes':6917023,
    'dictionary_sha256':'3768e05d0c48fe8a3b8a090c3ca1962703049aff7c8c8bdb18590dffe3297bbe',
    'official_codebook_sha256':'2d0f95549f9a7388491ed371abb2dcc4bae9c386f4b96e84dc58d7ab0e46af38',
    'official_codebook_page':3,
    'documentary_cleaning_script_sha256':'7bd25bb85511dcff86baa2d4110a2815838d671aafb6b9ad8560ca625f35dbb5',
    'source_day':'original zero-based integer 0..13',
    'analysis_day':'source_day + 1, explicitly documented study day 1..14',
    'select_source_tag':'daily','other_source_tag':'esm',
    'wave_reset':False,'timestamp_reconstruction':False,
}


def mapping_profile():
    return deepcopy(_PROFILE)


def validate_daily_mapping(config,intake):
    """Metadata only, before any source row/byte read in a new phase."""
    need(config['member']=='0062' and config['card']=='ES2','daily mapping scope differs')
    need(config['source_layout_review'].get('day_mapping')==_PROFILE,
         '0062 day mapping or documentary source era differs')
    member=intake['members']['0062'];pin=config['source_pin']
    need(member['version']==_PROFILE['dataset_version']
         and member['zenodo_record']==_PROFILE['zenodo_record'],'0062 source release differs')
    need(member['metadata_pins']['DOCUMENTED_METADATA.json']==_PROFILE['dictionary_sha256'],
         '0062 dictionary era differs')
    need(pin==member['raw_ts_pin_from_receipt_only']
         and pin['sha256']==_PROFILE['raw_ts_sha256'] and pin['bytes']==_PROFILE['raw_ts_bytes'],
         '0062 original source identity differs')
    validate_missing_tokens(config['missing_tokens'])


def validate_missing_tokens(tokens):
    need(type(tokens) is list and all(type(x) is str for x in tokens),
         'explicit reviewed missing-token list required')
    for token in tokens:
        try:value=float(token)
        except ValueError:continue
        need(not (np.isfinite(value) and value==int(value) and 0<=value<=13),
             'missing token would remove a documented study day')


def source_day(value,missing_tokens):
    if value in missing_tokens:return np.nan
    need(not isinstance(value,(bool,np.bool_)),'invalid original 0062 day code')
    try:number=float(value)
    except (TypeError,ValueError):raise ValueError('invalid original 0062 day code') from None
    need(np.isfinite(number) and number==int(number) and 0<=number<=13,
         'invalid original 0062 day code')
    return int(number)


def fields(member,card):
    base=original.fields(member,card)
    return base+('source',) if member=='0062' else base


def selected_frames(path,pin,member,card,missing_tokens,guard=lambda:None):
    if member!='0062':
        yield from original.selected_frames(path,pin,member,card,missing_tokens,guard)
        return
    validate_missing_tokens(missing_tokens)
    wanted=fields(member,card);path=Path(path)
    need(path.is_file() and path.stat().st_size==pin['bytes'],'source size mismatch')
    need(sha256(path,guard)==pin['sha256'],'source hash mismatch')
    for frame in pd.read_csv(path,sep='\t',usecols=list(wanted),dtype=str,
                             keep_default_na=False,na_filter=False,chunksize=20000):
        need(set(frame.columns)==set(wanted),'source whitelist mismatch')
        guard();yield frame.loc[:,list(wanted)]


def daily_people(frames,missing_tokens,layout):
    """Only source=='daily'; copy records before deterministic day projection.

    Raw source codes are never overwritten on disk or in the caller's frames.
    The returned people additionally retain source_days privately; core consumes
    only their explicitly derived days. Missing day remains missing. The old
    duplicate, complete-case, >=10-report and reliability rules are unchanged.
    """
    validate_missing_tokens(missing_tokens)
    counts={'input_source_rows':0,'daily_source_rows':0,'esm_rows_excluded':0,
            'daily_zero_code_rows':0,'daily_missing_day_rows':0}
    def projected():
        for frame in frames:
            need(set(frame.columns)==set(fields('0062','ES2')),'unexpected daily source columns')
            counts['input_source_rows']+=len(frame)
            need(set(frame['source'])<={'esm','daily'},'unknown source table tag')
            counts['esm_rows_excluded']+=int((frame['source']=='esm').sum())
            selected=frame.loc[frame['source']=='daily',list(original.fields('0062','ES2'))].copy()
            counts['daily_source_rows']+=len(selected)
            derived=[]
            for value in selected['day']:
                day=source_day(value,missing_tokens)
                if np.isnan(day):
                    counts['daily_missing_day_rows']+=1;derived.append(value)
                else:
                    counts['daily_zero_code_rows']+=int(day==0);derived.append(str(day+1))
            selected['day']=derived
            yield selected
    people,original_counts=original.daily_people(projected(),missing_tokens,layout)
    for person in people:person['source_days']=[int(day)-1 for day in person['days']]
    return people,dict(original_counts,source_selection=counts,day_mapping=mapping_profile(),
                       original_day_codes_retained_in_memory=True,
                       source_days_exported=False,analysis_day_is_explicit_derivation=True)
