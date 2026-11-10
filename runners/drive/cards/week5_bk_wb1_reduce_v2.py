"""Whole-bank WB1 cost and scientific reducers; original kernels and counts."""
from pathlib import Path
import time
from threadpoolctl import threadpool_limits
from runners.stage14.common import read,filehash,digest
from . import week5_bk_wb1_source as source
from . import week5_bk_wb1_encode_v2 as encoder
from . import week3_pieces_effects_h1 as effects
from . import week3_pieces_stats as stats


def work(manifest,rows,indexed,records):
    consistency=effects.consistency(records,20,stats.SEED)
    classes=effects.classes(records,stats.SEED)
    neutral=[dict(session=r['session'],writer=r['writer'],events=len(r['symbols']),real_covered=0,reference_covered=0) for r in rows if r['side']=='test']
    boot=[stats.coverage_interval(neutral,2000,stats.SEED) for _ in range(2)]
    digests=[dict(session=value['session'],occurrences=len(value['records']),sha256=digest(value['records'])) for _,value in sorted(indexed.items())]
    result=dict(sessions=len(rows),writers=manifest['writers'],candidates=len(manifest['candidates']),
                population_candidate_occurrences=sum(manifest['counts'].values()),sample_sessions=len(manifest['selected_sessions']),
                sample_occurrences=len(records),selected_sessions=manifest['selected_sessions'],
                session_digests=sorted(digests,key=lambda r:r['session']),kernel_digest=digest(dict(consistency=consistency,classes=classes,bootstrap=boot)),
                selection='fixed seed and session identity; first ceiling(N/10) in corpus mode',
                scientific_admission=False,upper_work_candidate_superset=True)
    return result


def run(output,inputs,config,verifying=False):
    if set(config)!={'operation'} or config['operation'] not in ('pilot_reduce','cost_reduce','effects_reduce'):
        raise ValueError('Exact full WB1 reduction required')
    operation=config['operation'];phase='effects' if operation=='effects_reduce' else 'cost'
    expected={'source_root','blocks'}|({'coverage_root'} if phase=='effects' else set())
    if set(inputs)!=expected:raise ValueError('Wrong complete encoding bank')
    root=Path(output);root.mkdir(parents=True,exist_ok=True);source_inputs={k:v for k,v in inputs.items() if k!='blocks'}
    manifest,rows,entries,indexed,records,costs,coverage=encoder.collect(source_inputs,phase,read(inputs['blocks']),operation!='pilot_reduce')
    if operation=='pilot_reduce':
        minimum=max(1,__import__('math').ceil(.05*len(entries)))
        if set(indexed)!=set(range(len(indexed))) or len(indexed)<minimum:
            raise ValueError('Original first five percent of whole selected sessions required')
        unit=max((max(c.values())/read(source.completed(path,encoder.__name__)[0]/'output/BLOCK.json')['count']
                  for path,c in zip(read(inputs['blocks']),costs)),default=0.)
        result=dict(complete_pilot_sessions=len(indexed),total_cost_sessions=len(entries),coverage=len(indexed)/len(entries),
                    cost_encoding_forecast_cpu_seconds=6*len(entries)*unit,
                    full_source_kernel_coverage_prior_charges_additional=True,scientific_admission=False,
                    scope='first five percent of unchanged first-tenth cost probe; not the complete probe')
        source.checked(root/'PILOT_FORECAST.json',result,verifying)
    elif operation=='cost_reduce':
        started=time.process_time();result=work(manifest,rows,indexed,records);kernels=time.process_time()-started
        source.checked(root/'WORK.json',result,verifying)
        # The exact old probe's work digest is retained. New bounded execution
        # overhead is charged rather than silently subtracted from the forecast.
        src,_=source.completed(inputs['source_root'],source.__name__)
        setup=max(read(src/'output'/(phase+'_COST.json'))['process_cpu_seconds'] for phase in ('EXECUTE','VERIFY'))
        encoded=max(sum(c[phase] for c in costs) for phase in ('EXECUTE','VERIFY'))
        scale=max(len(rows)/max(1,len(entries)),sum(manifest['counts'].values())/max(1,len(records)),
                  len(manifest['candidates'])/max(1,len({effects.piece_key(r['symbols']) for r in records})))
        # At most all kernel work scales tenfold from20 to200 references. This
        # deliberately also scales fixed classes/bootstrap, preserving the margin.
        forecast=dict(projected_missing_effect_work_cpu_seconds=6*(setup+scale*(encoded+10*kernels)),
                      safety_multiplier=3,both_passes=True,scale=scale,
                      includes_new_bounded_execution_overhead=True,scientific_admission=False,
                      excludes='all prior charges, this probe, native fixtures and separately measured coverage')
        name='VERIFY_FORECAST.json' if verifying else 'EXECUTE_FORECAST.json'
        if not (root/name).exists():source.checked(root/name,forecast)
    else:
        records.sort(key=lambda r:(r['session'],r['source_ordinal'],r['start'],r['stop'],effects.piece_key(r['symbols'])))
        result=dict(card='WB1b' if coverage['card']=='WB1b-coverage' else 'WB1',status='analysis_complete',full_card_complete=True,
                    scientific_admission=manifest['config']['mode']=='corpus' and coverage['route']['coverage_gate_passed'],
                    constructed=manifest['config']['mode']=='constructed',coverage_route=coverage['route'],
                    effects=effects.consistency(records,200,stats.SEED),piece_classes=effects.classes(records,stats.SEED),
                    occurrences=len(records),censored_followups=sum(not r['full_followup'] for r in records),
                    effect_definitions=dict(net_characters='all-origin Unicode document length change in the next full 60 seconds',
                        sentence_completed='any increase in punctuation-bounded sentence endings during the next 60 seconds',
                        accepted_retained_share='original accepted UTF-16 units inserted strictly after anchor through +60s that survive at session end; no acceptance means missing',
                        prompt_similarity_change='cosine change to initial prompt, pinned MiniLM; last 254 document tokens and first 254 prompt tokens'),
                    bindings={k:filehash(Path(v)/'COMPLETE.json') if k.endswith('_root') else filehash(v) for k,v in sorted(inputs.items())})
        fallback={}
        for effect,value in result['effects'].items():
            if value.get('state')=='unsupported':
                present=[r for r in records if r['side']=='test' and r[effect] is not None]
                fallback[effect]=dict(state='below floor, descriptive',observations=len(present),writers=len({r['writer'] for r in present}),
                    pooled_variance_share=effects.r_squared([r[effect] for r in present],[effects.piece_key(r['symbols']) for r in present]),
                    interval=None,scope='pooled held-out grouping only; no individual or population inference')
        source.checked(root/'WB1_EFFECT_ROWS.json.gz',records,verifying,True)
        source.checked(root/'WB1_RESULT.json',result,verifying)
        source.checked(root/'DESCRIPTIVE_FALLBACK.json',fallback,verifying)
    return dict(verified=True,complete_original_kernel_replay=True) if verifying else dict(status='complete',operation=operation)


def execute(output,inputs,config):
    with threadpool_limits(limits=2):return source.timed(run,output,inputs,config,False)
def verify(output,inputs,config):
    with threadpool_limits(limits=2):return source.timed(run,output,inputs,config,True)
