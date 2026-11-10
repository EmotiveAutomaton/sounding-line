"""CH1 fixed-node Stockfish measurement, two single-thread engines per slot.

DESIGN CHECK: LESSONS 2-5. A one-legal-move board has k50=1. Unique mate-in-one
is distinguished from longer mates. Every scored position resets the engine;
replay compares all scores rather than only its preferred move. Bad pins and
illegal moves refuse; scores do not establish a human association.
"""
from __future__ import annotations
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import gzip, hashlib, json, math, threading, time
import chess, chess.engine
import numpy as np
from .week5_ch_source import digest, write_json


def cp_value(score):
    """Keep mating scores explicit; numeric sentinel is only for ordering/gaps."""
    if score.is_mate():
        mate=score.mate()
        return float(100000-1000*mate if mate>0 else -100000-1000*mate)
    return float(score.score())


def summarize(infos, side, played, played_info=None):
    top=[]
    for info in infos:
        score=info['score'].pov(side);move=info['pv'][0].uci()
        top.append(dict(move=move,cp=cp_value(score),mate=score.mate(),nodes=info.get('nodes')))
    top.sort(key=lambda row:(-row['cp'],row['move']))
    if not top:raise ValueError('No engine principal variation')
    played_score=next((row for row in top if row['move']==played),None)
    if played_score is None:
        if played_info is None:raise ValueError('Played move absent and not measured')
        score=played_info['score'].pov(side)
        played_score=dict(cp=cp_value(score),mate=score.mate())
    best=top[0]['cp'];values=[x['cp'] for x in top]
    mating=any(row['mate'] is not None for row in top) or played_score['mate'] is not None
    return dict(top=top,k50=sum(best-x<=50 for x in values),k100=sum(best-x<=100 for x in values),
                best_gap=(values[0]-values[1]) if len(values)>1 else None,
                breadth=max(0,sum(best-x<=50 for x in values)-2),
                stakes=abs(best),centipawn_loss=max(0.,best-played_score['cp']),
                played_cp=played_score['cp'],played_mate=played_score['mate'],
                mate_sentinel_used=mating)


class Scorer:
    def __init__(self,path,nodes=1000000):
        self.engine=chess.engine.SimpleEngine.popen_uci(str(path),timeout=180.)
        self.engine.configure({'Threads':1,'Hash':64})
        self.nodes=nodes
    def score(self,row):
        board=chess.Board(row['fen']);move=chess.Move.from_uci(row['uci'])
        if move not in board.legal_moves:raise ValueError('Source played move illegal')
        # A new game identity causes python-chess to send ucinewgame before search.
        infos=self.engine.analyse(board,chess.engine.Limit(nodes=self.nodes),multipv=min(5,board.legal_moves.count()),game=object())
        played_info=None
        if not any(info['pv'][0]==move for info in infos):
            played_info=self.engine.analyse(board,chess.engine.Limit(nodes=self.nodes),root_moves=[move],game=object())
        result=summarize(infos,board.turn,move.uci(),played_info)
        return dict(position=row,engine=result,node_limit=self.nodes,threads=1,hash_mb=64)
    def close(self):self.engine.quit()


def score_key(row,nodes):
    return hashlib.sha256(json.dumps([row,nodes],sort_keys=True,separators=(',',':')).encode()).hexdigest()


def iter_positions(path):
    with gzip.open(path,'rt',encoding='utf8') as f:
        for line in f:yield json.loads(line)


def score_batch(source,executable,output,nodes=1000000,wall_seconds=600,max_positions=None,offset=0):
    """Return a checkpoint/yield, never a false completed population result."""
    output=Path(output);output.mkdir(parents=True,exist_ok=True);start=time.monotonic()
    engines=[Scorer(executable,nodes),Scorer(executable,nodes)];completed=reused=attempted=0
    try:
        with ThreadPoolExecutor(max_workers=2) as pool:
            batch=[]
            for index,row in enumerate(iter_positions(source)):
                if index<offset:continue
                if max_positions is not None and attempted>=max_positions:break
                key=score_key(row,nodes);path=output/(key+'.json')
                if path.exists():
                    prior=json.loads(path.read_text(encoding='utf8'))
                    if prior['position']!=row or prior['node_limit']!=nodes:raise ValueError('Changed saved position')
                    reused+=1;attempted+=1;continue
                if time.monotonic()-start>=wall_seconds:break
                batch.append((row,path));attempted+=1
                if len(batch)==2:
                    futures=[pool.submit(engines[i].score,item[0]) for i,item in enumerate(batch)]
                    for (_,path),future in zip(batch,futures):write_json(path,future.result());completed+=1
                    batch=[]
            if batch:
                row,path=batch[0];write_json(path,engines[0].score(row));completed+=1
    finally:
        for engine in engines:engine.close()
    return dict(new_positions=completed,reused_positions=reused,visited_positions=attempted,
                next_offset=offset+attempted,wall_seconds=time.monotonic()-start,node_limit=nodes,
                population_complete=False)


def replay_scores(executable,paths):
    engines={};counts=0
    try:
        for path in paths:
            original=json.loads(Path(path).read_text(encoding='utf8'));nodes=original['node_limit']
            engine=engines.setdefault(nodes,Scorer(executable,nodes)) if nodes not in engines else engines[nodes]
            if engine.score(original['position'])!=original:raise ValueError('Fresh-process engine score disagreement')
            counts+=1
    finally:
        for engine in engines.values():engine.close()
    return dict(verified_positions=counts,all_scores_equal=True)


def fit_temperature(scores,played_indices):
    """Held-out-month choice temperature; absent top-five choices are counted."""
    from scipy.optimize import minimize_scalar
    from scipy.special import logsumexp
    supported=[(np.asarray(s,float),int(i)) for s,i in zip(scores,played_indices) if i is not None]
    if len(supported)<20:return dict(status='below floor, descriptive',temperature=100.,supported=len(supported),fallback='fixed 100 centipawns')
    def objective(logtemp):
        temp=math.exp(logtemp)
        return sum(logsumexp(s/temp)-s[i]/temp for s,i in supported)
    fit=minimize_scalar(objective,bounds=(math.log(1.),math.log(10000.)),method='bounded')
    if not fit.success:raise ValueError('Temperature optimization failed')
    return dict(status='fitted',temperature=math.exp(fit.x),supported=len(supported),excluded=len(scores)-len(supported))


def policy_entropy(scores,temperature):
    x=np.asarray(scores,float)/temperature;x-=x.max();p=np.exp(x);p/=p.sum()
    return float(-np.sum(p*np.log(np.maximum(p,np.finfo(float).tiny))))


def execute(output,inputs,config):
    output=Path(output);output.mkdir(parents=True,exist_ok=True)
    executable=Path(inputs['engine']['path'])
    if digest(executable)!=inputs['engine']['sha256']:raise ValueError('Engine pin changed')
    if config.get('phase')=='verify':
        result=replay_scores(executable,sorted(Path(inputs['scores']['path']).glob('*.json')))
        write_json(output/'VERIFY.json',result)
    else:
        result=score_batch(inputs['positions']['path'],executable,output/'PRIVATE_SCORES',config.get('nodes',1000000),min(600,config.get('wall_seconds',600)),config.get('max_positions'),config.get('offset',0))
        write_json(output/'BATCH.json',result)
    return dict(status='complete',scientific_effect_computed=False)


def verify(output,inputs,config):
    result=replay_scores(inputs['engine']['path'],sorted((Path(output)/'PRIVATE_SCORES').glob('*.json')))
    write_json(Path(output)/'VERIFY.json',result)
    return dict(verified=True,complete_recalculation=True,**result)

