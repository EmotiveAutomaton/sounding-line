"""Authorized Jester complete-record population, preserving the partial row.

DESIGN CHECK: LESSONS3-5, October18. Every complete numeric row passes unchanged.
Only the pinned final partial record with exactly28empty/123numeric cells is
quarantined verbatim. Other incomplete rows, changed sources, wrong identities
or repeated partial records refuse. No blank becomes0or99. Original population
gap, failed attempt and sealed chunks remain; this intake has no scientific
positive/null/negative verdict. Fresh verification reparses the original XLS.
"""
from __future__ import annotations

import math
from pathlib import Path
import time
import numpy as np

from . import timing_jester_ratings as original
from .timing_census import read,write,filehash
from .timing_p6 import progress,write_equal
from .timing_stats import bind,check_binding

CONFIG=dict(card='Jester2plus-complete-records',rows_per_chunk=1024)
INPUTS=original.INPUTS|{'failed_plan','failed_record','decision'}
PRIOR_SECONDS=10.295497
FORECAST_SECONDS=60
CUMULATIVE_CAP_SECONDS=900


def validate(inputs,config):
    if set(inputs)!=INPUTS or config!=CONFIG or type(config.get('rows_per_chunk')) is not int:
        raise ValueError('exact Jester complete-record inputs/config required')
    base={k:inputs[k] for k in original.INPUTS};manifest,binding=original.validate(base,original.CONFIG)
    decision=read(inputs['decision'])
    if (decision.get('authority')!='Curator reply: Use the complete records; retain the original gap'
            or decision.get('complete_records')!=50691 or decision.get('quarantined_records')!=1):
        raise ValueError('complete-record population not authorized')
    plan=read(inputs['failed_plan']);failed=read(inputs['failed_record'])
    if (Path(inputs['failed_plan']).resolve().parent!=Path(inputs['failed_record']).resolve().parent
            or plan.get('module')!='runners.drive.cards.timing_jester_ratings' or plan.get('config')!=original.CONFIG
            or plan.get('inputs')!=base or failed.get('status')!='FAILED'):
        raise ValueError('original failed intake identity differs')
    module=Path(original.__file__).resolve()
    if plan.get('pins',{}).get(str(module))!=filehash(module):raise ValueError('original failed source changed')
    old=Path(inputs['failed_plan']).resolve().parent/'output'
    if read(old/'INPUT_BINDING.json')!=binding:raise ValueError('original source binding changed')
    previous=read(old/'PROGRESS.json')
    if previous.get('phase')!='parse' or not math.isfinite(previous.get('active_seconds',math.nan)) or not 0<=previous['active_seconds']<=PRIOR_SECONDS:
        raise ValueError('original elapsed-time/source checkpoint differs')
    sealed=previous['complete_raters']//1024
    if previous['complete_raters']!=sealed*1024 or sealed<1:raise ValueError('original sealed prefix differs')
    if manifest['source_kind']=='official_dataset2plus' and (sealed!=49 or previous['complete_raters']!=50176 or previous['total_raters']!=50692):
        raise ValueError('actual original49chunk prefix differs')
    if sorted(p.name for p in (old/'chunks').glob('*.npy'))!=[f'{j:04}.npy' for j in range(sealed)]:
        raise ValueError('old sealed chunk inventory differs')
    return base,manifest,binding,old,sealed


def partial_record(values,types,row,spec,manifest):
    if row!=spec['rows']-1 or manifest['sheets'][-1]!=spec:
        raise ValueError('incomplete record is not the authorized final source row')
    if manifest['source_kind']=='official_dataset2plus' and (row!=50691 or spec['name']!='jesterfinal151cols'):
        raise ValueError('wrong actual partial record identity')
    types=list(map(int,types));values=list(values)
    if len(values)!=151 or len(types)!=151 or types.count(0)!=28 or types.count(2)!=123:
        raise ValueError('partial record type/occupancy differs from exact123numeric28empty pattern')
    if any(v!='' for v,t in zip(values,types) if t==0):raise ValueError('empty cells contain unexpected values')
    if types[0]!=2 or not math.isfinite(float(values[0])) or not 0<=float(values[0])<=150 or float(values[0])!=int(values[0]):
        raise ValueError('partial record count cell invalid')
    for value,kind in zip(values[1:],types[1:]):
        if kind==2 and (not math.isfinite(float(value)) or not (-10<=value<=10 or value==99)):
            raise ValueError('partial record numeric value invalid')
    return dict(worksheet=spec['name'],zero_based_row=row,excel_row=row+1,cell_types=types,
        original_cell_values=values,blank_columns_zero_based=[i for i,t in enumerate(types) if t==0],
        numeric_cells=123,blank_cells=28,policy='Verbatim quarantine; no imputation, recoding or replacement.',
        workbook_sha256=manifest['workbook_sha256'])


def checked_chunks(book,manifest,quarantine):
    offset=0;found=[]
    for number,spec in enumerate(manifest['sheets']):
        sheet=book.sheet_by_index(number)
        if sheet.nrows!=spec['rows'] or sheet.ncols!=151:raise ValueError('worksheet dimensions differ')
        stop_total=sheet.nrows-(number==len(manifest['sheets'])-1)
        if number==len(manifest['sheets'])-1:
            found.append(partial_record(sheet.row_values(stop_total),sheet.row_types(stop_total),stop_total,spec,manifest))
            if found[0]!=quarantine:raise ValueError('quarantine changed during source scan')
        for start in range(0,stop_total,1024):
            stop=min(start+1024,stop_total)
            # No other incomplete cell is handled here: original strict parser
            # refuses it, including additional partial or blank interior rows.
            array=original.validate_rows([sheet.row_values(i) for i in range(start,stop)],
                [sheet.row_types(i) for i in range(start,stop)])
            yield dict(sheet=spec['name'],sheet_index=number,excel_row_first=start+1,
                excel_row_last=stop,rater_offset=offset+start,rows=stop-start),array
        offset+=stop_total;book.unload_sheet(number)
    if len(found)!=1:raise ValueError('exactly one authorized partial record required')


def report(manifest,texts,count,counts,zero,parser_log,quarantine,sealed):
    value=original.statistics(manifest,texts,count,counts,zero,parser_log)
    value.update(card=CONFIG['card'],population='Separate complete-record variant: every complete original row; one exact final partial row quarantined without value recoding.',
        original_full_population_question='OPEN: the original source contains one incomplete rating record.',
        original_dimension_rows=sum(s['rows'] for s in manifest['sheets']),quarantined_records=1,
        quarantine=dict(worksheet=quarantine['worksheet'],zero_based_row=quarantine['zero_based_row'],numeric_cells=123,blank_cells=28),
        reused_original_chunks=sealed,prior_attempt_seconds_charged=PRIOR_SECONDS,
        source_description_discrepancy='Archived page advertises66336 raters; actual DIMENSIONS50692 include50691complete rows and1partial row. All three counts retained.' if manifest['source_kind']=='official_dataset2plus' else 'Constructed complete-record variant with exact final partial occupancy.')
    return value


def copy_equal(source,dest):
    source,dest=Path(source),Path(dest);dest.parent.mkdir(parents=True,exist_ok=True)
    if dest.exists():
        if filehash(dest)!=filehash(source):raise ValueError('reused original checkpoint bytes differ')
    else:
        with dest.open('xb') as f:f.write(source.read_bytes())


def run(output,inputs,config,verify=False):
    started=time.monotonic();output=Path(output)
    base,manifest,binding,old,sealed=validate(inputs,config)
    previous=read(output/'ACTIVE_TIME.json')['seconds'] if (output/'ACTIVE_TIME.json').exists() else PRIOR_SECONDS
    if not math.isfinite(previous) or previous<PRIOR_SECONDS:raise ValueError('cumulative charge missing or invalid')
    elapsed=lambda:previous+time.monotonic()-started
    recovery=dict(config=config,inputs={k:filehash(v) for k,v in sorted(inputs.items())},prior_seconds=PRIOR_SECONDS)
    if verify:
        check_binding(output,inputs,config)
        if read(output/'RECOVERY_BINDING.json')!=recovery:raise ValueError('recovery inputs changed')
    else:
        write_equal(output/'RECOVERY_BINDING.json',recovery)
        copy_equal(old/'INPUT_BINDING.json',output/'INPUT_BINDING.json')
    texts=original.validate_texts(base,manifest);book,log=original.open_source(base,manifest)
    index=[];counts=np.zeros(150,dtype=np.int64);total=sum(s['rows'] for s in manifest['sheets'])-1
    row_count=zero=0
    try:
        spec=manifest['sheets'][-1];sheet=book.sheet_by_index(len(manifest['sheets'])-1);last=spec['rows']-1
        quarantine=partial_record(sheet.row_values(last),sheet.row_types(last),last,spec,manifest)
        if verify:
            if read(output/'QUARANTINE.json')!=quarantine:raise ValueError('quarantine differs from original source')
        else:write_equal(output/'QUARANTINE.json',quarantine)
        for unit,array in checked_chunks(book,manifest,quarantine):
            number=len(index);name=f'chunks/{number:04}.npy';dest=output/name;receipt=dest.with_suffix('.json')
            if number<sealed:
                prior=old/name;prior_receipt=prior.with_suffix('.json')
                expected=dict(unit=unit,input_binding_sha256=filehash(old/'INPUT_BINDING.json'),sha256=filehash(prior))
                if read(prior_receipt)!=expected or not np.array_equal(np.load(prior,allow_pickle=False),array,equal_nan=True):
                    raise ValueError('old sealed rows differ from fresh original source')
                if verify:
                    if filehash(dest)!=filehash(prior) or filehash(receipt)!=filehash(prior_receipt):raise ValueError('old chunks not preserved byte-for-byte')
                else:copy_equal(prior,dest);copy_equal(prior_receipt,receipt)
            elif not verify and not receipt.exists():
                if dest.exists():raise ValueError('unsealed recovery chunk')
                dest.parent.mkdir(parents=True,exist_ok=True)
                with dest.open('xb') as f:np.save(f,array,allow_pickle=False)
                write(receipt,dict(unit=unit,input_binding_sha256=filehash(output/'INPUT_BINDING.json'),sha256=filehash(dest)))
            expected=dict(unit=unit,input_binding_sha256=filehash(output/'INPUT_BINDING.json'),sha256=filehash(dest))
            if read(receipt)!=expected or not np.array_equal(np.load(dest,allow_pickle=False),array,equal_nan=True):raise ValueError('recovery chunk differs from fresh source')
            seen=np.isfinite(array);counts+=seen.sum(0);zero+=int(np.sum(~seen.any(1)));row_count+=len(array)
            index.append(dict(file=name,receipt=receipt.relative_to(output).as_posix(),**unit))
            seconds=elapsed()
            if seconds>CUMULATIVE_CAP_SECONDS:raise RuntimeError('original Jester900second cumulative cap exceeded')
            if not verify:
                progress(output/'ACTIVE_TIME.json',dict(seconds=seconds));progress(output/'PROGRESS.json',dict(complete_raters=row_count,total_raters=total,seconds=seconds))
                if row_count>=math.ceil(total/10) and not (output/'FIRST_TENTH.json').exists():
                    write_equal(output/'FIRST_TENTH.json',dict(complete_raters=row_count,total_raters=total,active_seconds=seconds,
                        projected_cpu_seconds=PRIOR_SECONDS+2*(seconds-PRIOR_SECONDS)*total/row_count,forecast_cpu_seconds=FORECAST_SECONDS,
                        method='Prior attempt charged once; all source authentication/open/replay observed, whole remaining pipeline doubled for fresh verification.'))
                if (output/'YIELD_REQUEST.json').exists():return dict(status='yielded',complete_raters=row_count,total_raters=total)
    finally:book.release_resources()
    if row_count!=total:raise ValueError('not every complete record retained')
    primary=report(manifest,texts,row_count,counts,zero,log.getvalue(),quarantine,sealed)
    ix=dict(schema=1,joke_ids=list(range(1,151)),missing='NaN',dtype='float64',rows=total,chunks=index)
    if verify:
        if primary!=read(output/'PRIMARY.json') or ix!=read(output/'RATINGS_INDEX.json'):raise ValueError('complete-record report differs from fresh original source')
        return dict(verified=True,primary=primary,source_raters_reparsed=row_count,cumulative_seconds=elapsed())
    write_equal(output/'RATINGS_INDEX.json',ix);write_equal(output/'PRIMARY.json',primary)
    names=['RECOVERY_BINDING.json','INPUT_BINDING.json','QUARANTINE.json','RATINGS_INDEX.json','PRIMARY.json','FIRST_TENTH.json']+[r[k] for r in index for k in ('file','receipt')]
    if (output/'TIMING_BINDINGS.json').exists():check_binding(output,inputs,config)
    else:bind(output,inputs,config,names)
    progress(output/'ACTIVE_TIME.json',dict(seconds=elapsed()))
    return primary


def execute(output:Path,inputs:dict,config:dict)->dict:return run(output,inputs,config)


def verify(output:Path,inputs:dict,config:dict)->dict:return run(output,inputs,config,verify=True)
