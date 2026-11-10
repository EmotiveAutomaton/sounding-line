"""Actual recent-window intake flow against a constructed immutable API tape."""
from pathlib import Path
import argparse,copy,json,shutil,subprocess,sys
from . import week5_bk_wiki_intake as w
from .week5_bk_klicke_intake import write,read,digest

START='2026-10-31T20:00:00Z';END='2026-11-07T20:00:00Z'


def tape():
    records=[]
    def add(params,body):records.append(dict(params=w.safe_params(params),response=body))
    def page(pid,revisions):return dict(query=dict(pages=[dict(pageid=pid,ns=0,title='Constructed article '+str(pid),revisions=revisions)]))
    def random(pid):add(dict(list='random',rnnamespace=0,rnfilterredir='nonredirects',rnlimit=1),dict(query=dict(random=[dict(id=pid,ns=0,title='Constructed article '+str(pid))])))
    def eligibility(pid,count):add(dict(prop='revisions',pageids=pid,rvprop='ids|timestamp',rvlimit=50,rvstart=END,rvdir='older'),page(pid,[dict(revid=i,timestamp=START) for i in range(count)]))
    random(9);eligibility(9,49);random(10);eligibility(10,50);random(10);random(11);eligibility(11,50)
    def revision(i,parent,stamp,text):return dict(revid=i,parentid=parent,timestamp=stamp,sha1=w.content_hash(text),slots=dict(main=dict(content=text)))
    revs=[revision(101,100,'2026-11-01T12:00:00Z','First constructed sentence.'),revision(102,101,'2026-11-02T12:00:00Z','Second constructed sentence.'),revision(103,102,'2026-11-03T12:00:00Z','First constructed sentence.')]
    params=dict(prop='revisions',pageids=10,rvprop='ids|timestamp|sha1|content',rvslots='main',rvlimit=50,rvstart=END,rvend=START,rvdir='older')
    first=page(10,[revs[2],revs[1]]);first['continue']={'continue':'||','rvcontinue':'constructed_revision_token'};add(params,first);add(dict(params,**first['continue']),page(10,[revs[0]]))
    flags=[dict(pageid=10,revid=r['revid'],old_revid=r['parentid'],timestamp=r['timestamp'],sha1=r['sha1'],bot=i==1) for i,r in enumerate(revs)]
    params=dict(list='recentchanges',rcnamespace=0,rctype='edit|new',rctitle='Constructed article 10',rcprop='ids|timestamp|flags|sha1',rclimit=500,rcstart=START,rcend=END,rcdir='newer')
    first=dict(query=dict(recentchanges=flags[:2]),**{'continue':{'continue':'||','rccontinue':'constructed_flag_token'}});add(params,first);add(dict(params,**first['continue']),dict(query=dict(recentchanges=flags[2:])))
    add(dict(prop='revisions',revids=100,rvprop='ids|timestamp|sha1|content',rvslots='main'),page(10,[revision(100,99,'2026-10-30T12:00:00Z','Left-censored baseline sentence.')]))
    add(dict(prop='revisions',pageids=11,rvprop='ids|timestamp|sha1|content',rvslots='main',rvlimit=50,rvstart=END,rvend=START,rvdir='older'),page(11,[]))
    add(dict(list='recentchanges',rcnamespace=0,rctype='edit|new',rctitle='Constructed article 11',rcprop='ids|timestamp|flags|sha1',rclimit=500,rcstart=START,rcend=END,rcdir='newer'),dict(query=dict(recentchanges=[])))
    return records


def checks():
    for params in (dict(rvuser='constructed-person'),dict(rcprop='ids|user'),dict(aufrom='constructed-person')):
        try:w.safe_params(params)
        except ValueError:pass
        else:raise AssertionError('Identity query accepted')
    assert w.content_hash('')=='phoiac9h4m842xq45sp7s6u21eteeq1'
    return dict(identity_queries_refused=True,independent_sha1_base36_empty_oracle=True)


def main():
    p=argparse.ArgumentParser();p.add_argument('--output',required=True,type=Path);p.add_argument('--verify',action='store_true');a=p.parse_args();root=a.output
    config=dict(card='BK-T2.r-recent-intake',mode='constructed',articles=2,window_start=START,window_end=END,max_new_draws=1);inputs=dict(constructed_wire=str(root/'TAPE.json'))
    if a.verify:
        result=w.verify(root/'resumed',inputs,config);bad=root/'false-output';shutil.copytree(root/'resumed',bad);path=bad/'articles/00000.json.gz';record=read(path);record['revisions'][0]['bot_flag']=True;path.unlink();write(path,record)
        try:w.verify(bad,inputs,config)
        except ValueError:pass
        else:raise AssertionError('False bot projection accepted')
        print(json.dumps(dict(replay=result,false_projection_refused=True,checks=checks())));return
    root.mkdir(parents=True,exist_ok=True);write(root/'TAPE.json',tape());check=checks()
    pilot=w.execute(root/'pilot',inputs,config);assert pilot['status']=='yielded' and pilot['completed_units']==1
    shutil.copytree(root/'pilot',root/'resumed');config['max_new_draws']=2;result=w.execute(root/'resumed',inputs,config);assert result['new_articles']==1
    r=read(root/'resumed/articles/00000.json.gz');assert [v['revision'] for v in r['revisions']]==[101,102,103] and [v['bot_flag'] for v in r['revisions']]==[False,True,False]
    assert r['revisions'][0]['sha1']==r['revisions'][2]['sha1'] and r['baseline']['left_censored'] is True and r['baseline']['bot_flag'] is None
    roster=read(root/'resumed/ROSTER.json');assert len(roster['considered'])==4 and len(roster['articles'])==2
    assert read(root/'resumed/articles/00001.json.gz')['revisions']==[]
    child=subprocess.run([sys.executable,'-X','utf8','-B','-m','runners.drive.cards.week5_bk_wiki_fixture','--output',str(root),'--verify'],capture_output=True,text=True)
    if child.returncode:raise RuntimeError(child.stderr[-3000:])
    write(root/'COMPLETE.json',dict(passed=True,constructed=True,checks=check,random_eligibility_and_duplicate_preserved=True,revision_and_flag_pagination=True,exact_bot_flags=True,left_censored_baseline_unknown=True,repeated_sha_preserved=True,quantum_resume=True,fresh_process=json.loads(child.stdout),pins={n:digest(Path(__file__).with_name(n)) for n in ('week5_bk_wiki_intake.py','week5_bk_wiki_fixture.py','week5_bk_klicke_intake.py')}));print(json.dumps(dict(passed=True,full_frozen_wire_replay=True)))


if __name__=='__main__':main()
