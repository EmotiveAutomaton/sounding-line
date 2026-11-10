"""Bounded source-replayed WB1 cost/full effect encoding, original CPU encoder."""
from pathlib import Path
from collections import defaultdict
import json
import os
import time
from threadpoolctl import threadpool_limits
from runners.stage14.common import read, filehash, digest, atomic
from . import week5_bk_wb1_source as source
from . import week5_bk_wb1_vectors as checkpoints
from . import week3_pieces_effects_h1 as effects
from . import week4_pieces_windows_h1 as exact
from .timing_p6 import gzread, gzip_equal, write_equal


def selected(inputs,phase):
    expected={'source_root'}|({'coverage_root'} if phase=='effects' else set())
    if set(inputs)!=expected:raise ValueError('Exact encoded source/coverage bundle required')
    root,manifest,rows=source.load(inputs['source_root'])
    if phase=='cost':
        entries=[r for r in manifest['sessions'] if r['cost_selected']];occurrences=None;coverage=None
    else:
        from . import week5_bk_wb1_coverage as producer
        covroot,plan=source.completed(inputs['coverage_root'],producer.__name__)
        if plan['config']['operation']!='coverage_reduce' or plan['inputs']['source_root']!=inputs['source_root']:
            raise ValueError('Coverage used a different source')
        coverage=read(covroot/'output/WB1_COVERAGE_RESULT.json')
        if coverage['status']!='component_complete' or coverage['full_card_complete'] is not False:
            raise ValueError('Full original coverage required')
        occurrences=defaultdict(list)
        for item in coverage['whole']['occurrences']:occurrences[item['session']].append(item)
        entries=[r for r in manifest['sessions'] if r['session'] in occurrences]
        if {r['session'] for r in entries}!=set(occurrences):raise ValueError('Coverage source session missing')
    binding=digest(dict(source=manifest['binding'],phase=phase,coverage=coverage,
                        encoder_sha256=filehash(effects.__file__),windows_sha256=filehash(exact.__file__)))
    return root,manifest,rows,entries,occurrences,coverage,binding


def encode_session(descriptor,occurrences,encoder,mode,full):
    events=[json.loads(line) for line in Path(descriptor['raw_path']).read_text(encoding='utf8').splitlines()]
    timeline=read(descriptor['timeline_path'])
    windows=exact.effect_windows(events,timeline,occurrences)
    if windows:
        if encoder is None:raise ValueError('A nonempty exact session needs the frozen encoder')
        prompt,prompt_scope=encoder.vectors([timeline['initial_document']])
        texts=sorted({w[key] for w in windows if w['full_followup'] for key in ('before','after')})
        similarities={}
        if texts:
            vectors,scopes=encoder.vectors(texts,context=True)
            similarities={text:(float(vector@prompt[0]),scope) for text,vector,scope in zip(texts,vectors,scopes)}
        for window in windows:
            before,after=window.pop('before'),window.pop('after')
            window['prompt_similarity_change']=similarities[after][0]-similarities[before][0] if window['full_followup'] else None
            if full:
                window['embedding_scope']=dict(prompt=prompt_scope[0],before=similarities[before][1],after=similarities[after][1]) if window['full_followup'] else None
    return windows


def run(output,inputs,config,verifying=False):
    if set(config)!={'phase','start','count'} or config['phase'] not in ('cost','effects'):
        raise ValueError('Exact WB1 encoding block required')
    phase=config['phase'];start=config['start'];count=config['count']
    if type(start) is not int or type(count) is not int or start<0 or not 1<=count<=8:
        raise ValueError('Bounded whole-session block required')
    root=Path(output);root.mkdir(parents=True,exist_ok=True);began=time.monotonic()
    src,manifest,rows,entries,occurrences,coverage,binding=selected(inputs,phase)
    if start+count>len(entries):raise ValueError('Encoding range exceeds complete selected source')
    source.checked(root/'BINDING.json',dict(binding=binding,config=config),verifying)
    encoder=None;values=[]
    for index in range(start,start+count):
        if (root/'YIELD_REQUEST.json').exists() or time.monotonic()-began>=1200:
            return dict(status='yielded',reason='sealed original whole-session encoding boundary')
        entry=entries[index];descriptor=source.session(src,manifest,entry)
        original=descriptor['candidate_occurrences'] if phase=='cost' else occurrences[entry['session']]
        path=root/f'session-{index:04d}.json.gz';seal=root/f'session-{index:04d}.seal.json'
        identity=dict(binding=binding,index=index,source_sha256=entry['sha256'],occurrences_sha256=digest(original))
        if path.exists() and seal.exists() and not verifying:
            if read(seal)!=dict(identity,sha256=filehash(path)):raise ValueError('Changed encoded-session checkpoint')
            record=gzread(path)
        else:
            if original and encoder is None:
                source.model(manifest['inputs'],manifest['config']['mode'])
                encoder=checkpoints.Encoder(root,manifest['inputs']['content_model'],manifest['config']['mode'],binding,verifying,began)
            if encoder is not None:encoder.begin_session(index,identity)
            try:records=encode_session(descriptor,original,encoder,manifest['config']['mode'],phase=='effects')
            except checkpoints.YieldRequested as exc:return dict(status='yielded',reason=str(exc))
            record=dict(**identity,session=entry['session'],records=records)
            source.checked(path,record,verifying,True)
            source.checked(seal,dict(identity,sha256=filehash(path)),verifying)
        if any(record[k]!=v for k,v in identity.items()) or record['session']!=entry['session'] or len(record['records'])!=len(original):
            raise ValueError('Encoding identity or occurrence count changed')
        values.append(dict(index=index,file=path.name,sha256=filehash(path),session=entry['session'],occurrences=len(record['records'])))
        atomic(root/'PROGRESS.json',dict(phase='verify' if verifying else 'encode',complete_sessions=len(values),block_sessions=count,total_sessions=len(entries)))
    block=dict(binding=binding,phase=phase,start=start,count=count,total_sessions=len(entries),entries=values)
    source.checked(root/'BLOCK.json',block,verifying)
    return dict(verified=True,full_source_and_embedding_replay=True) if verifying else dict(status='complete',sessions=count)


def invocation(output,inputs,config,verifying):
    root=Path(output);phase='VERIFY' if verifying else 'EXECUTE';began=time.process_time();stamp=time.time_ns();value=None
    try:
        with threadpool_limits(limits=2):value=run(output,inputs,config,verifying)
        return value
    finally:
        ledger=root/'cost_ledger';ledger.mkdir(parents=True,exist_ok=True)
        write_equal(ledger/f'{phase}-{os.getpid()}-{stamp}.json',dict(process_cpu_seconds=time.process_time()-began,outcome='exception' if value is None else value.get('status','verified')))
        done=value is not None and (value.get('verified') is True or value.get('status')=='complete')
        path=root/(phase+'_COST.json')
        if done and not path.exists():write_equal(path,dict(process_cpu_seconds=sum(read(p)['process_cpu_seconds'] for p in ledger.glob(phase+'-*.json')),startup_additional=True))


def execute(output,inputs,config):return invocation(output,inputs,config,False)
def verify(output,inputs,config):return invocation(output,inputs,config,True)


def collect(inputs,phase,paths,require_complete=True):
    src,manifest,rows,entries,occurrences,coverage,binding=selected(inputs,phase)
    indexed={};costs=[]
    for path in paths:
        root,plan=source.completed(path,__name__);cfg=plan['config']
        if plan['inputs']!=inputs or cfg['phase']!=phase:raise ValueError('Encoding used a different source or phase')
        block=read(root/'output/BLOCK.json')
        if block['binding']!=binding or block['phase']!=phase or block['start']!=cfg['start'] or block['count']!=cfg['count'] or block['total_sessions']!=len(entries):
            raise ValueError('Encoding block changed its binding or scope')
        if [e['index'] for e in block['entries']]!=list(range(cfg['start'],cfg['start']+cfg['count'])):
            raise ValueError('Missing complete encoding block range')
        for entry in block['entries']:
            index=entry['index']
            if index in indexed:raise ValueError('Duplicate session in encoding bank')
            if not 0<=index<len(entries) or entry['session']!=entries[index]['session']:
                raise ValueError('Wrong selected session index')
            p=root/'output'/entry['file']
            if filehash(p)!=entry['sha256']:raise ValueError('Encoded session bytes changed')
            record=gzread(p)
            if record['binding']!=binding or record['index']!=index or record['source_sha256']!=entries[index]['sha256']:
                raise ValueError('Wrong encoded session binding')
            indexed[index]=record
        costs.append({p:read(root/'output'/(p+'_COST.json'))['process_cpu_seconds'] for p in ('EXECUTE','VERIFY')})
    if require_complete and set(indexed)!=set(range(len(entries))):raise ValueError('Incomplete full encoding bank')
    records=[r for index in sorted(indexed) for r in indexed[index]['records']]
    return manifest,rows,entries,indexed,records,costs,coverage
