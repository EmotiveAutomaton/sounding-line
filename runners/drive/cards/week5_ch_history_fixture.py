"""Native serialized CH4/CH6 constructed-world and complete replay checks."""
from pathlib import Path
import argparse,json,math,sqlite3,subprocess,sys
import numpy as np
from . import week5_ch_histories as h
from . import week5_ch_history_index as index
from .week5_ch_source import digest,write_json


def run(output):
    output=Path(output);output.mkdir(parents=True,exist_ok=True);database=output/'constructed.sqlite'
    if database.exists():raise FileExistsError(database)
    con=sqlite3.connect(database);con.execute('CREATE TABLE histories(month TEXT,ordinal INTEGER,payload TEXT)');con.execute('CREATE TABLE settings(key TEXT,value TEXT)');con.execute("INSERT INTO settings VALUES('constructed_fixture','true')")
    rng=np.random.default_rng(21107);ordinal=0
    for p in range(16):
        player=f'constructed-player-{p}';start=50000.;net=0
        for g in range(120):
            ordinal+=1;delta=int(rng.choice([-4,-2,2,4]));net+=delta;rows=[]
            for move in range(10,40):
                share=float(rng.uniform(.2,.95));deviation=share-.575
                logtime=1+.2*share+.002*move+3*min(deviation,0)-2*max(deviation,0)+rng.normal(0,.035)
                rows.append(dict(player=player,ply=2*move-1,clock_before=300*share,think_time=math.exp(logtime)))
            meta=dict(players=[player,'unused constructed opponent'],start=start,end=None,initial=300,increment=2,time_control='blitz',rating_changes=[delta,-delta],result='1-0' if delta>0 else '0-1')
            value=dict(game=f'constructed-{p}-{g}',meta=meta,first_clocks=[300,300],rows=rows)
            con.execute('INSERT INTO histories VALUES(?,?,?)',('2017-04',ordinal,json.dumps(value)))
            stop=rng.random()<(0.6 if net>0 else .2)
            start+=3600 if stop else 600
            if stop:net=0
    con.commit();con.close();original_inputs=dict(histories=dict(path=str(database),sha256=digest(database)))
    index.execute(output/'index',original_inputs,dict(constructed_fixture=True))
    inputs=dict(histories=dict(path=str(output/'index/PRIVATE_PLAYER_HISTORY.sqlite'),sha256=digest(output/'index/PRIVATE_PLAYER_HISTORY.sqlite')))
    configs=dict(CH4=dict(card='CH4',draws=16,floor=8,constructed_fixture=True),CH6=dict(card='CH6',draws=16,floor=8,constructed_fixture=True))
    for card,config in configs.items():
        h.execute(output/card,inputs,config);result=json.loads((output/card/'SCIENCE.json').read_text())
        assert result['status']=='complete'
        if card=='CH4':
            assert result['gain']>0 and result['learning_curve_players']==16
            assert len(result['learning_curve_profile_width_scale_only'])==4
        else:assert result['log_odds']>0 and result['counts']['right_censored_window_tail']==16
    write_json(output/'CONFIG.json',dict(inputs=inputs,configs=configs,original_inputs=original_inputs))
    child=subprocess.run([sys.executable,'-X','utf8','-B','-m','runners.drive.cards.week5_ch_history_fixture','--output',str(output),'--verify'],capture_output=True,text=True)
    if child.returncode:raise RuntimeError(child.stderr[-3000:])
    write_json(output/'COMPLETE.json',dict(constructed=True,scientific_admission=False,checks=['CH4 chronological held-out planted target','CH4 complete five secondaries','CH6 positive standing stopping world','right-censored trailing games','entire serialized handlers fresh-process replay','disk-backed per-player complete source projection'],replay=json.loads(child.stdout),source_pins={name:digest(Path(__file__).with_name(name)) for name in ('week5_ch_histories.py','week5_ch_history_index.py','week5_ch_reserve_secondaries.py','week5_ch_models.py','week5_ch_collection.py','week5_ch_progress.py','week5_ch_grid.py')}))
    return dict(passed=True,constructed=True)


def main():
    p=argparse.ArgumentParser();p.add_argument('--output',required=True);p.add_argument('--verify',action='store_true');a=p.parse_args();output=Path(a.output)
    if a.verify:
        conf=json.loads((output/'CONFIG.json').read_text());result={card:h.verify(output/card,conf['inputs'],config) for card,config in conf['configs'].items()};result['index']=index.verify(output/'index',conf['original_inputs'],dict(constructed_fixture=True))
    else:result=run(output)
    print(json.dumps(result,sort_keys=True))

if __name__=='__main__':main()
