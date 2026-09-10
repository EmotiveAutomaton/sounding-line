"""Read-only original ArXivEdits preparation reconstruction.

DESIGN CHECK: B03/H02/I02/X01/X02/X05/X12; LESSONS 2--5, CONTROLS 6--7.
NULL: altered source spans, alternative decomposition, rights, correspondence,
exclusions, paper grouping or source counts refuse. ALTERNATIVE: the unchanged
canonical rules reconstruct the entire original released preparation and summary.
This explicit archival review does not assert execution of a new queue producer.
All retained papers were development-only; no reserve or new model work is used.
"""
import math
from .common import REPO,closure,digest,file_hash,read
from .queue import inside


def inspect(prepared,archive):
    from .arxivedits import raw_inputs,reconstruct
    prepared,archive=inside(prepared),inside(archive)
    before=closure([prepared]);identity=read(prepared/'IDENTITY.json');done=read(prepared/'COMPLETE.json')
    source=identity['sources'];archived=read(archive/'SOURCE.json')
    required={'runners/stage9/arxivedits.py','runners/stage9/common.py'}
    if (set(source['files'])!=required or source['sha256']!=digest(source['files'])
        or archived['sha256']!=digest(archived['files'])
        or any(archived['files'].get(name)!=sha or file_hash(inside(archive/name,archive))!=sha for name,sha in source['files'].items())
        or done['identity_sha256']!=digest(identity) or done['source_counts_match'] is not True or done['reserve_groups']!=0):
        raise ValueError('original annotated-span preparation or source archive identity differs')
    paths,current=raw_inputs()
    if {k:v for k,v in current.items() if k!='sources'}!={k:v for k,v in identity.items() if k!='sources'}:
        raise ValueError('original raw inputs, canonical rules or rights selection changed')
    pairs,attempts,records,lineages,summary=reconstruct(paths,identity['release_pin'])
    expected={prepared/'pairs'/(key+'.json') for key in pairs}
    if {p for p in (prepared/'pairs').rglob('*') if p.is_file()}!=expected:
        raise ValueError('original selected-pair inventory differs')
    if any(read(path)!=pairs[path.stem] for path in expected):
        raise ValueError('canonical or alternative annotations, rights or correspondence changed')
    payloads={'ATTEMPTS.json':attempts,'RECORDS.json':records,'LINEAGES.json':lineages}
    if any(read(prepared/name)!=rows for name,rows in payloads.items()):
        raise ValueError('source spans, exclusions or paper grouping do not reconstruct')
    omitted={'identity_sha256','elapsed_seconds','completed_at','output_hashes'}
    if ({k:v for k,v in done.items() if k not in omitted}!=summary
        or done['output_hashes']!={name:file_hash(prepared/name) for name in payloads}
        or any(type(done[k]) not in (int,float) or not math.isfinite(done[k]) or done[k]<0 for k in ('elapsed_seconds','completed_at'))):
        raise ValueError('original annotated-span summary or payload hashes differ')
    if raw_inputs()[1]!=current or closure([prepared])!=before:
        raise ValueError('raw-source reconstruction changed or raced original evidence')
    return {'status':'RECONSTRUCTED','prepared_identity_sha256':digest(identity),
        'prepared_complete_sha256':file_hash(prepared/'COMPLETE.json'),
        'raw_input_sha256':digest(identity['input_files']),'original_source_sha256':source['sha256'],
        'source_archive':archive.relative_to(REPO).as_posix(),'payload_sha256':digest(payloads),
        'pairs_sha256':digest(pairs),'summary_sha256':digest(summary),
        'attempted_pairs':summary['attempted_pairs'],'selected_pairs':summary['selected_pairs'],
        'paper_lineages':summary['paper_lineages'],'usable_edits':summary['usable_edits'],
        'versions':summary['versions'],'reserve_groups':0,'new_fits':0,'new_reader_calls':0,
        'new_reserve_openings':0,'scientific_admission':False,
        'scope':'original development-only annotated spans and explicit-license selection; coauthors not disentangled, no localization or maker-reported intention'}


def archive_audits(reviews):
    """Explicit original-plan inventory, separate from active case-producer reviews."""
    if not isinstance(reviews,list):raise ValueError('explicit raw preparation archive list required')
    result={}
    for review in reviews:
        if not isinstance(review,dict) or set(review)!={'kind','prepared','source_archive','identity_sha256','complete_sha256'} or review['kind']!='arxivedits':
            raise ValueError('unsupported or incomplete historical raw-preparation review')
        prepared=inside(review['prepared']);key=prepared.relative_to(REPO).as_posix()
        if key in result:raise ValueError('duplicate historical raw-preparation review')
        if digest(read(prepared/'IDENTITY.json'))!=review['identity_sha256'] or file_hash(prepared/'COMPLETE.json')!=review['complete_sha256']:
            raise ValueError('historical preparation does not match its original-plan review')
        result[key]=inspect(prepared,inside(review['source_archive']))
    return {'preparations':result,'new_queue_producer_execution_inferred':False,'scientific_admission':False}
