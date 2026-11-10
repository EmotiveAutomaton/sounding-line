"""MD4: identifier-stripped Jangraw first-block source projection.

DESIGN CHECK: LESSONS 2-5; CONTROLS 6-7. Read task headers, never infer a
condition or calendar from filenames. Author-derived protocol/response times
are elapsed task coordinates, not wall-clock timestamps. Missing events and
ambiguous participant joins are counted exclusions. No mood effect is fitted.
Derived from Jangraw et al. (2023), NIMH public-domain work; see MD4.md.
"""
from __future__ import annotations
from collections import Counter, defaultdict
from decimal import Decimal, InvalidOperation
import csv, hashlib, hmac, json, math, time
from pathlib import Path
import numpy as np
import pandas as pd

ARCHIVE_SHA = 'f1c470a3ec8caddf35d2082a0c9f4fc33b4d79edf2ce77caaa1078638fb8afd4'
MANIFEST_SHA = '36b2e7653d23282c36187a0271ebf2e4d2c9113352080c74acc6a7b63f933a07'
REST = ('COVID01','Expectation-12min','Expectation-7min','Numbers','Recovery1',
        'RecoveryInstructed1Freq0p25','RecoveryInstructed1Freq0p5',
        'RecoveryInstructed1Freq2','RecoveryInstructed1','RestDownUp','Stability01-Rest')
COHORTS = dict.fromkeys(REST,'rest') | {'Motion':'visuomotor','MotionFeedback':'visuomotor',
                                    'Stability01-RandomVer2':'random_gambling'}
DEFAULTS = dict(freqMult=1.,getAnswerDur=3.,showChoiceDur=4.,showResultDur=1.,
                isiDur=1.,moodQuestionDur=1.5,moodRatingDur=4.5,itiDur=2.,iriDur=16.5)
FIELDS = set(DEFAULTS) | {'participant','expName','condition','choice','choiceKey.rt','returnLoop.ran',
                        'doRating','doRatingCond','trialHappyLoop.ran','blockLoop.ran'}
for prefix in ('happy','blockHappy'):
    FIELDS |= {prefix+'Slider.response',prefix+'Slider.rt',prefix+'Resp.keys',prefix+'Resp.rt'}

def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
    return h.hexdigest()

def save(path,value):
    Path(path).parent.mkdir(parents=True,exist_ok=True)
    Path(path).write_text(json.dumps(value,sort_keys=True,indent=2,allow_nan=False)+'\n',encoding='utf8')

def number(value):
    try:
        v=float(value)
        return v if math.isfinite(v) else None
    except (ValueError,TypeError):return None

def token(value):
    """Local anonymous-code join only; never returned in exported records."""
    text=str(value).strip()
    if not present(value):return ''
    try:
        v=Decimal(text)
        return str(int(v)) if v.is_finite() and v==v.to_integral_value() else text
    except InvalidOperation:return text

def truth(value):
    return str(value).strip().lower() in ('true','1','1.0')

def present(value):
    return value is not None and str(value).strip().lower() not in ('','nan','none','null','na')

def rows(path, independent=False, fields=FIELDS):
    if independent:
        frame=pd.read_csv(path,dtype=str,keep_default_na=False,usecols=lambda c:c in fields)
        return list(frame.columns),frame.to_dict('records')
    with Path(path).open(newline='',encoding='utf-8-sig') as f:
        reader=csv.DictReader(f);header=reader.fieldnames or []
        return header,[{k:v for k,v in row.items() if k in fields} for row in reader]

def task_header(header):
    return any(k in header for k in ('blockHappySlider.response','blockHappyResp.keys'))

def event_projection(header, data, cohort, independent=False):
    if cohort not in COHORTS:raise ValueError('unsupported cohort')
    numeric_keys = 'happySlider.rt' not in header
    p=DEFAULTS.copy();audit=Counter()
    for key in p:
        found=[number(r.get(key)) for r in data if number(r.get(key)) is not None]
        if found:
            if len(set(found))!=1:raise ValueError('changing timing parameter')
            p[key]=found[0]
        elif key=='iriDur':p[key]=15/p['freqMult'] if p['freqMult']>0 else float('nan')
        else:audit['default_protocol_parameters']+=1
    if any(not math.isfinite(x) or x<0 for x in p.values()):raise ValueError('invalid timing parameter')
    if p['freqMult']<=0:raise ValueError('invalid frequency multiplier')
    if cohort=='Stability01-RandomVer2':
        condition={str(r.get('condition','')).strip().lower() for r in data}-{''}
        if condition!={'random'}:raise ValueError('random condition metadata mismatch')
    if cohort.startswith('Motion'):
        expected='Mmi_Motion_Feedback' if cohort=='MotionFeedback' else 'Mmi_Motion'
        if {r.get('expName','') for r in data}-{''}!={expected}:raise ValueError('visuomotor metadata mismatch')
    # First block only. Event increments reproduce GetMmiRatingsAndTimes;
    # unlike the author Numbers branch, missing responses are never filled forward.
    clock=0.;block=-1;events=[];deltas=[];ratings=[];types=[]
    def rating(row,prefix):
        value=number(row.get(prefix+('Resp.keys' if numeric_keys else 'Slider.response')))
        if value is not None and numeric_keys:value=(value-1)/8
        return value
    def rt(row,prefix,maximum):
        value=number(row.get(prefix+('Resp.rt' if numeric_keys else 'Slider.rt')))
        if value is None:audit['response_time_protocol_fallbacks']+=1;return maximum
        if value<0:raise ValueError('negative response time')
        return value
    for row in data:
        base=rating(row,'blockHappy')
        if base is not None:
            block+=1
            if block>0:break
            delta=p['moodQuestionDur']+rt(row,'blockHappy',p['moodRatingDur'])
            clock+=delta;deltas.append(delta);ratings.append(base);types.append('baseline')
            events.append((clock,base,'baseline'))
        if block<0:continue
        choice=present(row.get('choice'));value=rating(row,'happy')
        is_rest=number(row.get('returnLoop.ran')) is not None if 'returnLoop.ran' in header else (value is not None and not choice)
        if 'returnLoop.ran' not in header:audit['inferred_return_event_rows']+=int(is_rest)
        planned=(is_rest or str(row.get('doRating','')).strip().lower()=='yes' or number(row.get('trialHappyLoop.ran')) is not None)
        if planned and value is None:raise ValueError('missing planned rating event')
        if choice:
            choice_rt=number(row.get('choiceKey.rt'))
            if choice_rt is None:choice_rt=p['getAnswerDur'];audit['choice_time_protocol_fallbacks']+=1
            if choice_rt<0:raise ValueError('negative choice time')
            delta=p['showChoiceDur']+p['showResultDur']+p['itiDur']+choice_rt
            clock+=delta;deltas.append(delta);ratings.append(None);types.append('choice')
        if value is not None:
            if COHORTS[cohort]=='random_gambling' and is_rest:raise ValueError('random cohort first block is rest')
            if COHORTS[cohort]!='random_gambling' and not is_rest:raise ValueError('nonrest event in opening rest/task block')
            delta=(p['iriDur'] if is_rest else p['isiDur'])+p['moodQuestionDur']+rt(row,'happy',p['moodRatingDur'])
            clock+=delta;deltas.append(delta);ratings.append(value);types.append('rating')
            events.append((clock,value,'rating'))
    if independent:
        cumulative=np.cumsum(np.array(deltas,dtype=float))
        events=[(float(t),float(v),kind) for t,v,kind in zip(cumulative,ratings,types) if v is not None]
    if not events or events[0][2]!='baseline':raise ValueError('missing initial block rating')
    if any(v<0 or v>1 for _,v,_ in events):raise ValueError('mood outside unit interval')
    if any(b[0]<=a[0] for a,b in zip(events,events[1:])):raise ValueError('nonincreasing event clock')
    origin=events[0][0]
    projected=[dict(minute=(t-origin)/60.,mood=v,rating_order=i,event_kind=kind) for i,(t,v,kind) in enumerate(events)]
    audit['ratings']=len(projected);audit['numeric_key_tasks']=int(numeric_keys)
    return projected,dict(audit)

def validate(source,inputs,constructed=False):
    manifest=source/'SANITIZATION_MANIFEST.json'
    if not constructed and sha(manifest)!=MANIFEST_SHA:raise ValueError('sanitized manifest pin mismatch')
    m=json.loads(manifest.read_text('utf8'))
    if not constructed and (m['archive_sha256']!=ARCHIVE_SHA or not m['archive_crc_passed']):raise ValueError('archive verification mismatch')
    mapping_path=Path(inputs['cohort_map']);mapping=json.loads(mapping_path.read_text('utf8'))
    if sha(mapping_path)!=inputs['cohort_map_sha256']:raise ValueError('cohort mapping pin mismatch')
    salt=Path(inputs['salt']).read_bytes()
    if len(salt)!=32:raise ValueError('identity salt size mismatch')
    return m,mapping['cohort_data_checks'],salt

def prepare(output,inputs,config,independent=False):
    source=Path(inputs['source']);constructed=bool(config.get('constructed_fixture',False))
    m,mapping,salt=validate(source,inputs,constructed)
    if constructed and not m.get('constructed_fixture'):raise ValueError('fixture flag on real source refused')
    audit=Counter();by_cohort={};complete={};input_pins={}
    for cohort in COHORTS:
        if cohort not in mapping:audit['cohorts_without_data_check']+=1;continue
        record=mapping[cohort];path=source/record['file']
        if sha(path)!=record['sha256']:raise ValueError('DataCheck pin mismatch')
        input_pins[record['file']]=record['sha256']
        header,check=rows(path,independent,{'participant','isComplete'})
        if not {'participant','isComplete'}<=set(header):raise ValueError('DataCheck completion fields missing')
        grouped=defaultdict(list)
        for row in check:grouped[token(row.get('participant',''))].append(truth(row.get('isComplete')))
        complete[cohort]={key for key,flags in grouped.items() if key and all(flags)}
        audit['conflicting_completion_statuses']+=sum(len(set(v))>1 for v in grouped.values())
        audit['DataCheck_complete_records']+=len(complete[cohort])
        by_cohort[cohort]=Counter(complete_records=len(complete[cohort]))
    files=[r for r in m['files'] if r.get('group')=='PilotData' and r.get('cohort') in complete and r['file'].endswith('.csv')]
    candidates=defaultdict(list);cpu_started=time.process_time();wall_started=time.monotonic()
    for index,record in enumerate(files):
        if not independent and index and index%20==0:
            progress=dict(processed_files=index,total_files=len(files),cpu_seconds=time.process_time()-cpu_started,
                          wall_seconds=time.monotonic()-wall_started,scientific_effect_computed=False)
            save(Path(output)/'PROGRESS.json',progress)
            if index>=math.ceil(.05*len(files)) and not (Path(output)/'PILOT.json').exists():
                save(Path(output)/'PILOT.json',dict(progress,forecast_cpu_seconds=progress['cpu_seconds']*len(files)/index,
                                                   basis='first completed file boundary at or above5% of eligible source files'))
            if (Path(output)/'YIELD_REQUEST.json').exists():
                save(Path(output)/'CHECKPOINT.json',dict(progress,restart_from_source_required=True))
                return dict(status='yielded',reason='owner request',checkpoint='CHECKPOINT.json',restart_from_source_required=True)
        cohort=record['cohort'];path=source/record['file'];counts=by_cohort[cohort]
        if sha(path)!=record['sha256']:raise ValueError('working task pin mismatch')
        input_pins[record['file']]=record['sha256']
        # Read the header before selecting columns; survey contents are not loaded.
        with path.open(newline='',encoding='utf-8-sig') as f:header=next(csv.reader(f),[])
        if not task_header(header):counts['non_task_files']+=1;continue
        header,data=rows(path,independent);counts['task_files']+=1
        keys={token(r.get('participant','')) for r in data if present(r.get('participant',''))}
        if len(keys)!=1:counts['ambiguous_task_identity']+=1;continue
        person=next(iter(keys))
        if person not in complete[cohort]:counts['not_completed_in_DataCheck']+=1;continue
        private_key=hmac.new(salt,(cohort+'\0'+person).encode(),hashlib.sha256).hexdigest()
        try:projected,diagnostics=event_projection(header,data,cohort,independent)
        except ValueError as error:
            counts['excluded_'+str(error).replace(' ','_')]+=1;continue
        candidates[(cohort,private_key)].append((projected,diagnostics))
    result=[]
    for (cohort,key),entries in sorted(candidates.items()):
        counts=by_cohort[cohort];canon=[json.dumps(e[0],sort_keys=True) for e in entries]
        if len(set(canon))>1:counts['conflicting_task_copies_excluded']+=len(entries);continue
        counts['identical_task_copies_collapsed']+=len(entries)-1
        projected,diagnostics=entries[0];counts.update(diagnostics);counts['retained_people']+=1
        for row in projected:result.append(dict(person=key,cohort=cohort,condition=COHORTS[cohort],**row))
    frame=pd.DataFrame(result,columns=['person','cohort','condition','minute','mood','rating_order','event_kind'])
    counts={'overall':dict(audit),'cohorts':{c:dict(v) for c,v in by_cohort.items()},'ratings':len(frame),
            'people':int(frame.person.nunique()),'constructed':constructed,'timing':'author protocol durations plus actual response times; opening block only'}
    if independent:return frame,counts,input_pins
    output=Path(output);output.mkdir(parents=True,exist_ok=True);frame.to_parquet(output/'PRIVATE_RATINGS.parquet',index=False)
    save(output/'COUNTS.json',counts)
    if not (output/'PILOT.json').exists():save(output/'PILOT.json',dict(processed_files=len(files),total_files=len(files),cpu_seconds=time.process_time()-cpu_started,basis='entire source smaller than first20file boundary'))
    receipt=dict(complete=True,constructed=constructed,archive_sha256=m['archive_sha256'],manifest_sha256=sha(source/'SANITIZATION_MANIFEST.json'),
                 cohort_map_sha256=sha(inputs['cohort_map']),input_files=input_pins,ratings_sha256=sha(output/'PRIVATE_RATINGS.parquet'),
                 scientific_result=False,derivative='Sounding Line source projection derived from Jangraw et al. 2023; acknowledges authors and NIMH')
    save(output/'SOURCE.json',receipt);return counts

def execute(output,inputs,config):return prepare(output,inputs,config)

def verify(output,inputs,config):
    output=Path(output);receipt=json.loads((output/'SOURCE.json').read_text('utf8'))
    if receipt['ratings_sha256']!=sha(output/'PRIVATE_RATINGS.parquet'):raise ValueError('projected ratings changed')
    frame,counts,pins=prepare(output,inputs,config,True)
    pd.testing.assert_frame_equal(frame,pd.read_parquet(output/'PRIVATE_RATINGS.parquet'),check_exact=True)
    if counts!=json.loads((output/'COUNTS.json').read_text('utf8')) or pins!=receipt['input_files']:raise ValueError('source replay mismatch')
    record=dict(verified=True,ratings=len(frame),all_values_checked=True,independent_csv_reader=True,independent_cumulative_event_clock=True)
    save(output/'VERIFIED.json',record);return record
