"""Sample adapter repair: genre comes from the authenticated window ledger.

DESIGN CHECK: the real producer lacks genre in P6 records. Require exact
session/writer equality to the completed window ledger before stratifying.
Known missing/mismatched joins refuse; either effect direction leaves this
pre-outcome selection unchanged. Original adapter and failed preflight remain.
"""
from pathlib import Path
from types import FunctionType
from . import week4_s1_nuisance as original
from . import week4_s1_nuisance_v2 as corrected
from . import week4_s1_nuisance_sample as first
from .timing_census import read
from .timing_p6 import write_equal

configuration=original.configuration
writer_frame=first.writer_frame
select_writers=first.select_writers

def checked_frame(records,windows):
    source={r['session']:r['writer'] for r in records}
    target={r['session']:r['writer'] for r in windows}
    if len(source)!=len(records) or len(target)!=len(windows) or source!=target:
        raise ValueError('Exact genre ledger source join differs')
    return writer_frame(windows)

def sampled_view(values,manifest):
    records,windows,intervals,by_writer,medians=values
    if checked_frame(records,windows)!=manifest['frame']:
        raise ValueError('Authenticated genre frame differs')
    selected=set(first.validate_sample(windows,manifest))
    return (records,[w for w in windows if w['writer'] in selected],intervals,by_writer,medians)

def known_checks():
    records=[dict(session=str(i),writer=str(i//2)) for i in range(8)]
    windows=[dict(r,genre='a' if i<4 else 'b') for i,r in enumerate(records)]
    frame=checked_frame(records,windows);selected=select_writers(frame,2)
    manifest=dict(seed=first.SEED,frame=frame,sample_size=2,selected_writers=selected)
    values=(records,windows,{}, {}, {})
    view=sampled_view(values,manifest)
    assert len(view[1])==4 and all(view[i] is values[i] for i in (0,2,3,4))
    try:checked_frame(records,windows[:-1])
    except ValueError:pass
    else:raise AssertionError('Missing source join accepted')
    return dict(first.known_checks(),real_producer_genre_join=True,whole_writer_source_preserved=True,missing_source_refused=True)

def run(output,inputs,config,verification=False):
    scope={}
    def load(source):
        if set(source)!={'histories_completion','typing_completion','pmap_completion','sample_manifest'}:
            raise ValueError('Exact sample inputs required')
        values=original.load({k:v for k,v in source.items() if k!='sample_manifest'})
        manifest=read(source['sample_manifest']);view=sampled_view(values,manifest)
        scope.update(seed=first.SEED,population_writers=len(manifest['frame']),sample_writers=manifest['sample_size'],
            selected_writers=manifest['selected_writers'],source_sessions=len(values[1]),sampled_sessions=len(view[1]),
            scope='Whole-writer sample; original full-population source and history matches preserved.')
        return view
    def checks():return dict(corrected.known_check(),**known_checks())
    runner=FunctionType(original.run.__code__,dict(original.run.__globals__,load=load,
        features=corrected.features,known_check=checks),original.run.__name__,original.run.__defaults__,original.run.__closure__)
    result=runner(output,inputs,config,verification)
    value=scope or dict(scope='Constructed sample interface; no corpus accessed.',checks=known_checks())
    path=Path(output)/'SAMPLE_SCOPE.json'
    if verification:
        if read(path)!=value:raise ValueError('Sample scope replay differs')
    else:write_equal(path,value)
    return result

def execute(output,inputs,config):return run(output,inputs,config)
def verify(output,inputs,config):return run(output,inputs,config,True)
