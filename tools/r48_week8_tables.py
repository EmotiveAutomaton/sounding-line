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


SEALED = {'SLD8':('trait.csv','contrast','110','Neuroticism and stressor reactivity, mean of six feelings','positive'),
          'LKG2':('comparisons.csv','measure','11','Estimated minus partner-rated standing, rungs','descriptive')}


def project(card, directory, terminal):
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
