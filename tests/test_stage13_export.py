from copy import deepcopy
import hashlib
import pytest
from runners.stage13.export_tompathy import export,u16


def captured():
    texts=['A public fixture with an emoji \U0001f642.', 'A second paragraph.'];text='\n\n'.join(texts);regions=[];start=0;raw=text.encode('utf-16-le')
    for i,exact in enumerate(texts):
        n=u16(exact);regions.append(dict(id=f'p{i+1}',anchor=dict(exact=exact,index=i,start=start,prefix=raw[max(0,start-80)*2:start*2].decode('utf-16-le'),suffix=raw[(start+n)*2:(start+n+80)*2].decode('utf-16-le'))));start+=n+2
    return dict(id='fixture',revision=hashlib.sha256(text.encode()).hexdigest(),title='fixture',source='fixture',capturedAt='2026-09-27T22:00:00Z',regions=regions,truncated=False)


def test_export_preserves_capture_nonexclusive_goals_and_unknown_values():
    a=captured();r={'p1':dict(visibility='I1',goals=[dict(label='Goal one',support=.8),dict(label='Goal two',support=.8)],processes=[dict(label='known',probability=.6),dict(label='unknown',probability=.4)])}
    packet,side=export(a,r,outer={'ClaimBoundary':{'provenance':'retained'}})
    assert packet['artifact']==a and packet['origin']=='imported'
    assert [h['support']['value'] for h in packet['hypotheses'] if h['kind']=='goal']==[.8,.8]
    assert all(e['contribution'] is None for e in packet['estimates'])
    assert side['outer']['ClaimBoundary']['provenance']=='retained'
    bad=deepcopy(a);bad['regions'][1]['anchor']['start']-=1
    with pytest.raises(ValueError):export(bad,{})
    with pytest.raises(ValueError):export(a,{'p1':dict(visibility='I3',goals=[])})
