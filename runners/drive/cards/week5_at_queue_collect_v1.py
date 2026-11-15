"""Complete original m00 pilot catalog across old and nested native producers.

DESIGN CHECK: LESSONS 3-5. Both scientific directions require exactly165 frozen
ordinals/27007 words, original row/model/context/FP64 binding, all native guards
and fresh verification. Gaps, duplicates, partial queues, altered sources or
missing costs refuse. Complete pilot is not complete ten-reader bank or science.
This private candidate has not been executed; participant rows are decoded only
inside a future admitted counted collection, never by its builder.
"""
from pathlib import Path
import math
from . import week5_at_queue_v1 as queue
from .week5_at_collect_v5 import CORE
from .week5_at_scoring_v4 import score_binding, NUMERICAL_SPEC
from .week5_at_source import authenticate as authenticate_source
from .batch_runtime import read, freeze, filehash, check_files
from .timing_p6 import gzread
from .week5_historical_exit_v1 import stopped

MODULE='runners.drive.cards.week5_at_queue_collect_v1'


def require(value,message):
    if not value:raise ValueError(message)


def original_scope(ordinals,words):
    require(ordinals==list(range(165)) and words==27007,
            'Original pilot must contain exactly165 ordinals and27007 words')


def native_complete(root, terminal):
    root=Path(root);require(terminal.get('status')=='COMPLETE' and terminal.get('fresh_process_verified') is True,
                           'Actual complete fresh outer native run required')
    require(not any((root/name).exists() for name in ('PAUSED.json','FAILED.json','MONITOR_FAILED.json')),
            'Ambiguous outer terminal')
    require(terminal['outputs'].get('PLAN.json')==filehash(root/'PLAN.json'),'Outer plan unsealed')
    for name,digest in terminal['outputs'].items():
        path=queue.below(root,name);require(filehash(path)==digest,'Changed completed outer output')
    require(stopped(read(root/'OWNER.json')['native'],terminal['at']),'Outer native exit unknown')
    measured=0.0
    for phase in ('EXECUTE','VERIFY'):
        usage=read(root/(phase+'_JOB_USAGE.json'))
        require(usage['includes_all_descendants_and_exited_processes'] is True and usage['exit_code']==0,
                'Incomplete outer native phase accounting')
        measured+=usage['cpu_seconds']
    require(terminal['cpu_seconds']+1e-9>=measured and read(root/'VERIFIED.json').get('verified') is True,
            'Outer verification or inclusive accounting absent')


def phase_proof(root, batch, nested):
    """Original guard evidence and actual fresh-forward count, without model load."""
    native=[];guards={};cpu=0.0;peaks=[]
    verification=read(root/'VERIFIED.json')
    require(verification.get('verified') is True and
            verification['fresh_forward_count']==max(1,math.ceil(.02*batch['words'])) and
            math.isfinite(verification['max_error']) and verification['max_error']<=1e-4,
            'Original seeded fresh-forward verification missing')
    for phase in ('EXECUTE','VERIFY'):
        identity=read(root/(phase+'_NATIVE.json'))['native'];native.append(identity)
        usage=read(root/(phase+'_JOB_USAGE.json'))
        require(usage['includes_all_descendants_and_exited_processes'] is True and usage['exit_code']==0 and
                math.isfinite(usage['cpu_seconds']) and usage['cpu_seconds']>=0,'Native usage missing')
        cpu+=usage['cpu_seconds']
        environment=read(root/(phase+'_ENVIRONMENT.json'))
        require(environment['cuda_visible']=='' and environment['threads']==2 and
                all(p['num_threads']<=2 for p in environment['pools']),'Actual numerical environment changed')
        if nested:
            exit_record=read(root/(phase+'_EXIT.json'))
            closed=read(root/(phase+'_CLOSED.json'))
            require(exit_record['exit_code']==0 and exit_record['native']==identity and
                    read(root/(phase+'_OWNED.json'))['native']==identity and closed['native']==identity and
                    closed['known_not_same_live'] is True and closed['native_inspection_completed'] is True and
                    closed['forced'] is False,'Exact nested native closure missing')
        valid=[]
        for p in (root/'output').glob('GUARD_'+phase+'_*.json'):
            g=read(p)
            if g.get('status')!='returned' or g.get('phase')!=phase.lower():continue
            own=g['identity'];initial=g['initial']
            if own['pid']!=identity['pid']:continue
            require(g['limits']==queue.LIMITS and
                    abs(own['creation_time']-((identity['created_ticks']-116444736000000000)/1e7))<=.000002 and
                    Path(own['executable']).resolve()==Path(identity['executable']).resolve(),
                    'Guard identity or original limits changed')
            require(initial['commit_headroom_bytes']>=26*2**30 and initial['ram_available_bytes']>=20*2**30,
                    'Model started below original memory floor')
            valid.append(p)
        require(len(valid)==1,'Exact current native guard receipt missing or ambiguous')
        guards[phase]=dict(path=str(valid[0]),sha256=filehash(valid[0]))
        peaks.append(read(valid[0])['peak_working_set_bytes']/2**30)
    require(native[0]!=native[1],'Fresh native verification did not use a different process')
    return dict(native_phase_cpu_seconds=cpu,native_pairs=native,guards=guards,
                measured_peak_working_set_GiB=max(peaks))


def score_rows(root, batch, model, model_hash):
    """Exact original row order/binding and sealed score blocks; no association."""
    plan=read(root/'PLAN.json');summary=read(root/'output/SUMMARY.json')
    require(plan['module']==queue.SCORER and plan['config']['context']=='final' and
            plan['config']['context_length']==1024,'Unknown producer or changed context')
    pins={str(Path(p).resolve()).casefold():s for p,s in plan['pins'].items()}
    for name,digest in CORE.items():
        path=Path(__file__).parent/name
        require(filehash(path)==digest and pins.get(str(path.resolve()).casefold())==digest,
                'Original numerical/guard code pin missing')
    source=Path(plan['inputs']['rows']).resolve();manifest=Path(plan['inputs']['model_manifest']).resolve()
    require(source==Path(batch['input_rows']).resolve() and filehash(source)==batch['input_sha256'] and
            pins.get(str(source).casefold())==batch['input_sha256'],'Wrong original source chunk')
    require(filehash(manifest)==model_hash and pins.get(str(manifest).casefold())==model_hash and
            read(manifest)==model,'Model revision/manifest mismatch')
    require(summary['model']==model['model'] and summary['model_revision']==model['revision'] and
            summary['context']=='final' and summary['context_length']==1024 and
            summary['numerical_spec']==NUMERICAL_SPEC and summary['words']==batch['words'],
            'Changed score summary scope')
    rows=gzread(source)
    require(len(rows)==batch['words'],'Original source row count differs')
    binding=score_binding(rows,model,'final',1024)
    require(read(root/'output/BINDING.json')=={'sha256':binding},'Original row/model/context binding differs')
    index=read(root/'output/INDEX.json')
    require([v['row_key'] for v in index]==[r['row_key'] for r in rows],'Original word-row order differs')
    blocks={};result=[]
    for ordinal,item in enumerate(index):
        path=queue.below(root/'output',item['file'])
        if path not in blocks:
            require(filehash(path)==item['sha256'] and
                    read(path.with_suffix('.receipt.json'))=={'sha256':item['sha256']},'Score block hash differs')
            blocks[path]=read(path)
        block=blocks[path]
        require(block['binding']==binding and block['offset']==8*(ordinal//8) and
                len(block['values'])==min(8,len(rows)-block['offset']) and
                item['slot']==ordinal%8 and item['file']==f'block-{ordinal//8:05d}.json',
                'Original eight-row block/index position differs')
        value=block['values'][item['slot']]
        require(value['row_key']==item['row_key'],'Word identity differs inside sealed block')
        score=value['score'];nll=score['native_token_nll']
        require(len(nll)==len(score['native_token_ids']) and len(nll)>0 and
                all(math.isfinite(x) and x>=0 for x in nll+[score['entropy_nats']]) and
                score['surprisal_nats']==sum(nll),'Retained original score arithmetic differs')
        result.append(dict(row_key=item['row_key'],score_file=str(path),slot=item['slot'],sha256=item['sha256']))
    return result


def queue_cost_chain(root):
    entries=[];seen=set()
    while True:
        root=Path(root).resolve();require(root not in seen,'Cyclic queue continuation');seen.add(root)
        plan=read(root/'PLAN.json')
        terms=[n for n in ('COMPLETE.json','PAUSED.json','FAILED.json') if (root/n).is_file()]
        require(len(terms)==1 and terms[0]!='FAILED.json','Unknown queue continuation cost')
        terminal=read(root/terms[0]);require(stopped(read(root/'OWNER.json')['native'],terminal['at']),'Queue ancestor exit unknown')
        require(math.isfinite(terminal['cpu_seconds']) and terminal['cpu_seconds']>=0,'Missing queue terminal cost')
        entries.append(dict(root=str(root),terminal=terms[0],sha256=filehash(root/terms[0]),
             cpu_seconds=terminal['cpu_seconds'],supervisor_envelope_cpu_seconds=30))
        resume=plan.get('resume')
        if not resume:break
        prior=Path(resume['root']).resolve()
        require(filehash(prior/'PLAN.json')==resume['plan_sha256'] and filehash(prior/'PAUSED.json')==resume['paused_sha256'],
                'Queue continuation identity changed')
        previous=read(prior/'PLAN.json')
        require(all(previous[k]==plan[k] for k in ('module','inputs','config','family','campaign')),
                'Queue continuation changed scientific identity')
        root=prior
    return entries


def validate(request):
    require(set(request)=={'queue_root','queue_complete_sha256','pilot_source_root','pilot_source_complete_sha256'},
            'Exact complete original pilot collection interface required')
    root=Path(request['queue_root']).resolve()
    require(filehash(root/'COMPLETE.json')==request['queue_complete_sha256'],'Wrong completed queue')
    outer=read(root/'PLAN.json');done=read(root/'COMPLETE.json');native_complete(root,done)
    require(outer['module']==queue.MODULE and outer['family']=='AT' and outer.get('owner_reviewed') is True,
            'Unreviewed queue producer')
    spec=read(outer['inputs']['queue_manifest'])
    require(outer['pins'].get(outer['inputs']['queue_manifest'])==filehash(outer['inputs']['queue_manifest']),
            'Unpinned queue manifest')
    queue.authenticate(spec,include_prefix=True)
    require(spec['start_ordinal']==133 and spec['end_ordinal_exclusive']==165,'Undeclared pilot queue range')
    source=Path(request['pilot_source_root']).resolve()
    require(filehash(source/'COMPLETE.json')==request['pilot_source_complete_sha256'],'Original pilot source identity changed')
    authenticate_source(source)
    expected={b['file']:b for b in read(source/'output/BATCHES.json') if b['context']=='final'}
    require(set(expected)=={b['source_file'] for b in spec['batches']},'Pilot source roster incomplete')
    queue_summary=read(root/'output/QUEUE_SUMMARY.json');nested=queue_summary['completed_chunks']
    require([r['ordinal'] for r in nested]==list(range(133,165)),'Missing, reordered or duplicated new ordinals')
    records=[dict(ordinal=x['ordinal'],root=Path(x['root']),nested=False,complete_sha256=x['complete_sha256'])
             for x in spec['prefix']['chunks']]
    for item in nested:
        chunk=queue.below(root/'output',item['root'])
        require(filehash(chunk/'CHUNK_COMPLETE.json')==item['sha256'],'Nested completion identity differs')
        seal=read(chunk/'CHUNK_COMPLETE.json');queue.check_seal(chunk,seal)
        require(seal['ordinal']==item['ordinal'],'Nested ordinal differs')
        records.append(dict(ordinal=item['ordinal'],root=chunk,nested=True,complete_sha256=item['sha256']))
    require([r['ordinal'] for r in records]==list(range(165)),'Original pilot ordinals not exactly complete')
    model=read(spec['model_manifest']);catalog=[];word_keys=set();word_index=[];native_keys=set()
    for record,batch in zip(records,spec['batches']):
        require(expected[batch['source_file']]['sha256']==batch['input_sha256'],'Pilot source entry changed')
        chunk=record['root']
        if not record['nested']:
            require(filehash(chunk/'COMPLETE.json')==record['complete_sha256'],'Historical completion changed')
        proof=phase_proof(chunk,batch,record['nested'])
        for identity in proof['native_pairs']:
            key=(identity['pid'],identity['created_ticks'])
            require(key not in native_keys,'One native phase cannot authenticate two original chunks')
            native_keys.add(key)
        rows=score_rows(chunk,batch,model,spec['model_manifest_sha256'])
        for row in rows:
            require(row['row_key'] not in word_keys,'Duplicated word across original chunks')
            word_keys.add(row['row_key']);word_index.append(dict(ordinal=record['ordinal'],**row))
        catalog.append(dict(ordinal=record['ordinal'],producer_kind='nested_queue' if record['nested'] else 'top_level',
            root=str(chunk),complete_sha256=record['complete_sha256'],words=len(rows),source_sha256=batch['input_sha256'],**proof))
    original_scope([r['ordinal'] for r in records],len(word_index))
    costs={x['root']:x for x in spec['prefix']['attempts']}
    for entry in queue_cost_chain(root):
        require(entry['root'] not in costs,'Outer queue charged twice');costs[entry['root']]=entry
    envelope=dict(schema='AT_M00_COMPLETE_PILOT_QUEUE_ENVELOPE_V1',model=spec['model'],
        model_revision=spec['model_revision'],model_manifest_sha256=spec['model_manifest_sha256'],
        numerical_spec=NUMERICAL_SPEC,batches=165,words=27007,complete_original_m00_pilot=True,
        whole_ten_reader_bank_ready=False,scientific_admission=False,association_computed=False,
        native_cpu_seconds=sum(x['cpu_seconds'] for x in costs.values()),
        supervisor_envelope_cpu_seconds=sum(x['supervisor_envelope_cpu_seconds'] for x in costs.values()),
        measured_peak_working_set_GiB=max(
            max(x['measured_peak_working_set_GiB'] for x in catalog),
            read(spec['prefix']['all_prior_AT_failure_and_pause_cost_inventory']['path'])['measured_envelope']['measured_peak_working_set_GiB']),
        charged_attempts=list(costs.values()),failed_AT_attempt_inventory=spec['prefix']['all_prior_AT_failure_and_pause_cost_inventory'],
        cost_scope='Complete original prefix ancestry and each outer queue attempt once; all separate AT failures remain separately charged')
    return catalog,word_index,envelope


def execute(output,inputs,config):
    require(set(inputs)=={'catalog_request'} and not config,'Exact frozen catalog request required')
    catalog,index,envelope=validate(read(inputs['catalog_request']))
    output=Path(output);freeze(output/'PILOT_CATALOG.json',catalog);freeze(output/'SCORES_INDEX.json',index)
    freeze(output/'MEASURED_ENVELOPE.json',envelope)
    return dict(status='complete',complete_original_m00_pilot=True,whole_bank_ready=False,scientific_admission=False)


def verify(output,inputs,config):
    require(set(inputs)=={'catalog_request'} and not config,'Exact frozen catalog request required')
    catalog,index,envelope=validate(read(inputs['catalog_request']))
    output=Path(output)
    require(read(output/'PILOT_CATALOG.json')==catalog and read(output/'SCORES_INDEX.json')==index and
            read(output/'MEASURED_ENVELOPE.json')==envelope,'Complete original pilot catalog replay differs')
    return dict(verified=True,complete_original_m00_pilot=True,whole_bank_ready=False,scientific_admission=False)
