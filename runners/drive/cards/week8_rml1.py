"""RML1 source binding for the two separately authorized meeting corpora."""
from collections import defaultdict
from pathlib import Path
import re
import xml.etree.ElementTree as ET
from zipfile import ZipFile

import numpy as np
from . import week7_ami_channels as ami, week7_icsi_recordings as icsi, week8_lgh6 as sources
from . import week8_room_operator as room
from .week7_ami_pcm import read_headset
from runners.stage14.common import atomic, filehash, freeze, now, read


PRIOR_UNIT = {'RML1-ICSI-room':'LGH6-ICSI-prejoin','RML1-AMI-room':'LGH6-AMI-prejoin'}
PRIOR_UNIT.update({'RML1-ICSI-room-DN':'LGH6-ICSI-prejoin-DN',
                   'RML1-AMI-room-DN':'LGH6-AMI-prejoin-DN'})


def design(unit):
    prior = PRIOR_UNIT[unit]
    corpus,info,archive,_,_,cap = sources.inputs(prior)
    root = sources.ROOT
    pins = {Path(k):v for k,v in info['pins'].items()}
    dependencies = [root/'docs/design/stage-15/week8/RML1.md', sources.HIST/sources.COHORTS[prior][1],
                    Path(sources.__file__),Path(room.__file__),Path(icsi.__file__),Path(ami.__file__),
                    root/'runners/drive/cards/week7_ami_pcm.py']
    if corpus == 'ICSI':
        dependencies.append(sources.HIST/'icsi-decoder/sph2pipe.exe')
    return dict(inputs=list(dict.fromkeys([*pins,*dependencies])),expected=pins,peak=2.0,cap=cap,
                operations=['execute','verify'],source='icsi-close-talk' if corpus=='ICSI' else 'ami-assigned-headsets-171')


def icsi_annotations(data):
    channels,marks,_,_,_,_ = icsi.transcript(data)
    speech = defaultdict(list)
    masks = []
    unknown = 0
    for seg in ET.fromstring(data).iter('Segment'):
        span = icsi.timed(seg.get('StartTime'),seg.get('EndTime'))
        if any('laugh' in v.get('Description','').lower() for v in seg.iter('VocalSound')):
            if span:
                masks.append(span)
            else:
                unknown += 1
        if span and seg.get('Participant') in channels:
            count = sum(len(re.findall(r"[^\W_]+(?:['’][^\W_]+)*",t)) for t in seg.itertext())
            if count:
                speech[seg.get('Participant')].append((*span,count))
    return channels, speech, masks, [m['start'] for m in marks], unknown


def annotations(corpus, archive, inventory):
    with ZipFile(archive) as bundle:
        if corpus=='ICSI':
            for meeting, path in sorted(icsi.editions(bundle).items()):
                channels,speech,masks,onsets,unknown=icsi_annotations(bundle.read(path))
                yield {person:f'{meeting}/{name}.sph' for person,name in channels.items()},speech,masks,onsets,unknown
            return
        assignments=ami.channel_map(archive)
        for meeting, paths in sorted(ami.complete_meetings(assignments,inventory).items()):
            speech,files,masks,onsets,unknown={}, {}, [], [], 0
            for path in paths:
                _,agent = assignments[path]
                stream=ami.intervals(bundle,meeting,agent)
                if stream is None or agent in files:
                    raise ValueError('Unbound or duplicated AMI channel')
                laughs,words,untimed=stream
                unknown+=untimed
                files[agent]=path
                speech[agent]=[(a,b,1) for a,b in words]
                masks.extend(laughs)
                onsets.extend(a for a,b in laughs)
            yield files,speech,masks,onsets,unknown


def fixture():
    proof=room.fixture()
    data=b'<M><Participant Name="p" Channel="chan1"/><Participant Name="q" Channel="chan2"/><Segment Participant="p" StartTime="4" EndTime="6">one two</Segment><Segment Participant="q" StartTime="8" EndTime="9"><VocalSound Description="laugh"/></Segment><Segment Participant="p" StartTime="12" EndTime="14">word<VocalSound Description="laugh"/></Segment><Segment Participant="q"><VocalSound Description="laugh"/></Segment></M>'
    channels,speech,masks,onsets,unknown=icsi_annotations(data)
    assert len(channels)==2 and speech['p'][0]==(4,6,2)
    assert masks==[(8,9),(12,14)] and onsets==[8] and unknown==1
    proof['checks'].extend(['mixed ICSI mask','lexical count from timed utterance','untimed annotation excludes meeting'])
    return proof


def run(unit,d,mode):
    prior=PRIOR_UNIT[unit]
    corpus,info,archive,_,expected,_=sources.inputs(prior)
    root=Path(read(sources.ROOT/'.agent-state/data_collection_root.json')['root'])
    inventory=info['inventory' if corpus=='ICSI' else 'files']
    models=[[],[],[]]
    included=0
    untimed_meetings=0
    for index,(files,speech,masks,onsets,unknown) in enumerate(annotations(corpus,archive,inventory),1):
        if unknown:
            untimed_meetings+=1
        else:
            blocks=[]
            masks=room.merged(masks)
            for person,key in files.items():
                pin=inventory[key]
                if corpus=='ICSI':
                    wave,rate=icsi.decode_sphere(root/'open/icsi-close-talk/raw'/key,pin,sources.HIST/'icsi-decoder/sph2pipe.exe')
                else:
                    wave,rate=read_headset(root/'open'/pin['edition']/'raw'/key,pin)
                blocks.append(room.measure_channel(wave,rate,speech.get(person,[]),masks))
                del wave
            levels=room.combine(blocks)
            bins=levels.shape[1]
            starts=np.asarray(onsets)
            counts=np.bincount((starts[(starts>=0)&(starts<30*bins)]//30).astype(int),minlength=bins)
            for groups,measure in zip(models,levels,strict=True):
                groups.append(room.design(measure,counts))
            included+=1
        atomic(d/(mode+'_COVERAGE.json'),dict(at=now(),meetings=index,expected=expected))
    if index!=expected:
        raise ValueError('Original meeting count changed')
    data={}
    for name, groups in zip(('room','sound','pace'),models,strict=True):
        # DM permits only model weights. Keep all bin, speaker and channel values local to this process.
        fitted=room.fit(groups) if sum(len(y)>1 and y.sum()>0 for _,y in groups)>=20 else None
        data[name]=fitted if fitted else {'code':12}
    freeze(d/(mode+'_SUMMARY.json'),dict(corpus=corpus,source_meetings=expected,complete_annotation_meetings=included,
           untimed_laugh_exclusions=untimed_meetings,models=data,source_class='P',
           coefficient_order=['absolute change','signed change','mean level','mean level squared','high then fall','prior laughs']))


def check(unit,d):
    a,b=d/'execute_SUMMARY.json',d/'verify_SUMMARY.json'
    if a.read_bytes()!=b.read_bytes():
        raise ValueError('Room models differ on independent source replay')
    return {p.name:filehash(p) for p in (a,b)}
