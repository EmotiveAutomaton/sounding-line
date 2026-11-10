"""WC4 complete R1 retention source; original eight properties and POS model."""
from pathlib import Path
from types import FunctionType,SimpleNamespace
import copy
from . import week3_stability_inputs as old
from . import week5_bk_outcome_source as shared
from .timing_census import read,filehash
from .timing_p6 import gzread
from .timing_pmap_source import completed
from .week3_pieces_coverage import authenticated


def configuration(config):
    if config.get('card')!='WC4-inputs':raise ValueError('WC4 source card required')
    value=shared.configuration(dict(config,card='FR1-inputs'));value['card']='WC4-inputs';return value


def prepare(args,spans,wb1,annotation):
    fn=FunctionType(old.prepare_session.__code__,dict(old.__dict__,spans_source=SimpleNamespace(spans=lambda *unused:copy.deepcopy(spans))))
    value=fn(**args,wb1=wb1,annotation=annotation)
    value['r1_audit']=dict(physical_insertions=len(spans),canonical=sum(s['canonical'] for s in spans),comparator_unsupported=sum(not s['comparator_supported'] for s in spans))
    return value


def run(output,inputs,config,verifying=False):
    configuration(config);alias=dict(config,card='FR1-inputs')
    if (Path(output)/'YIELD_REQUEST.json').exists():return dict(status='yielded',reason='source resource request before loading')
    if config['mode']=='constructed':
        loaded=shared.load(inputs,alias);tagger=None;index=None
    else:
        required={'r1_root','pmap_completion','event_completion','event_index','event_result','model_manifest','tagger_completion'}
        if set(inputs)!=required:raise ValueError('Complete R1, WB1, PMAP and actual POS proof required')
        loaded=shared.load({k:inputs[k] for k in ('r1_root','pmap_completion')},alias)
        smoke_root=Path(inputs['tagger_completion']).parent
        completed(inputs['tagger_completion'],smoke_root/'output/TAGGER_SMOKE.json');smoke=read(smoke_root/'output/TAGGER_SMOKE.json')
        if smoke.get('card')!='WC4-tagger-smoke' or smoke.get('model_manifest_sha256')!=filehash(inputs['model_manifest']):raise ValueError('Actual pinned POS proof differs')
        for key in ('event_index','event_result'):authenticated(inputs['event_completion'],inputs[key])
        result=read(inputs['event_result'])
        if result['sessions']!=1399:raise ValueError('Full WB1 event census required')
        for path,sha in result['source_bindings'].items():
            if filehash(path)!=sha:raise ValueError('Original WB1 source changed')
        entries=read(inputs['event_index']);index={r['session']:r for r in entries}
        if len(entries)!=1399 or set(index)!=set(loaded[1].p2):raise ValueError('WB1/R1/PMAP populations differ')
        tagger=old.LocalTagger(inputs['model_manifest'])
    def extract(args,spans,card):
        if config['mode']=='constructed':
            args=dict(args);wb1=args.pop('wb1');annotation=args.pop('annotation')
        else:
            sid=args['meta']['session'];item=index[sid];base=Path(inputs['event_index']).parent;path=(base/item['file']).resolve();path.relative_to(base.resolve())
            if filehash(path)!=item['sha256']:raise ValueError('WB1 event session changed')
            wb1=gzread(path)
            if wb1['raw_sha256']!=args['timeline']['source_sha256'] or wb1['p2_sha256']!=loaded[1].p2[sid]['sha256']:raise ValueError('WB1 original raw/P2 identity differs')
            annotation=tagger(args['timeline']['final_document'])
        value=prepare(args,spans,wb1,annotation)
        if config['mode']!='constructed' and filehash(path)!=item['sha256']:raise ValueError('WB1 session changed during source extraction')
        return value
    fn=FunctionType(shared.run.__code__,dict(shared.__dict__,configuration=configuration,load=lambda unused_i,unused_c:loaded,prepare=extract,
        fr=SimpleNamespace(assemble=old.assemble)))
    return fn(output,inputs,config,verifying)


def execute(output,inputs,config):return run(output,inputs,config)
def verify(output,inputs,config):return run(output,inputs,config,True)
