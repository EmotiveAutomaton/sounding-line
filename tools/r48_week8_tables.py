"""Read verified Week 8 aggregate outputs and project their registered statistics."""
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from r48_extract import checked, csvrows, read, row, write, RAW8


def replay(directory, terminal):
    files = terminal['results']
    name, = [name for name in files if name.startswith('verify_')]
    first = 'execute_' + name[len('verify_'):]
    if not terminal['verified'] or files[first] != files[name]:
        raise ValueError('Missing matching independent replay')
    checked(directory / first, files[first])
    return read(checked(directory / name, files[name]))


def scalar(label, v, n, obs=None, reading='descriptive', unit='people'):
    bounds = v.get('interval')
    if bounds is None and 'lower' in v:
        bounds = [v['lower'], v['upper']]
    return row(label, v['estimate'], bounds, n, obs, reading, unit)


def game(card, obj):
    rows = []
    for key, panel in obj['panels'].items():
        name = 'All players' if key == 'all_players' else 'Endpoint sensitivity'
        labels = ['bad minus good fading rate']
        if card == 'ACC1':
            labels = ['one fading rate', 'two fading rates'] if key == 'all_players' else ['one fading rate']
        for label,v in zip(labels,panel['values'],strict=True):
            rows.append(scalar(name+', '+label,v,panel['test'],reading='positive'))
            rows.append(row(name+', '+label+', bootstrap standard error',v['se'],None,panel['test']))
        for label,rate in zip(('common','good','bad'),panel['development_rates'],strict=True):
            rows.append(row(name+', development '+label+' rate',rate,None,panel['train']))
    return rows


def couples(obj):
    rows=[]
    for feeling,v in obj['comparisons'].items():
        n=v['support']['people']
        for k,r in v['comparisons'].items():
            rows.append(scalar(feeling+', '+k.replace('_',' '),r,n,v['support']['rows']))
        for k,x in v['support'].items():
            rows.append(row(feeling+', '+k.replace('_',' '),x,None,n,reading='support'))
    for k,x in obj['structure'].items():
        rows.append(row(k.replace('_',' '),x,None,None,reading='support',unit='source census'))
    return rows


def diaries(obj):
    rows=[]
    for diary,v in obj.items():
        for window,fit in v['readings'].items():
            n=fit['support']['people']
            for k,r in {'anxiety minus sadness':fit['primary'],**fit['components']}.items():
                rows.append(scalar(diary+', '+window+', '+k,r,n,fit['support']['rows'],
                                   'positive' if k=='anxiety minus sadness' else 'descriptive'))
            for k,x in fit['support'].items():
                rows.append(row(diary+', '+window+', '+k,x,None,n,reading='support'))
        n=v['clock']['people']
        for k,x in v['thresholds'].items():
            rows.append(row(diary+', '+k.replace('_',' '),x,None,n,reading='support'))
        for k,x in v['clock'].items():
            if isinstance(x,(int,float)):
                rows.append(row(diary+', clock '+k,x,None,n,reading='support'))
        for k,x in v['clock']['gap_minutes'].items():
            rows.append(row(diary+', gap minutes '+k,x,None,n,reading='support'))
        for k,x in zip(v['clock']['bands_minutes_right_inclusive'],v['clock']['pairs_by_band'],strict=True):
            rows.append(row(diary+', gap band '+k,x,None,n,reading='support'))
    return rows


def time_use(obj):
    rows=[scalar(k,v,v['n'],v['episodes']) for k,v in obj['tables'].items()]
    for year in obj['years']:
        for k,x in year.items():
            if k!='year':
                rows.append(row(str(year['year'])+', '+k.replace('_',' '),x,None,None,reading='support',unit='source census'))
    return rows


def body_maps(obj):
    if obj['status']!='void':
        raise ValueError('Unexpected positive map binding needs review')
    return [row('Records in the fixed binding check',obj['binding_sample'],None,None,unit='binding records',reading='support'),
            row('Pixels in the registered body mask',obj['body_pixels'],None,None,unit='pixels',reading='support'),
            *[row('Anatomical mask, '+k,x,None,None,unit='pixels',reading='support') for k,x in obj['regional_pixels'].items()]]


def lag_tables():
    # The original pool and all new cells must pass the independent replay
    # checks before any original estimate or verdict is made available here.
    from week8_lag_pool import assemble
    result=assemble()
    rows=[]
    for v in result['pooled']:
        for stat in ('ratio','slope'):
            rows.append(row(f"Pooled {v['family']}, {v['gap']}, median {stat}",v[stat],None,
                            v['contributing_diaries'],unit='diaries'))
    for v in result['diaries']:
        for stat in ('ratio','slope','undecided','identified'):
            rows.append(row(f"Diary {v['member']}, {v['family']}, {v['gap']}, {stat}",
                            v[stat],None,v['cells'],unit='selected cells'))
    for v in result['cells']:
        if v['member']=='0057':
            name=f"0057 {v['cell']}, {v['gap']}"
            rows.append(row(name+', next-prompt slope',v['estimate'],v['interval'],v['people'],v['pairs']))
            rows.append(row(name+', same-prompt slope',v['same_prompt'],None,None,unit='frozen atlas cell'))
            rows.append(row(name+', ratio',v['ratio'],None,v['people'],v['pairs']))
    return rows


def meeting_tables(card, root=RAW8):
    rows=[]
    for corpus in ('ICSI','AMI'):
        suffix='prejoin' if card=='LGH6' else 'room'
        directory=root/f'{card}-{corpus}-{suffix}-DN'
        obj=replay(directory,read(directory/'COMPLETE.json'))
        if obj['source_class']!='P' or obj['corpus']!=corpus:
            raise ValueError('Different corpus or source class')
        if card=='LGH6':
            tables=obj['tables']
            rows.append(row(corpus+', source meetings',obj['meetings'],None,None,unit='meetings',reading='support'))
            short=tables['short_intervals']
            rows.append(row(corpus+', short intervals',short['intervals'],None,short['n'],reading='support'))
            for panel in ('heldout','all'):
                fit=tables[panel]
                label=corpus+', '+panel
                rows.append(row(label+', model disposition code',fit['code'],None,fit.get('n'),
                                fit.get('meetings'),reading='support'))
                for v in fit.get('models',[]):
                    model=label+', voicing model '+str(v['model'])
                    rows.append(scalar(model,v,fit['n'],reading='positive' if panel=='heldout' else 'descriptive'))
                    for field in ('shuffle95','shuffle_upper'):
                        if field in v:
                            rows.append(row(model+', '+field,v[field],None,fit['n'],reading='control'))
        else:
            for field in ('source_meetings','complete_annotation_meetings','untimed_laugh_exclusions'):
                rows.append(row(corpus+', '+field.replace('_',' '),obj[field],None,None,unit='meetings',reading='support'))
            for group,model in obj['models'].items():
                if 'code' in model:
                    rows.append(row(corpus+', '+group+', model disposition code',model['code'],None,None,unit='meetings',reading='support'))
                    continue
                for label,(point,lo,hi) in zip(obj['coefficient_order'],model['weights'],strict=True):
                    rows.append(row(corpus+', '+group+', '+label,point,[lo,hi],model['meetings'],unit='meetings'))
    return rows


def atlas_tables(directory, terminal):
    name='ATLAS_COMPLETE.json'
    audit=read(checked(directory/name,terminal['results'][name]))
    if not terminal['verified'] or len(audit['checksums'])!=audit['public_rows']+audit['internal_rows']:
        raise ValueError('Incomplete atlas replay')
    rows=[]
    agreement_counts={}
    for cell,sha in sorted(audit['checksums'].items()):
        if Path(cell).name!=cell or not cell.endswith('.json'):
            raise ValueError('Unknown atlas checkpoint')
        v=read(checked(directory/'verified_cells'/cell,sha))
        scope='0049' if v['scope']=='internal' else v['scope']
        label=f"{scope}, {v['event']}/{v['feeling']}"
        n=v['splits']
        if n!=10 or len(v['paired_intervals'])!=n:
            raise ValueError('Incomplete registered split schedule')
        qualifies=v['same_clear']>=8
        agreement_counts[scope]=agreement_counts.get(scope,0)+int(qualifies)
        for field in ('defined_both','same_clear','both_positive','both_negative'):
            rows.append(row(label+', '+field,v[field],None,n,unit='splits'))
        rows.append(row(label+', at least eight agreements',int(qualifies),None,n,unit='splits'))
        for split,pair in enumerate(v['paired_intervals'],1):
            for half,fit in zip(('A','B'),pair,strict=True):
                point,lo,hi=fit if fit is not None else (None,None,None)
                rows.append(row(f'{label}, split {split} half {half}',point,[lo,hi],None,unit='half sample'))
    for scope,total in sorted(agreement_counts.items()):
        rows.insert(0,row(scope+', cells with at least eight agreements',total,None,None,unit='cells'))
    return rows


SEALED = {'SLD8':('trait.csv','contrast','110','Neuroticism and stressor reactivity, mean of six feelings','positive'),
          'LKG2':('comparisons.csv','measure','11','Estimated minus partner-rated standing, rungs','descriptive')}


def project(card, directory, terminal):
    if card=='LAG2':
        return lag_tables()
    if card in ('LGH6','RML1'):
        return meeting_tables(card)
    if card=='ATL2':
        return atlas_tables(directory,terminal)
    if card in SEALED:
        fname,tag,code,label,direction=SEALED[card]
        if set(terminal['aggregates'])!={fname} or not terminal['verified']:
            raise ValueError('Unreviewed set of released tables')
        values=csvrows(checked(directory/'gated-return'/fname,terminal['aggregates'][fname]))
        if len(values)!=1 or values[0][tag]!=code or set(values[0])!={tag,'estimate','lower','upper','n'}:
            raise ValueError('Unreviewed released form')
        r=values[0]
        return [scalar(label,r,r['n'],reading=direction)]
    if card in ('SLD7','SLD9','TMP2-source'):
        if terminal['reason']!='Sealed exit 4' or not terminal['submitted'] or list((directory/'gated-return').glob('*')):
            raise ValueError('Withholding differs from the submitted disposition')
        return []
    obj=replay(directory,terminal)
    if card in ('ACC1','ADP1'):
        return game(card,obj)
    return {'TWO3':couples,'DRV1':diaries,'MNG1':time_use,'BMP1':body_maps}[card](obj)


if __name__=='__main__':
    card,unit=sys.argv[1:]
    directory=RAW8/unit
    terminal,=[p for p in [directory/'COMPLETE.json',directory/'FAILED.json'] if p.exists()]
    write(card,project(card,directory,read(terminal)))
