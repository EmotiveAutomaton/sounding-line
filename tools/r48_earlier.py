"""Recover historical report tables without a new data pass."""
import csv
import json
from pathlib import Path
from r48_extract import BASE, OUT, RAW7, RESTRICTED, ROOT, checked, csvrows, digest, read, row, verified, write


def prices():
    d=verified('SCR1-tail-recovery-*')
    rows=[]
    names={'dip':'Pooled top-price dip','refusal':'Observed refusal','excess_primary':'Pooled excess, open bottom',
           'excess_secondary':'Pooled excess, truncated'}
    for k,v in d['pooled'].items():
        rows.append(row(names[k],v['point'],v['interval'],d['people'],reading='negative' if k=='dip' else 'positive' if 'excess' in k else 'descriptive',unit='people in source roster'))
    path=RESTRICTED/'SCR1_ITEMS.csv'
    for r in csvrows(checked(path,read(RESTRICTED/'MANIFEST.json')['outputs'][path.name])):
        rows.append(row('Item '+r['item']+', '+r['measure'],r['estimate'],[r['lower'],r['upper']],r['answers']))
    rows.extend([row('Refusal-count variance ratio',d['refusal_variance_ratio'],n=d['complete_people']),
                 row('Odd-item refusal and even-item price',d['odd_even_corr'],n=d['odd_even_people'])])
    write('SCR1',rows)


def values():
    p=RAW7/'VAL1-observed-export-buffer-repair-20261124/internal_return'
    pins=read(p/'MANIFEST.json')
    rows=[]
    for r in csvrows(checked(p/'ITEMS.csv',pins['ITEMS.csv'])):
        for col in ['round_to_within','country_share','within_share','round_share','absolute_points_per_decade','signed_points_per_decade',
                    'countries','cells','slope_countries','timed_n']:
            timed=col in ('absolute_points_per_decade','signed_points_per_decade','slope_countries')
            name=r['form']+' '+r['item']+' '+col.replace('_',' ')
            rows.append(row(name,r[col],n=r['timed_n'] if timed else r['n']))
    write('VAL1',rows)
    # The item wording column never enters the released table.
    for name in ['COVERAGE.csv','EDITIONS.csv']:
        src=checked(p/name,pins[name])
        (OUT/('VAL1_'+name)).write_bytes(src.read_bytes())


def meetings():
    for key,pattern in [('LGH1-AMI','LGH1-AMI-original-*'),('LGH5','LGH5-AMI-provisional-*')]:
        rows=[]
        for d in sorted(RAW7.glob(pattern)):
            p=d/'verify_SUMMARY.json'
            if not p.is_file() or not (d/'COMPLETE.json').is_file():continue
            summary=read(checked(p,digest(d/'execute_SUMMARY.json')))
            if summary['aggregate_files'] or summary['tables']: raise ValueError('Newly available group table needs review')
            c=summary['counts']
            prefix='' if key=='LGH1-AMI' else ('Full roster, ' if c['meetings']==171 else str(c['meetings'])+' meetings, ')
            for col,label in [('meetings','Meetings'),('verified_channels','Channels'),('measured_intervals','Measured intervals'),
                              ('complete_six_measures','Complete acoustic intervals'),('untimed_marks','Untimed annotations')]:
                name=prefix+(label.lower() if prefix else label)
                rows.append(row(name,c[col],n=c['meetings'],unit='meetings'))
        if not rows:raise ValueError(key+' empty')
        write(key,rows)
    folder=BASE/'WEEK7'
    receipt=read(folder/'LGH3_ICSI_CONTEXT_RETURN.json')
    facts=['Recent laughter','Three speakers','Speech after laugh','Last third of meeting']
    rows=[]
    for name,published in receipt['files'].items():
        for r in csvrows(checked(folder/published,receipt['output_hashes'][name])):
            label=facts[int(r['fact'])-1]
            if 'fraction_explained' in r:
                rows.append(row(label+', explained fraction',r['fraction_explained'],n=r['n']))
                rows.append(row(label+', shuffle threshold',r['shuffle_95'],n=r['n'],reading='control'))
            else:
                for measure in ('rate','duration_seconds','bursts','voiced_fraction','relative_pitch_semitones','pitch_iqr_semitones','relative_level_db'):
                    rows.append(row(f"{label}, component {r['component']}, {measure.replace('_',' ')}",r[measure],n=r['n']))
    write('LGH3',rows)


def diaries():
    rows=[]
    for k,v in verified('ATL-extended-0049-*').items():
        for name,val,interval,kind in [('adjusted',v.get('point'),v.get('bootstrap',{}).get('interval'),'descriptive'),
                                       ('raw',v.get('raw'),None,'descriptive'),('day',v.get('day'),None,'descriptive'),
                                       ('shuffle band',None,v.get('free_shuffle',{}).get('interval'),'control')]:
            rows.append(row(k+', '+name,val,interval,v.get('people'),v.get('prompts'),kind))
    write('ATL-0049',rows)
    rows=[]
    for k,cell in verified('LAG-next-prompt-0049-*')['cells'].items():
        for clock,label in [('all','all pairs'),('short','capped gap')]:
            v=cell[clock]
            rows.append(row(k+', '+label,v['estimate'],v['interval'],v['people'],v['pairs']))
            rows.append(row(k+', '+label+' ratio',v['ratio'],n=v['people'],obs=v['pairs']))
    write('LAG-0049',rows)
    p=ROOT/'.agent-state/drive-20261115/week7-phase0/0049_EFFORT_INTERNAL.json'
    d=read(checked(p,read(BASE/'WEEK5/BT_0049_EFFORT_FILING_20261122.json')['internal_record_sha256']))['results']
    occurrence=next((ROOT/'.agent-state/drive-20261115/person-rows-20261121/bt-0049-occurrence').glob('qualification-*/AUDIT.json'))
    o=read(checked(occurrence,read(BASE/'WEEK5/BT_0049_OCCURRENCE_CHECKPOINT_20261121.json')['verified_sha256']))
    for key, groups in [('BT-0049-effort',{k:{'effort':v} for k,v in d['rows'].items()}),
                        ('BT-0049-occurrence',o['rows'])]:
        rows=[]
        for k,forms in groups.items():
            for form,v in forms.items():
                n=v.get('people',o.get('support',{}).get(k,{}).get(form,{}).get('people'))
                for measure in ('mean','raw','adjusted'):
                    x=v.get(measure)
                    if isinstance(x,dict):
                        rows.append(row(k+', '+form+' '+measure,x.get('estimate'),x.get('interval'),n))
                for field in ('spread_selected','variance_over_squared_mean'):
                    if isinstance(v.get(field),(float,int)) and not isinstance(v[field],bool):
                        rows.append(row(k+', '+form+' '+field.replace('_',' '),v[field],n=n))
        write(key,rows)


def sealed_history():
    disposition=read(BASE/'WEEK5/MIDUS_SEALED_TWO_WAVE_DISPOSITION_20261120.json')
    for wave, attempt in zip(('M2','M3'), disposition['waves'], strict=True):
        if (attempt['returned_tables'],attempt['study_exit'],attempt['wrapper_exit']) != (0,12,4):
            raise ValueError('Recheck the original two-wave release')
        write('SMF1-original-'+wave,[])
    for key,file in [('MIB1-wave2','MIB1_SEALED_ROSTER_20261123'),('MIB1-wave3','MIB1_WAVE_THREE_RETURN_20261126'),
                     ('MIB2','MIB2_SEALED_RETURN_20261123'),('DFB1','DFB1_SEALED_RETURN_20261123'),('MIB3','MIB3_SEALED_RETURN_20261123')]:
        if not (BASE/'WEEK7'/(file+'.md')).is_file():raise ValueError('Missing disposition')
        write(key,[])
    directory=BASE/'WEEK5'
    hashes=read(directory/'SMF1_THREE_SEALED_RETURNS_20261122.json')['aggregate_hashes']
    codes={'MI1':[1],'MI2':[2,3,4],'MI4':[7,8,9,10,11,12],'D5.s':[14]}
    for card,indices in codes.items():
        batch='d5' if card=='D5.s' else 'main'
        table=directory/('SMF1_BM_20261122_'+batch.upper()+'_table_status.csv')
        rows=[]
        for r in csvrows(checked(table,hashes[batch][table.name])):
            if int(r['table']) in indices:
                if r['kept']!='0':raise ValueError('New released table needs review')
                rows.append(row('Table '+r['table']+' source roster; reason code '+r['reason'],n=r['n'],reading='support'))
        if len(rows)!=len(indices):raise ValueError('Missing historical status')
        write(card,rows)
    w=BASE/'WEEK7'
    files=read(w/'SLD3_DAILY_TRAIT.json')['aggregates']
    rows=[]
    for r in csvrows(checked(w/'SLD3_trait.csv',files['trait.csv'])):
        label={'15':'Anger group','16':'Fear group','17':'All-negative mean'}.get(r['contrast'],'Registered contrast '+r['contrast'])
        rows.append(row(label,r['estimate'],[r['lower'],r['upper']],r['n']))
    for r in csvrows(checked(w/'SLD3_table_status.csv',files['table_status.csv'])):
        if r['kept']=='0':
            rows.append(row('Contrast '+r['table']+' unavailable, status '+r['analysis_state']+' (source roster)',n=r['n'],reading='support'))
    write('SLD3',rows)


def icsi():
    folder=BASE/'WEEK7'
    receipt=read(folder/'LGH1_ICSI_ACOUSTICS.json')
    prefix='LGH1_ICSI_ACOUSTICS_'
    labels={'1':'Speaking at onset','2':'Another speaker joins','3':'Target share changes'}
    rows=[]
    for filename,pin in receipt['public_files'].items():
        if not filename.endswith('.csv'):
            continue
        table=filename.removeprefix(prefix).removesuffix('.csv')
        for item in csvrows(checked(folder/filename,pin)):
            keys=[table.replace('_',' ')]
            if 'fact' in item:
                keys.append(labels[item['fact']])
            if 'component' in item:
                keys.append('component '+item['component'])
            for col,value in item.items():
                if col not in ('n','component','fact'):
                    rows.append(row(', '.join([*keys,col.replace('_',' ')]),value,n=item['n'],
                                    reading='control' if col=='shuffle_95' else 'descriptive'))
    for label,value in receipt['summary']['counts'].items():
        rows.append(row(label.replace('_',' '),value,n=receipt['summary']['counts']['meetings'],unit='meetings',reading='support'))
    write('LGH1-ICSI',rows)


if __name__=='__main__':
    prices()
    values()
    meetings()
    diaries()
    sealed_history()
    icsi()
