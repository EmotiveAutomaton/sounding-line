"""Balanced local Stack Exchange edit export from completed GO3 held-out folds.

DESIGN CHECK: EX2/T and original GO3 source/features/folds. Selection is fixed
from reason and source order before predictions are read. No refit, new split,
participant lookup, or private-ID URL is permitted. Missing support refuses the
5000-row bundle rather than replacing it with a convenience sample.
"""
from collections import Counter
from pathlib import Path
import hashlib
import heapq
import json
import math
import time
import xml.etree.ElementTree as ET
import numpy as np
import pyarrow.parquet as pq
from . import week5_engine_export_io as common
from . import week5_go3_bank_publication as producer
from . import week5_go3_bank_analysis as bank_analysis
from . import week5_go3_features_publication as feature_producer
from . import week5_go3_features_collected as feature
from . import week5_go3_collection as collection
from . import week5_go3_publication as publication
from . import week5_go_revisions as source
from . import week5_go3_analysis as definitions

MODULE='runners.drive.cards.week5_ex2'
PER_CATEGORY=1000
DIFF_DEFINITIONS=[
 'before Unicode-code-point length','after Unicode-code-point length','after minus before length',
 'tokens added by SequenceMatcher with autojunk=False','tokens removed by same matcher',
 'replacement opcodes','exact token Levenshtein distance','distance / max(1,before length,after length)',
 'after minus before count: [.!?,;:]','after minus before count: https?:// or ](',
 'after minus before count: backtick code spans or <code>',
 'after minus before newline count','after minus before runs of 2+ whitespace',
 'after minus before capitalized-word count']


class Paused(Exception):pass


def authenticate(inputs,stop):
    if set(inputs)!={'analysis_run'}:raise ValueError('One final primary GO3 analysis required')
    root,plan,done=common.complete(inputs['analysis_run'],producer.MODULE)
    publication.require_complete_identity(root,module=producer.MODULE,sources=producer.SOURCES)
    verified=common.read(root/'VERIFIED.json');result=common.read(root/'output/RESULT.json')
    if any(verified.get(key) is not True for key in ('complete_replay',
        'complete_models_predictions_and_reference_banks_replayed','complete_feature_bank_authenticated')):
        raise ValueError('Full independent GO3 held-out-prediction replay required')
    if plan['config'].get('phase')!='GO3' or plan['config'].get('cell')!='GO3':
        raise ValueError('Only original full GO3 primary supplies this export')
    if result.get('status')!='ok' or result.get('folds')!=5 or result.get('draws')!=2000:
        raise ValueError('Pooled descriptive fallback has no qualified held-out export')
    feature_root=Path(plan['inputs']['feature_run'])
    publication.require_complete_identity(feature_root,module=feature_producer.MODULE,sources=feature_producer.SOURCES)
    feature_root,bank,_=bank_analysis.authenticate_bank(feature_root,stop,feature_producer.MODULE)
    sources=bank['binding']['provenance']['sources']
    for info in sources:
        now=collection.authenticate(info['site'],dict(root=info['root'],complete_sha256=info['complete_sha256']),stop)
        if now!=info:raise ValueError('Complete source provenance differs from feature bank')
    binding=dict(module_sha256=common.io.sha(__file__),analysis_complete=common.io.sha(root/'COMPLETE.json'),
        feature_complete=common.io.sha(feature_root/'COMPLETE.json'),feature_report=common.io.sha(feature_root/'output/FEATURES.json'),
        per_category=PER_CATEGORY,selection='smallest SHA256 EX2|20261107|site|source_row; independent of classifier output')
    return root,feature_root,bank,sources,binding


def rank(meta):return int(hashlib.sha256(f"EX2|20261107|{meta['site']}|{meta['source_row']}".encode()).hexdigest(),16)


def accumulate(records,site,first,state):
    heaps={name:[tuple(item) for item in state['heaps'][name]] for name in source.PRIMARY}
    for value in heaps.values():heapq.heapify(value)
    editors=set(state['editors'])
    for offset,row in enumerate(records):
        if row['type'] not in (5,24) or row['reason'] not in source.PRIMARY:continue
        index=state['primary_rows'];state['primary_rows']+=1;editors.add(row['editor'])
        state['counts'][row['reason']]+=1
        meta={key:row[key] for key in collection.METADATA}
        if meta['site']!=site:raise ValueError('Feature source block site differs')
        meta.update(primary_index=index,source_row=first+offset)
        item=(-rank(meta),site,meta['source_row'],meta);heap=heaps[row['reason']]
        if len(heap)<PER_CATEGORY:heapq.heappush(heap,item)
        elif item[:3]>heap[0][:3]:heapq.heapreplace(heap,item)
    state['editors']=sorted(editors);state['heaps']={k:[list(v) for v in heap] for k,heap in heaps.items()}


def selected(state):
    if any(state['counts'][name]<PER_CATEGORY for name in source.PRIMARY):
        return None
    rows=[item[3] for name in source.PRIMARY for item in state['heaps'][name]]
    if len(rows)!=5000 or len({r['primary_index'] for r in rows})!=5000:
        raise ValueError('Fixed balanced selection is incomplete or duplicated')
    return sorted(rows,key=lambda row:row['primary_index'])


def predictions(root,rows,editors,primary_rows):
    keys=sorted(editors)
    assignment={key:i%5 for i,key in enumerate(np.random.default_rng(source.core.SEED).permutation(keys))}
    by_index={row['primary_index']:row for row in rows};seen=[];found=set()
    for fold in range(5):
        path=Path(root)/'output/classifier/folds'/f'{fold}.npz'
        saved=feature.load_arrays(path);indices=saved['indices'];predicted=saved['prediction']
        if (indices.ndim!=1 or predicted.shape!=indices.shape or not np.issubdtype(indices.dtype,np.integer)
            or not np.issubdtype(predicted.dtype,np.integer) or np.any(np.diff(indices)<=0)
            or np.any(predicted<0) or np.any(predicted>=5)):
            raise ValueError('Malformed original held-out prediction block')
        seen.extend(indices.tolist())
        for index in set(by_index)&set(indices.tolist()):
            row=by_index[index]
            if assignment[row['editor']]!=fold or index in found:raise ValueError('User-disjoint fold identity differs')
            position=int(np.searchsorted(indices,index));row['user_fold']=fold
            row['classifier_output']=source.PRIMARY[int(predicted[position])];found.add(index)
    if sorted(seen)!=list(range(primary_rows)) or found!=set(by_index):
        raise ValueError('Held-out predictions do not cover the exact complete primary population')
    return rows


def recover_public_posts(path,salt,site,wanted,found,stop):
    """Read only public post Id for the local HMAC join; no user/profile query."""
    context=ET.iterparse(path,events=('start','end'));_,root=next(context)
    for event,element in context:
        if event!='end' or element.tag!='row':continue
        value=element.attrib.get('Id')
        if not value or not value.isdigit():raise ValueError('Malformed source public post identifier')
        hashed=source.salted(salt,site+'-post',value)
        if hashed in wanted:
            if hashed in found and found[hashed]!=value:raise ValueError('Ambiguous public post identity')
            found[hashed]=value
        element.clear();root.clear()
        if wanted<=set(found):return
        if stop():raise Paused('public post-ID scan boundary; preserved matches, replay prefix on resume')
    if wanted-set(found):raise ValueError('Selected salted posts have no exact public-source ID')


def export_row(meta,record,public_post):
    if any(record[key]!=meta[key] for key in collection.METADATA):
        raise ValueError('Selected source row no longer matches held-out feature row')
    if not isinstance(record['before'],str) or not isinstance(record['after'],str) or record['before']==record['after']:
        raise ValueError('Selected body edit lacks its original changed texts')
    if not public_post.isdigit():raise ValueError('Only public numeric post IDs may form attribution URLs')
    site=meta['site'];domain='writing' if site=='writers' else site
    return dict(site=site,post_id=public_post,attribution_url=f'https://{domain}.stackexchange.com/questions/{public_post}',
        before=record['before'],after=record['after'],reason_category=meta['reason'],user_fold=meta['user_fold'],
        classifier_output=meta['classifier_output'])


def run(output,inputs,config):
    if set(config)-{'max_wall_seconds'}:raise ValueError('No export sampling/model option is configurable')
    wall=config.get('max_wall_seconds',900)
    if not isinstance(wall,(int,float)) or not math.isfinite(wall) or wall<=0:raise ValueError('Positive wall limit required')
    output=Path(output);output.mkdir(parents=True,exist_ok=True);began=time.monotonic()
    stop=lambda:time.monotonic()-began>=wall or (output/'YIELD_REQUEST.json').exists()
    state=None
    try:
        root,feature_root,bank,sources,binding=authenticate(inputs,stop)
        path=output/'STATE.json';state=common.state(path,binding,dict(next_block=0,primary_rows=0,
            heaps={key:[] for key in source.PRIMARY},counts={key:0 for key in source.PRIMARY},editors=[],
            text_cursor={},text_files={},post_ids={}))
        for name,sha in state['text_files'].items():
            if common.io.sha(output/name)!=sha:raise ValueError('Selected text checkpoint changed')
        for n in range(state['next_block'],len(bank['blocks'])):
            if stop():raise Paused('metadata selection block boundary')
            block=bank['blocks'][n]
            rows=pq.read_table(feature_root/'output'/block['path'],columns=list(collection.METADATA)).to_pylist()
            accumulate(rows,block['site'],block['first_row'],state);state['next_block']=n+1
            if (n+1)%16==0 or n+1==len(bank['blocks']):common.checkpoint(path,state)
            common.io.write_json(output/'PROGRESS.json',dict(phase='EX2_metadata',completed=n+1,total=len(bank['blocks'])))
        rows=selected(state)
        if rows is None:
            result=dict(card='EX2',record_kind='run',theory_tags=[],by_construction=False,
                complete_export=False,status='unsupported',reason='fewer than 1000 held-out primary body edits in a category',
                counts=state['counts']);common.io.write_json(output/'RESULT.json',result);return result
        rows=predictions(root,rows,state['editors'],state['primary_rows'])
        by_site={info['site']:{row['source_row']:row for row in rows if row['site']==info['site']} for info in sources}
        for info in sources:
            site=info['site'];cursor=0;needed=by_site[site]
            for batch in pq.ParquetFile(info['projection']).iter_batches(batch_size=512):
                end=cursor+batch.num_rows
                if end<=state['text_cursor'].get(site,0):cursor=end;continue
                if stop():raise Paused('selected body-text block boundary')
                for offset,record in enumerate(batch.to_pylist()):
                    index=cursor+offset
                    if index not in needed:continue
                    meta=needed[index]
                    if any(record[key]!=meta[key] for key in collection.METADATA):raise ValueError('Source/feature row identity differs')
                    name=f'selected_text/{site}-{index:09d}.json';dest=output/name
                    if dest.exists() and common.read(dest)!=record:raise ValueError('Unsealed selected text differs')
                    if not dest.exists():common.io.write_json(dest,record)
                    state['text_files'][name]=common.io.sha(dest)
                cursor=end;state['text_cursor'][site]=end;common.checkpoint(path,state)
            if cursor!=info['rows']:raise ValueError('Selected source projection lost rows')
            source_root=Path(info['root']);source_plan=common.read(source_root/'PLAN.json')
            salt_path=Path(source_plan['inputs']['salt'])
            if common.io.sha(salt_path)!=info['salt_sha256']:raise ValueError('Original source post-identity salt changed')
            salt=salt_path.read_bytes();wanted={row['post'] for row in needed.values()}
            mapping=state['post_ids'].setdefault(site,{})
            if wanted-set(mapping):
                xml=source_root/'output/xml/Posts.xml';receipt=common.read(source_root/'output/SOURCE.json')
                if common.io.sha(xml)!=receipt['member_sha256']['Posts.xml']:raise ValueError('Pinned Posts.xml changed')
                try:recover_public_posts(xml,salt,site,wanted,mapping,stop)
                finally:common.checkpoint(path,state)
        if len(state['text_files'])!=5000:raise ValueError('Balanced export lacks exact selected source texts')
        exported=[]
        for meta in rows:
            record=common.read(output/f"selected_text/{meta['site']}-{meta['source_row']:09d}.json")
            exported.append(export_row(meta,record,state['post_ids'][meta['site']][meta['post']]))
        bundle=output/'bundle';bundle.mkdir(exist_ok=True);common.io.write_json(bundle/'EDITS.json',exported)
        feature_defs=dict(diff={f'diff_{i}':name for i,name in enumerate(DIFF_DEFINITIONS)},
            tokenizer=r'\w+|[^\w\s]',feature_code_sha256=common.io.sha(definitions.__file__),
            intent_probabilities='Frozen StandardScaler + C=1 logistic regression, published IteraTeR train only; applied to same 14 diff features',
            iterater_train_sha256=definitions.ITERATER_SHA,primary_reason_order=source.PRIMARY,
            classifier='GO3 original five editor-disjoint folds; training-fold StandardScaler and C=1 logistic regression; no refit',
            model_outputs='Saved held-out predicted reason category, not in-sample prediction or calibrated probability')
        common.io.write_json(bundle/'FEATURES.json',feature_defs)
        summary=dict(rows=5000,category_counts=dict(Counter(row['reason_category'] for row in exported)),
            fold_counts=dict(Counter(str(row['user_fold']) for row in exported)))
        text=('# EX2: balanced held-out editing-reason task\n\nDerived from the five approved Stack Exchange dumps, '
            'under the supplied CC BY-SA 3.0 notice. Before/after excerpts are retained unchanged; attribution '
            'URLs use recovered public post IDs, never participant hashes or account IDs. Follow each post '
            'for contributor attribution and original context. This local derivative retains that licence '
            'and acknowledgement; it is not permission for a provider transfer or public publication.\n\n'
            'The 5000 body edits contain 1000 per frozen primary category. Selection ranks only site/source '
            'row identity with SHA-256 and seed label 20261107; classifier output cannot influence selection. '
            'Every output is the original independently replayed held-out prediction, with the original '
            'five-fold editor assignment. Comment-derived reason labels are retrospective proxies, not '
            'the writer\'s goal survey. No classifier was refitted for this export.\n\n'
            'FEATURES.json pins the original diff/IteraTeR definitions. MANIFEST.json pins complete source '
            'and prediction evidence. Scientific ledger reference: S15-W5-GO3-PRIMARY-20261108.\n\n'
            +json.dumps(summary,indent=2)+'\n')
        (bundle/'README.md').write_text(text,encoding='utf8',newline='\n')
        common.io.write_json(bundle/'MANIFEST.json',dict(card='EX2',complete_export=True,source_binding=binding,
            files={name:common.io.sha(bundle/name) for name in ('EDITS.json','FEATURES.json','README.md')}))
        result=dict(card='EX2',record_kind='run',theory_tags=[],by_construction=False,complete_export=True,**summary)
        common.io.write_json(output/'RESULT.json',result);return result
    except (Paused,bank_analysis.Paused,feature.Paused,collection.Paused) as error:
        if state is not None:common.checkpoint(output/'STATE.json',state)
        return dict(status='yielded',verified=False,phase='EX2_export',reason=str(error),
            completed=state['next_block'] if state else 0,total=len(bank['blocks']) if state else 1)


def execute(output,inputs,config):return run(output,inputs,config)
def verify(output,inputs,config):
    output=Path(output);result=run(output/'independent-replay',inputs,config)
    if result.get('status')=='yielded':return result|{'verified':False}
    if result!=common.read(output/'RESULT.json'):raise ValueError('EX2 complete export replay differs')
    if result.get('complete_export'):common.replay_bundle(output/'bundle',output/'independent-replay/bundle')
    return dict(verified=True,all_selection_folds_text_and_attribution_replayed=True)
def export_local(root,destination):return common.materialize(root,destination,card='EX2',module=MODULE,producer_sha256=common.io.sha(__file__))
