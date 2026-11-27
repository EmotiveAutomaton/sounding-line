"""LGH6 on the frozen assigned microphones, with the exact LGH1 held-out split."""
from collections import defaultdict
import csv
from pathlib import Path
from tempfile import TemporaryDirectory
import xml.etree.ElementTree as ET
from zipfile import ZipFile

import numpy as np

from . import week7_ami_channels as ami, week7_icsi_recordings as icsi
from . import week7_meeting_acoustics as acoustic
from . import week8_join_operator as op
from . import week8_gear as gear
from .week7_ami_pcm import read_headset
from runners.drive.sealed import week7_lgh1 as prev
from runners.stage14.common import read, filehash, freeze, atomic, now

ROOT=gear.REPO
HIST=ROOT/'.agent-state/drive-20261115/week7-phase1'
PREVIOUS=gear.ROOT.parent/'drive-week7-20261122'
PUBLIC=ROOT/'results/phase_2_4_stage_15/WEEK7'
COHORTS={
    'LGH6-ICSI-prejoin':('ICSI','ICSI_CHANNEL_REPAIR.json','LGH1-ICSI-channel-repair-20261122',75,90000),
    'LGH6-AMI-prejoin':('AMI','AMI_PROVISIONAL_171.json','LGH5-AMI-provisional-171-dualmono-repair1-20261124',171,110000)
}
for original in tuple(COHORTS):
    COHORTS[original+'-DN']=COHORTS[original]


def inputs(unit):
    corpus,receipt,prior,total,cap=COHORTS[unit]
    info=read(HIST/receipt)
    archive=next(Path(p) for p in info['pins'] if p.endswith('ICSI_original_transcripts.zip' if corpus=='ICSI' else '/AMI.zip') or
                 (corpus=='AMI' and p.endswith('\\AMI.zip')))
    base=PREVIOUS/prior
    old=base/('execute' if corpus=='ICSI' else 'baseline')
    return corpus,info,archive,old,total,cap


def design(unit):
    corpus,info,archive,old,total,cap=inputs(unit)
    receipt=HIST/COHORTS[unit][1]
    candidate=old.parent/'COMPLETE.json'
    pins={Path(p):v for p,v in info['pins'].items()}
    # Only source and original operator bytes, and the known aggregate outputs, enter the review.
    present=[Path(p) for p in (icsi.__file__,ami.__file__,op.__file__,prev.__file__,acoustic.__file__)]
    extras=[receipt,candidate,old.parent/(old.name+'_SUMMARY.json'),ROOT/'docs/design/stage-15/week8/LGH6.md',
            ROOT/'runners/drive/cards/week7_ami_pcm.py',ROOT/'docs/design/stage-15/week7/LGH1_RECORDING_BINDING.md',
            *present,*sorted((old/'group_tables').glob('*.csv'))]
    if corpus=='ICSI':
        extras.extend([HIST/'ICSI_FINAL_VALIDATION.json', PUBLIC/'LGH3_ICSI_CONTEXT_RETURN_component_context.csv'])
    else:
        extras.extend([HIST/'AMI_PROVISIONAL_24.json',HIST/'AMI_PROVISIONAL_48.json',HIST/'AMI_VERIFIED_INVENTORY.json'])
    return dict(inputs=list(dict.fromkeys([*pins,*extras])),expected=pins,peak=2.5,cap=cap,
                operations=['execute','verify'],source='icsi-close-talk' if corpus=='ICSI' else 'ami-assigned-headsets-171')


def fixture():
    proof=op.fixture()
    rng=np.random.default_rng(20261127)
    features=rng.normal(size=(240,6))
    meta=[dict(speaker=i%24,overlap_other=0) for i in range(240)]
    with TemporaryDirectory() as scratch:
        folder=Path(scratch)
        tables=folder/'group_tables'
        tables.mkdir()
        prior=tables/'mixture.csv'
        _,test=np.array_split(np.random.default_rng(2026112205).permutation(240),2)
        n=len({meta[i]['speaker'] for i in test})
        prior.write_text('components,n\n1,'+str(n)+'\n',encoding='ascii')
        expected=dict(counts={'complete_six_measures':240},aggregate_files={'group_tables/mixture.csv':filehash(prior)})
        actual,known,permit=prior_membership(features,meta,folder,expected)
        assert np.array_equal(actual,test) and permit and len(known[0])==24
        assert set(actual)==set(test)
    proof['checks']+=['original seeded roster','historical count check','class P aggregate reporting']
    return proof


def meetings(corpus,archive,inventory):
    with ZipFile(archive) as bundle:
        if corpus=='ICSI':
            roster=icsi.editions(bundle)
        else:
            assignments=ami.channel_map(archive)
            roster=ami.complete_meetings(assignments,inventory)
            xml=ET.fromstring(bundle.read('corpusResources/meetings.xml'))
            people={(m.get('observation'),s.get('nxt_agent')):s.get('global_name')
                    for m in xml.findall('meeting') for s in m.findall('speaker')}
        for meeting in sorted(roster):
            if corpus=='ICSI':
                channels,marks,speech,ref,_,_=icsi.transcript(bundle.read(roster[meeting]))
                files={p:f'{meeting}/{name}.sph' for p,name in channels.items()}
            else:
                files,marks,speech,ref,_,_=acoustic.ami_transcript(bundle,meeting,assignments,roster[meeting],people)
            yield meeting,files,marks,speech,ref


def prior_membership(features,metadata,old,expected):
    finite=np.flatnonzero(np.isfinite(features).all(axis=1))
    if len(finite)!=expected['counts']['complete_six_measures']:
        raise ValueError('Earlier six-measure roster differs')
    rng=np.random.default_rng(2026112205)
    train,test=np.array_split(rng.permutation(finite),2)
    speakers=np.array([r['speaker'] for r in metadata])
    universe=frozenset(speakers)
    hist=[universe,frozenset(speakers[finite])]
    tables=old/'group_tables'
    prior=expected['aggregate_files']
    for name,h in prior.items():
        if filehash(old/name)!=h:raise ValueError('Prior aggregate changed')
    # The previous full-roster disclosure failure applies to its held-out panel.
    sources=sorted(tables.glob('*.csv'))
    if not sources:
        if 'held-out roster disclosure' not in expected['disposition']:
            raise ValueError('Earlier table disposition differs')
        return test,hist,False
    hist.append(frozenset(speakers[test]))
    x=features
    z=(x-x[train].mean(axis=0))/x[train].std(axis=0)
    groups=prev.mixture(z[train]).predict(z[test])+1
    facts=np.array([[r.get(k,np.nan) for k in prev.FACTS] for r in metadata],float)[test]
    overlap=np.array([r['overlap_other'] for r in metadata])[test]
    for path in sources:
        with path.open(newline='') as stream:
            for row in csv.DictReader(stream):
                mask=np.ones(len(test),bool)
                if 'component' in row:mask &= groups==int(row['component'])
                if 'fact' in row:mask &= np.isfinite(facts[:,int(row['fact'])-1])
                if path.stem=='target_minutes':mask &= np.isfinite(facts[:,2])
                if path.stem=='overlap':mask &= overlap==int(row['other_speaking'])
                group=frozenset(speakers[test[mask]])
                if len(group)!=int(row['n']):raise ValueError('Prior released membership differs')
                if group not in hist:hist.append(group)
    return test,hist,True


def calculate(unit,d,mode):
    corpus,info,archive,old,total,_=inputs(unit)
    source=Path(read(ROOT/'.agent-state/data_collection_root.json')['root'])
    inventory=info['inventory' if corpus=='ICSI' else 'files']
    expected=read(old.parent/(old.name+'_SUMMARY.json'))
    original_features=[];metadata=[];candidate=[];old_index=[];short=set()
    excluded=0
    for index,(meeting,files,marks,speech,ref) in enumerate(meetings(corpus,archive,inventory),1):
        windows=op.bounds(marks)
        full={};parts={};lengths=[]
        for person,key in files.items():
            pin=inventory[key]
            if corpus=='ICSI':
                channel=source/'open/icsi-close-talk/raw'/key
                wave,rate=icsi.decode_sphere(channel,pin,HIST/'icsi-decoder/sph2pipe.exe')
            else:
                channel=source/'open'/pin['edition']/'raw'/key
                wave,rate=read_headset(channel,pin)
            lengths.append(len(wave)/rate)
            indices=[i for i,event in enumerate(marks) if event['speaker']==person]
            if not indices:continue
            energy=0.;n=0
            for span in icsi.union(ref.get(person,[])):
                s=icsi.samples(wave,rate,span);energy+=s@s;n+=len(s)
            baseline=np.sqrt(energy/n) if n else 0.
            prior=icsi.channel_features(wave,rate,ref.get(person,[]),[marks[i] for i in indices])
            for i,feat in zip(indices,prior,strict=True):
                if feat is not None:full[i]=[feat[k] for k in prev.FEATURES]
                a,b,j,k=windows[i]
                sample=icsi.samples(wave,rate,(a,b))
                val=op.prefix(sample,rate,baseline)
                if val is None:
                    if op.active_samples(sample,rate).sum()<round(.2*rate):
                        excluded+=1;short.add(person)
                    continue
                parts[i]=(val[0],val[1],k,j)
        facts=prev.heldout_facts(meeting,speech,marks,0.,min(lengths),{})
        if len(facts)!=len(marks):raise ValueError('Earlier annotation facts changed')
        offset=len(original_features)
        new_ids={i:offset+p for p,i in enumerate(sorted(full))}
        for i in sorted(full):
            if (facts[i]['speaker']!=marks[i]['speaker'] or facts[i]['joined']!=windows[i][2]):
                raise ValueError('Join or original order differs')
            original_features.append(full[i]);metadata.append(facts[i])
        for i in sorted(parts):
            candidate.append((marks[i]['speaker'],meeting,*parts[i]))
            old_index.append(new_ids.get(i,-1))
        atomic(d/(mode+'_COVERAGE.json'),dict(at=now(),meetings=index,expected=total))
    if index!=total:raise ValueError('Meeting roster changed')
    X=np.asarray(original_features,float)
    test,known,previously_releasable=prior_membership(X,metadata,old,expected)
    if corpus=='AMI':
        # Earlier AMI milestones withheld their component tables. Include their
        # actual source and complete-acoustics memberships in the joint check.
        official=read(HIST/'AMI_VERIFIED_INVENTORY.json')
        names=ami.complete_meetings(ami.channel_map(archive),official['files'])
        for subset in (set(names),*(set(read(HIST/f'AMI_PROVISIONAL_{n}.json')['meetings']) for n in (24,48))):
            if not subset:raise ValueError('Previous AMI cohort missing')
            for complete in (False,True):
                members=frozenset(r['speaker'] for i,r in enumerate(metadata) if r['conversation'] in subset
                                  and (not complete or np.isfinite(X[i]).all()))
                if members and members not in known:known.append(members)
    held=np.isin(old_index,test)
    people=np.array([r[0] for r in candidate]); conv=np.array([r[1] for r in candidate])
    codes=np.column_stack((np.unique(people,return_inverse=True)[1],np.unique(conv,return_inverse=True)[1],
                           np.asarray([r[2:] for r in candidate],float)))
    output={}
    for label,mask in [('heldout',held),('all',np.ones(len(held),bool))]:
        # A speaker appearing only once supplies no within-person contrast.
        persons,counts=np.unique(people[mask],return_counts=True)
        mask=mask & np.isin(people,persons[counts>=2])
        group=frozenset(people[mask])
        if len(group)<2 or len(set(conv[mask]))<2:
            output[label]=dict(code=12,n=len(group),meetings=len(set(conv[mask])))
            continue
        known.append(group)
        coefs=op.regress(codes[mask])
        output[label]=dict(code=0,n=len(group),meetings=len(set(conv[mask])),models=coefs) if coefs else dict(code=12)
    output['short_intervals']=dict(n=len(short),intervals=excluded)
    return dict(corpus=corpus,meetings=total,tables=output,source_class='P',
                note='Active pre-join sound. Each primary reproduces the original held-out assignment.')


def run(unit,d,mode):
    freeze(d/(mode+'_SUMMARY.json'),calculate(unit,d,mode))


def check(unit,d):
    a=d/'execute_SUMMARY.json';b=d/'verify_SUMMARY.json'
    if a.read_bytes()!=b.read_bytes():raise ValueError('Fresh source replay differs')
    return {a.name:filehash(a),b.name:filehash(b)}
