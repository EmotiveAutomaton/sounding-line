"""Proposed Week6 documented-day/population-guard entrypoint. Not installed or runtime-qualified.

DESIGN CHECK: source admission is distinct from collection. Enclosing counted
runtime owns actual native identity, Job containment, inclusive CPU, all-eight-
slot admission and final exits. This adapter cooperates with its yield marker.
Neither a partial execute nor partial replay can return verified=true.
"""
from pathlib import Path
import time
if __package__:
    from . import es_core_v2 as core, es_source_v2 as source, es_handler_v3 as handler
else:
    import es_core_v2 as core
    import es_source_v2 as source
    import es_handler_v3 as handler


def load(inputs,config):
    core.need(set(inputs)=={'source_path','metadata_path','metadata_sha256','source_admission_path','source_admission_sha256'},
              'unexpected ES input fields')
    metadata=Path(inputs['metadata_path']);admission=Path(inputs['source_admission_path'])
    core.need(source.sha256(metadata)==inputs['metadata_sha256'],'ES metadata intake pin differs')
    core.need(source.sha256(admission)==inputs['source_admission_sha256'],'ES source admission pin differs')
    intake=handler.read_json(metadata);review=handler.read_json(admission);panel=config['panel_config']
    core.need(review['schema']=='ES_OWNER_SOURCE_ADMISSION_V1' and review['status']=='OWNER_ADMITTED','ES source not admitted')
    core.need(review['member']==panel['member'] and panel['card'] in review['cards'],'source admission scope differs')
    core.need(review['source_pin']==panel['source_pin'] and review['metadata_sha256']==inputs['metadata_sha256'],'source admission identity differs')
    core.need(review['missing_tokens']==panel['missing_tokens'] and review['source_layout_review']==panel['source_layout_review'],
              'source layout declarations differ')
    if panel['member']=='0062':
        core.need(review['daily_layout']==panel['daily_layout'],'daily-layout admission differs')
        source.validate_daily_mapping(panel,intake)
    return intake,panel


def operation(output,inputs,config,phase):
    output=Path(output);output.mkdir(parents=True,exist_ok=True);intake,panel=load(inputs,config)
    core.need(set(config)=={'panel_config','max_new_draws','max_wall_seconds'},'ES runtime configuration differs')
    wall=config['max_wall_seconds'];core.need(not isinstance(wall,bool) and isinstance(wall,(float,int)) and 0<wall<=1500,'cooperative wall bound differs')
    start=time.monotonic();root=output.parent
    if phase=='execute':preserve_inherited_yield(output)
    def guard():
        if (output/'YIELD_REQUEST.json').exists() or (output/'STOP_REQUEST.json').exists() or time.monotonic()-start>=wall:
            raise handler.Pause('owner resource yield or bounded wall quantum')
    # Preserve original declaration before any source read. Runtime's plan pin
    # check and counted native phase cover all helper files plus this adapter.
    try:
        result=handler.run_phase(panel,intake,inputs['source_path'],output/phase,phase,guard,
                                 max_new_draws=config['max_new_draws'])
    except handler.Pause:
        result={'status':'PAUSED','verified':False}
    if result['status']=='PAUSED':
        return {'status':'yielded','verified':False,'operation':phase,'engine':result,
                'checkpoint':'output/'+phase,'scientific_result_complete':False}
    if phase=='execute':return {'status':'computed','verified':False,'engine':result,'requires_fresh_replay':True}
    proof=handler.compare_fresh_phases(output/'execute',output/'verify')
    # This is numerical replay verification only. The actual runtime still must
    # inspect both distinct native identities, Job usage/empty proof and exit0
    # before freezing the external COMPLETE marker or landing a scientific row.
    answer={'status':'verified','verified':True,'numerical_replay':proof,
            'native_proof_required_from_runtime':True,'engine_status':result['status']}
    if 'population_support' in result:answer['population_inference_supported']=False
    return answer


def preserve_inherited_yield(output):
    """Do not mistake an authenticated predecessor yield for a new request.

    Move only the exact file already listed in this attempt's RESUMED_FROM
    output-manifest proof. A fresh or changed request is always honored. Keep
    the bytes and an explicit archive receipt; do not unlink historical evidence.
    """
    output=Path(output);marker=output/'YIELD_REQUEST.json';resume=output.parent/'RESUMED_FROM.json'
    if not marker.is_file() or not resume.is_file():return
    copied=handler.read_json(resume).get('copied',{});expected=copied.get('YIELD_REQUEST.json')
    if expected is None or source.sha256(marker)!=expected:return
    archive=output/'inherited_controls';archive.mkdir(exist_ok=True)
    target=archive/f'YIELD_{expected}.json'
    core.need(not target.exists(),'inherited yield already archived')
    marker.rename(target)
    handler.exclusive_json(archive/f'YIELD_{expected}_RECEIPT.json',{'source_resume_sha256':source.sha256(resume),
        'marker_sha256':expected,'archived':target.name,'fresh_requests_still_honored':True})


def execute(output,inputs,config):return operation(output,inputs,config,'execute')


def verify(output,inputs,config):return operation(output,inputs,config,'verify')
