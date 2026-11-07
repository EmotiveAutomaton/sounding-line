"""Pinned-month 1% sampling and exact annotation arithmetic, with no effect fit.

DESIGN CHECK: LESSONS 2-5. Keep sample selection before availability filters.
Missing/rounded clocks and mate evaluations never become invented numeric data.
"""
from pathlib import Path
import io,re,gzip,json,time
import numpy as np
import pyarrow as pa
from runners.stage14.common import read,freeze,filehash
from .backlog_intake import fetch

HEADER=re.compile(r'^\[(\w+) "(.*)"\]$')
EVAL=re.compile(r'\[%eval (-?\d+(?:\.\d+)?)\]')
CLOCK=re.compile(r'\[%clk (\d+):(\d+):(\d+(?:\.\d+)?)\]')
SAN=re.compile(r'^(?:O-O(?:-O)?|[KQRBN]?[a-h1-8x]*[a-h][1-8](?:=[QRBN])?)[+#]?$')


def games(stream):
    record=[];size=0
    for line in stream:
        if line.startswith('[Event ') and record:yield record;record=[];size=0
        size+=len(line)
        if size>1024**2:raise ValueError('Game text exceeds bounded parser')
        record.append(line.rstrip('\r\n'))
    if record:yield record


def decode(lines):
    headers={};moves=[]
    for line in lines:
        match=HEADER.match(line)
        if match:
            if match[1] in ('WhiteElo','BlackElo','TimeControl'):headers[match[1]]=match[2]
        elif line.strip():moves.append(line)
    return dict(headers=headers,moves=' '.join(moves))


def features(record):
    headers=record['headers'];tc=re.fullmatch(r'(\d+)\+(\d+)',headers.get('TimeControl',''))
    if not tc:return [],{'invalid_time_control':1}
    try:ratings=[float(headers['WhiteElo']),float(headers['BlackElo'])]
    except (KeyError,ValueError):return [],{'missing_rating':1}
    if not all(np.isfinite(x) and x>0 for x in ratings):return [],{'missing_rating':1}
    initial,increment=map(int,tc.groups());moves=[]
    for match in re.finditer(r'\{([^}]*)\}|([^\s{}]+)',record['moves']):
        if match[1] is not None:
            if not moves:continue
            ev=EVAL.search(match[1]);clk=CLOCK.search(match[1])
            if ev:moves[-1]['evaluation']=float(ev[1])
            if clk:moves[-1]['clock']=float(clk[1])*3600+float(clk[2])*60+float(clk[3])
        else:
            token=re.sub(r'^\d+\.(?:\.\.)?','',match[2]).rstrip('!?')
            if not token or token in ('1-0','0-1','1/2-1/2','*') or token.startswith('$'):continue
            if not SAN.fullmatch(token):return [],{'unsupported_move_token':1}
            moves.append(dict(evaluation=None,clock=None))
    last=[float(initial),float(initial)];rows=[];counts={'parsed_moves':len(moves),'missing_eval_or_clock':0,'nonpositive_seconds':0}
    previous=None
    for index,move in enumerate(moves):
        side=index%2;before=last[side];after=move['clock'];ev=move['evaluation'];last[side]=after
        if previous is None or ev is None or before is None or after is None:counts['missing_eval_or_clock']+=1
        else:
            seconds=before-after+increment
            if seconds<=0:counts['nonpositive_seconds']+=1
            else:
                quality=-max(0.,(previous-ev)*(1 if side==0 else -1)*100)
                ply=index+1
                rows.append([quality,ratings[side],np.log(seconds),int(before<=10),int(20<ply<=60),int(ply>60),abs(previous)*100])
        previous=ev
    return rows,counts


def prepare(source,selected_path,feature_path,rate=.01,max_games=None):
    rng=np.random.default_rng(20261106);counts={};total=selected=annotated=usable=0;arrays=[];ids=[]
    with pa.input_stream(str(source),compression='zstd') as binary,io.TextIOWrapper(binary,encoding='utf8') as text,Path(selected_path).open('wb') as raw:
        with gzip.GzipFile(filename='',fileobj=raw,mode='wb',mtime=0) as saved:
            for ordinal,lines in enumerate(games(text)):
                total+=1
                if rng.random()<rate:
                    selected+=1;record=decode(lines);saved.write((json.dumps(record,sort_keys=True)+'\n').encode())
                    if '[%eval ' in record['moves'] and '[%clk ' in record['moves']:
                        annotated+=1;values,dispositions=features(record)
                        for k,v in dispositions.items():counts[k]=counts.get(k,0)+v
                        if values:
                            usable+=1;arrays.extend(values);ids.extend([ordinal]*len(values))
                if max_games and total>=max_games:break
    values=np.asarray(arrays,dtype=float).reshape((-1,7));group=np.asarray(ids,dtype=np.int64)
    np.savez_compressed(feature_path,values=values,groups=group)
    return dict(source_games=total,selected_games=selected,annotated_games=annotated,usable_games=usable,
                moves=len(values),sample_probability=rate,seed=20261106,dispositions=counts,
                source_case_pass=usable>=1000 and len(values)>=10000,prefix_only=max_games is not None)


def execute(output,inputs,config):
    output=Path(output);output.mkdir(parents=True,exist_ok=True)
    if config.get('download'):
        source=output/'month.pgn.zst';receipt=fetch(source,config['url'],3600000000)
        if receipt['bytes']!=3481200992:raise ValueError('Named-month source size changed')
        freeze(output/'DOWNLOAD.json',receipt)
    else:
        source=Path(inputs['source']['path']);assert filehash(source)==inputs['source']['sha256']
    result=prepare(source,output/'PRIVATE_SELECTED.jsonl.gz',output/'PRIVATE_FEATURES.npz',config.get('sample_probability',.01),config.get('max_games'))
    result['source_sha256']=filehash(source);freeze(output/'SOURCE.json',result)
    return dict(status='complete',scientific_effect_computed=False)


def verify(output,inputs,config):
    output=Path(output);prior=read(output/'SOURCE.json')
    source=output/'month.pgn.zst' if config.get('download') else Path(inputs['source']['path'])
    assert filehash(source)==prior['source_sha256']
    result=prepare(source,output/'VERIFY_SELECTED.jsonl.gz',output/'VERIFY_FEATURES.npz',config.get('sample_probability',.01),config.get('max_games'))
    result['source_sha256']=filehash(source);assert result==prior
    assert filehash(output/'PRIVATE_SELECTED.jsonl.gz')==filehash(output/'VERIFY_SELECTED.jsonl.gz')
    with np.load(output/'PRIVATE_FEATURES.npz') as a,np.load(output/'VERIFY_FEATURES.npz') as b:
        assert np.array_equal(a['values'],b['values']) and np.array_equal(a['groups'],b['groups'])
    return dict(verified=True,complete_recalculation=True)
