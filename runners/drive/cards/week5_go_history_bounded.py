"""Document-sealed GO history preparation; exact uninterrupted numerical consumer.

DESIGN CHECK: source-only five-percent pilot, complete per-document provenance,
fresh independent projection, and no scientific result from a partial history.
"""
from collections import Counter
from pathlib import Path
import hashlib,json,time
from . import week5_go as core
from . import week5_go_history as history


def prepare(output,inputs,config):
    output.mkdir(parents=True,exist_ok=True)
    rows=json.loads(Path(inputs['documents']).read_text('utf8'))['documents']
    binding={'documents':core.sha(inputs['documents']),'salt_sha256':core.sha(inputs['salt']),
             'heads':core.PINS,'history_module':core.sha(history.__file__),'bounded_module':core.sha(__file__)}
    counts=Counter();anchors=[];first=[];new=0;start=time.process_time()
    for index,row in enumerate(rows):
        part=output/'document-parts'/f'{index:06d}';seal=part/'SEAL.json'
        if seal.exists():
            saved=json.loads(seal.read_text('utf8'))
            if saved['binding']!=binding:raise ValueError('history checkpoint binding differs')
            for name,value in saved['files'].items():
                if core.sha(part/name)!=value:raise ValueError('history document checkpoint changed')
            receipt=json.loads((part/'SOURCE.json').read_text('utf8'))
        else:
            if new>=config.get('max_new_documents',len(rows)) or time.process_time()-start>=config.get('max_cpu_seconds',1e100) or (output/'YIELD_REQUEST.json').exists() or (output.parent/'YIELD_REQUEST.json').exists():
                report={'status':'yielded','source_only':True,'documents_complete':index,'documents_total':len(rows),'new_documents':new,
                        'new_cpu_seconds':time.process_time()-start,'projection_forecast_cpu_seconds':(time.process_time()-start)/max(1,new)*len(rows)}
                core.write(output/'PROGRESS.json',report);return report
            part.mkdir(parents=True,exist_ok=True);core.write(part/'INPUT.json',{'documents':[row]})
            receipt=history.source(part,{**inputs,'documents':str(part/'INPUT.json')})
            core.write(seal,{'binding':binding,'files':{name:core.sha(part/name) for name in ['SOURCE.json','anchors.json','first-drafts.json']}})
            new+=1
        counts.update(receipt['counts']);anchors.extend(json.loads((part/'anchors.json').read_text('utf8'))['anchors'])
        first.extend(json.loads((part/'first-drafts.json').read_text('utf8'))['documents'])
        core.write(output/'PROGRESS.json',{'documents_complete':index+1,'documents_total':len(rows),'new_cpu_seconds':time.process_time()-start})
    core.write(output/'anchors.json',{'anchors':anchors});core.write(output/'first-drafts.json',{'documents':first})
    result={'source_only':True,'counts':dict(counts),'bilateral_anchors':len(anchors),'three_each_anchors':sum(a['three_each'] for a in anchors),
            'first_draft_documents':len(first),'heads':core.PINS,'anchors_sha256':core.sha(output/'anchors.json'),
            'first_drafts_sha256':core.sha(output/'first-drafts.json'),'binding':binding}
    core.write(output/'SOURCE.json',result);return result


def execute(output:Path,inputs:dict,config:dict):
    if config.get('phase')=='prepare':return prepare(output,inputs,config)
    return history.execute(output,inputs,config)


def verify(output:Path,inputs:dict,config:dict):
    if config.get('phase')!='prepare':return history.verify(output,inputs,config)
    replay=prepare(output/'independent-replay',inputs,config)
    if replay.get('status')=='yielded':return {**replay,'verified':False}
    expected=json.loads((output/'SOURCE.json').read_text('utf8'))
    if expected!=replay:raise ValueError('complete independent history source differs')
    for name in ['anchors.json','first-drafts.json']:
        if core.sha(output/name)!=core.sha(output/'independent-replay'/name):raise ValueError('history projection row differs')
    return {'verified':True,'whole_projection_replay':True}
