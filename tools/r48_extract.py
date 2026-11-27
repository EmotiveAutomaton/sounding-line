"""Project the retained, aggregate-only November releases onto the report schema."""
import csv
import hashlib
import io
import json
from pathlib import Path

from r48_reports import FIELDS, OUT, ROOT

BASE = ROOT / 'results/phase_2_4_stage_15'
RAW7 = BASE / 'raw/drive-week7-20261122'
RAW8 = BASE / 'raw/drive-week8-20261127'
RESTRICTED = ROOT / '.agent-state/drive-20261115/week7-phase1/restricted'


def digest(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def read(p):
    return json.loads(p.read_text(encoding='utf8'))


def checked(p, expected):
    if digest(p) != expected:
        raise ValueError(f'Receipt differs for {p.name}')
    return p


def verified(stem):
    d = next(RAW7.glob(stem))
    path = d / 'verify_INTERNAL.json'
    complete = read(d/'COMPLETE.json')
    checked(path, complete.get('verified_result') or complete['result_sha256'])
    checked(d/'execute_INTERNAL.json',digest(path))
    return read(path)


def csvrows(path):
    with path.open(encoding='utf-8-sig', newline='') as src:
        return list(csv.DictReader(src))


def row(label, point=None, interval=(), n=None, obs=None, reading='descriptive', unit='people'):
    lo,hi = interval or ('','')
    return [label, point,lo,hi,n,unit,obs,reading]


def write(key, rows):
    stream = io.StringIO(newline='')
    writer = csv.writer(stream,lineterminator='\n')
    writer.writerow(FIELDS)
    writer.writerows(rows)
    (OUT / (key+'.csv')).write_bytes(stream.getvalue().encode('utf8'))


def public_sources():
    d = verified('GAT1-Columbia-keyed-dictionary-repair-*')
    write('GAT1',[row('Rating by shared interest',d['point'],d['interval'],d['raters'],d['analysed_rows'],'positive')])
    d = verified('GAT2-Columbia-relative-mean-*')
    write('GAT2',[row(k.capitalize()+' advantage',v['coefficient'],v['interval'],d['support']['analysed_raters'],
                      d['support']['analysed_rows'],'positive' if k=='mean' else 'descriptive') for k,v in d['rows'].items()])
    d = verified('CRV1-Hilton-Moser-*')['paired']
    write('CRV1-pitch',[row(label,d['contrasts'][k]['mean'],d['contrasts'][k]['interval'],d['n'],2*d['n'],'positive')
                        for k,label in [('pitch_height','Pitch height, semitones'),('pitch_spread','Pitch spread, semitones')]])
    d=verified('CRV1-Rosslund-*')
    write('CRV1-timing',[row(label,d[k]['mean'],d[k]['interval'],d[k]['people'],d[k]['valid_rows'],sign)
                         for k,label,sign in [('vowel_ms','Target vowel duration, ms','positive'),
                                              ('syllables_per_phonation_second','Syllables per phonation second','negative')]])
    d=verified('PSD2-everyday-checklist-blank-repair-*')['pairs']
    write('PSD2-checklist',[row('Pride with '+label,d[k]['ratio'],d[k]['interval'],d[k]['eligible_people'],d[k]['eligible_prompts'])
                            for k,label in [('Embarassment','embarrassment'),('Guilt','guilt')]])
    d=verified('UGM1-EPE-responder-*')
    rows=[]
    for k,label,i,sign in [('offer','Valence, offer',0,'descriptive'),('gap','Valence, expectation gap',0,'positive'),
                            ('change','Valence, offer change',0,'descriptive'),('larger_negative_gap','Arousal, negative surprise magnitude',2,'positive'),
                            ('larger_positive_gap','Arousal, positive surprise magnitude',1,'positive')]:
        v=d['terms'][k]
        model=d['models'][i]
        rows.append(row(label,v['estimate'],v['interval'],model['varying_players'],model['complete_trials'],sign))
    write('UGM1',rows)
    name='TWO1_AGREEMENT.csv'
    rows=[]
    for r in csvrows(checked(RESTRICTED/name,read(RESTRICTED/'MANIFEST.json')['outputs'][name])):
        k=r['comparison']
        sign={'between_minus_within':'positive','within_minus_half_between':'negative'}.get(k,'descriptive')
        n=r['repeat_people'] if k=='within' else r['people']
        rows.append(row(r['quantity']+', '+k.replace('_',' '),r['estimate'],[r['lower'],r['upper']],n,r['occasions'],sign))
    write('TWO1',rows)


def sealed_table(unit,name):
    path = RAW7 / unit
    receipt = read(path/'COMPLETE.json')
    if not receipt['verified'] or not receipt['replay']:
        raise ValueError('Missing sealed replay receipt')
    return csvrows(checked(path/'gated-return'/name,receipt['aggregates'][name]))


def released_sealed():
    data=sealed_table('CAD1-primary-20261125','pace.csv')
    rows=[row('Pace per enjoyment point',r['estimate'],[r['lower'],r['upper']],r['n'],reading='positive') for r in data]
    sup=sealed_table('CAD1-primary-20261125','support.csv')
    for r in sup:
        label={'1':'Repeat speakers','2':'Single-complete-conversation speakers'}[r['kind']]
        rows.append(row(label,n=r['n'],reading='support'))
    write('CAD1',rows)
    for key,unit,table,field,labels in [
        ('CAD2','CAD2-original-word-clock-20261126','timing.csv','measure',['Population surprise','Personal surprise','Donor-speaker control','Within-speaker shuffle']),
        ('LGH2-survey','LGH2-survey-20261125','mood.csv','comparison',['Relative laughter on incoming mood','Outgoing mood on relative laughter'])]:
        support,=sealed_table(unit,'support.csv')
        obs=support['evaluation_words' if key=='CAD2' else 'conversations']
        rows=[]
        for r in sealed_table(unit,table):
            i=int(r[field])-1
            if not 0<=i<len(labels) or int(support['n'])!=int(r['n']):
                raise ValueError('Unexpected support or registered code')
            sign=('positive' if i<2 else 'control') if key=='CAD2' else 'descriptive'
            rows.append(row(labels[i],r['estimate'],[r['lower'],r['upper']],r['n'],obs,sign))
        write(key,rows)
    path=BASE/'WEEK8/SLD5_purpose.csv'
    rows=[]
    for r in csvrows(checked(path,read(BASE/'WEEK8/SLD5_PURPOSE_AFTER_MARITAL_LOSS.json')['aggregate_sha256'])):
        group={'1':'Both losses','2':'Spouse death','3':'Finalized divorce','4':'Later loss'}[r['group']]
        time={'1':'wave one to two','2':'wave one to three','3':'wave two to three'}[r['transition']]
        form={'1':'registered','2':'earlier score adjusted'}[r['form']]
        sign='negative' if r['group']=='2' and r['transition'] in {'1','2'} and r['form']=='1' else 'descriptive'
        rows.append(row(', '.join([group,time,form]),r['estimate'],[r['lower'],r['upper']],r['n'],reading=sign))
    write('SLD5',rows)
    for key,receipt in [('LKG1','LKG1_LIKING_GAP_DISPOSITION'),('SLD6','SLD6_TRAIT_STRESSOR_RETURN')]:
        data=read(BASE/'WEEK8'/(receipt+'.json'))
        codes=[u['native_code'] for u in data['units']] if 'units' in data else [data['native_exit']]
        if data['aggregate_files']!=0 or set(codes)!={12}:raise ValueError('Withholding receipt changed')
        write(key,[])


def week8_public():
    receipt=read(BASE/'WEEK8/LGH7_MEETING_ROLE_RETURN.json')
    path=RAW8/'LGH7-registered-meeting-roles/verify_INTERNAL.json'
    checked(path,receipt['replay_sha256'])
    checked(path.with_name('execute_INTERNAL.json'),receipt['replay_sha256'])
    signed=read(checked(path.with_name('RESTRICTED_FILING.json'),receipt['internal_record_sha256']))
    work=read(path)
    if signed['evidence']!=work or signed['verdict']!='undecided':raise ValueError('AMI filing mismatch')
    d=work['AMI']
    rows=[row('Manager minus other roles',d['point'],d['interval'],d['rank_meetings'],reading='positive',unit='meetings'),
          row('Permutation reference band',None,d['permutation_interval'],d['rank_meetings'],d['permutations'],'control','meetings'),
          row('Permutations at or above observed',d['permutation_at_or_above'],(),d['permutations'],unit='permutations')]
    for label,v in (d['role_rates']|d['join_pairs']).items():
        rows.append(row('Joining rate, '+label,v['rate'],(),v['meetings'],unit='meetings'))
    for label,v,unit in [('Meetings with roles',d['meetings_with_roles'],'meetings'),('Missing an initiating role',d['meetings_missing_an_initiating_role'],'meetings'),
                         ('Untimed annotations',work['AMI_exclusions']['untimed_marks'],'marks'),('Without scenario roles',work['AMI_exclusions']['without_scenario_roles'],'meetings'),
                         ('ICSI originals checked',work['ICSI']['reviewed_originals'],'meetings')]:
        rows.append(row(label,v,(),v,reading='support',unit=unit))
    write('LGH7',rows)
    source=read(BASE/'WEEK8/ADM2_SOURCE_ADMISSIONS.json')
    b=source['bindings']
    if not source['fresh_replay'] or not all(v['status']=='admitted' for v in b.values()):raise ValueError('ADM2 incomplete')
    write('ADM2',[row('Sources admitted',len(b),(),len(b),unit='releases'),
                  row('World emBODY raster files',b['volynets-world-embody']['map_files'],(),b['volynets-world-embody']['map_files'],unit='files'),
                  row('CASE paired participants',b['case-full']['subject_file_pairs'],(),b['case-full']['subject_file_pairs'])])


if __name__=='__main__':
    public_sources()
    released_sealed()
    week8_public()
