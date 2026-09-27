"""Offline v1 export with exact native capture identity and lossless outer sidecar.

DESIGN CHECK: LESSONS 3-5. NULL: changed revision, UTF-16 anchor or context IDs
refuse matching; unknown values stay unknown. ALTERNATIVE: imported per-region
hypotheses survive the real ToMpathy parser without changing provenance fields.
"""
from copy import deepcopy
import argparse,hashlib
from pathlib import Path
from .common import digest,read,freeze
from .scoring import probabilities


def u16(s):return len(s.encode('utf-16-le'))//2


def export(artifact,readings,context=(),outer=None):
    text='\n\n'.join(r['anchor']['exact'] for r in artifact['regions'])
    if hashlib.sha256(text.encode()).hexdigest()!=artifact['revision']:raise ValueError('capture revision does not bind exact text')
    start=0
    for index,r in enumerate(artifact['regions']):
        a=r['anchor'];raw=text.encode('utf-16-le');length=u16(a['exact'])
        prefix=raw[max(0,start-80)*2:start*2].decode('utf-16-le',errors='surrogatepass');suffix=raw[(start+length)*2:(start+length+80)*2].decode('utf-16-le',errors='surrogatepass')
        if a!=dict(exact=a['exact'],index=index,start=start,prefix=prefix,suffix=suffix):raise ValueError('native UTF-16 anchor mismatch')
        start+=length+2
    known={r['id'] for r in artifact['regions']}
    if set(readings)-known:raise ValueError('reading region not captured')
    hypotheses=[];alternatives=[];nodes=[];estimates=[]
    for region in sorted(known):
        reading=readings.get(region,{})
        if reading and reading.get('visibility') not in ('I1','I2'):raise ValueError('nonempty reading needs explicit I1/I2 visibility; evaluator I3 excluded')
        if reading.get('visibility')=='I2' and not any(c['selected'] for c in context):raise ValueError('context reading lacks selected source context')
        for i,g in enumerate(reading.get('goals',[])):
            hid=f'{region}-goal-{i}';sid=f'{region}-goals'
            support=None if g.get('support') is None else dict(value=g['support'],scale=[0,1],semantics='relative',meaning='Nonexclusive compatibility, not a normalized goal posterior',candidateSet=sid)
            hypotheses.append(dict(id=hid,kind='goal',label=g['label'],description=g.get('description',''),makers=['maker-unknown'],regions=[region],status='hypothesis',support=support,evidence=[]))
        members=[h['id'] for h in hypotheses if h['kind']=='goal' and region in h['regions']]
        if members:alternatives.append(dict(id=f'{region}-goals',kind='independent',members=members,exhaustive=False))
        processes=reading.get('processes',[]);p=probabilities([x.get('probability') for x in processes],len(processes)) if processes else None
        for i,x in enumerate(processes):
            hid=f'{region}-process-{i}';sid=f'{region}-processes';nodes.append(hid)
            support=None if p is None else dict(value=p[i],scale=[0,1],semantics='probability',meaning='Exclusive declared process alternatives, including unknown support',candidateSet=sid)
            hypotheses.append(dict(id=hid,kind='process',label=x['label'],description=x.get('description',''),makers=['maker-unknown'],regions=[region],status='hypothesis',support=support,evidence=[]))
        if processes:alternatives.append(dict(id=f'{region}-processes',kind='competing',members=nodes[-len(processes):],exhaustive=True))
        hypotheses.append(dict(id=f'{region}-value-unknown',kind='value',label='Values unknown',description='No independent value evidence was supplied.',makers=['maker-unknown'],regions=[region],status='unknown',support=None,evidence=[]))
        estimates.append(dict(region=region,contribution=None,uncertainty=dict(level='unknown',meaning='No calibrated authorship share; contribution estimates remain separately typed in the sidecar.')))
    ctx=[dict(c) for c in context if c['selected']]
    for c in ctx:
        if c['id']!=digest([c['source'],c['excerpt']]):raise ValueError('context ID must bind source and exact excerpt')
    packet=dict(schemaVersion='1.0',id='stage13-'+digest([artifact['revision'],readings,ctx])[:24],revision=1,artifact=deepcopy(artifact),provider=dict(id='sounding-line-stage13-offline',method='Source-bound offline hypothesis export; no live inference'),origin='imported',scope=dict(kind='context' if ctx else 'artifact',contextIds=[c['id'] for c in ctx]),makers=[dict(id='maker-unknown',label='Maker identity unknown',identity='unknown',relationship='No asserted individual identity')],hypotheses=hypotheses,alternatives=alternatives,process=dict(nodes=nodes,edges=[]),estimates=estimates,evidence=[])
    sidecar=dict(schema='sounding-line.stage13.outer.v1',artifact_revision=artifact['revision'],readings=deepcopy(readings),context=deepcopy(ctx),outer=deepcopy(outer),claim='I1 captured text; I2 selected context if supplied; I3 evaluator information excluded from packet; sidecar is not a widened ReadingProfile.ClaimBoundary.provenance')
    return packet,sidecar


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--capture',type=Path,required=True);p.add_argument('--readings',type=Path);p.add_argument('--out',type=Path,required=True);a=p.parse_args();packet,sidecar=export(read(a.capture),read(a.readings) if a.readings else {});freeze(a.out/'packet.json',packet);freeze(a.out/'sidecar.json',sidecar)
