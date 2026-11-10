"""Bounded immutable GO3 diff/IteraTeR feature blocks and full analysis replay."""
from pathlib import Path
import hashlib,json,time
import numpy as np
from . import week5_go as core
from . import week5_go3_analysis as analysis
from .week5_go1_pipeline import requested


def features(output,inputs,config):
    import pyarrow as pa
    import pyarrow.parquet as pq
    output.mkdir(parents=True,exist_ok=True);model,training=analysis.external_intent(inputs['iterater_train'])
    paths=[Path(directory)/'edits.parquet' for directory in inputs['sites']]
    bound={'inputs':{str(p):core.sha(p) for p in paths},'analysis_sha256':core.sha(analysis.__file__),'bounded_sha256':core.sha(__file__),'iterater':training['source_sha256']}
    start=time.process_time();new=0;parts=[];index=0;total=0
    for path in paths:
        for batch in pq.ParquetFile(path).iter_batches(batch_size=512):
            part=output/'blocks'/f'{index:07d}.parquet';seal=part.with_suffix('.seal.json');index+=1
            if seal.exists():
                saved=json.loads(seal.read_text('utf8'))
                if saved['binding']!=bound or saved['sha256']!=core.sha(part):raise ValueError('revision feature checkpoint changed')
            else:
                if new>=config.get('max_new_blocks',10**12) or requested(output) or time.process_time()-start>=config.get('max_cpu_seconds',1e100):
                    return {'status':'yielded','blocks_complete':len(parts),'new_blocks':new,'new_cpu_seconds':time.process_time()-start}
                frame=batch.to_pandas();x=np.asarray([analysis.features(a,b) for a,b in zip(frame.before,frame.after)],float);prob=model.predict_proba(x)
                saved_frame=frame.drop(columns=['before','after']).copy()
                for j in range(x.shape[1]):saved_frame[f'diff_{j}']=x[:,j]
                for j,label in enumerate(model.classes_):saved_frame['intent_'+label]=prob[:,j]
                part.parent.mkdir(parents=True,exist_ok=True);saved_frame.to_parquet(part,index=False)
                core.write(seal,{'binding':bound,'sha256':core.sha(part)});new+=1
            parts.append(part);total+=batch.num_rows;core.write(output/'PROGRESS.json',{'blocks_complete':len(parts),'rows':total,'new_cpu_seconds':time.process_time()-start})
    writer=None
    try:
        for part in parts:
            table=pq.read_table(part)
            if writer is None:writer=pq.ParquetWriter(output/'features.parquet',table.schema,compression='zstd')
            writer.write_table(table)
    finally:
        if writer is not None:writer.close()
    if writer is None:raise ValueError('no revision features')
    result={**training,'rows_projected':total,'binding':bound,'features_sha256':core.sha(output/'features.parquet')}
    core.write(output/'FEATURES.json',result);return result


def execute(output:Path,inputs:dict,config:dict):
    if config.get('phase')=='features':return features(output,inputs,config)
    return analysis.execute(output,inputs,config)


def verify(output:Path,inputs:dict,config:dict):
    if config.get('phase')!='features':return analysis.verify(output,inputs,config)
    actual=features(output/'independent-replay',inputs,config)
    if actual.get('status')=='yielded':return {**actual,'verified':False}
    if actual!=json.loads((output/'FEATURES.json').read_text('utf8')):raise ValueError('GO3 complete feature replay differs')
    return {'verified':True,'all_feature_rows_replayed':True}
