import numpy as np
import pytest
import gzip
import json
import os
import subprocess
import sys
import math

from runners.drive.cards.events_d35 import chronological_partition,build_metrics,primary_from_rows,adjusted_change,refit_projection,execute,verify
from runners.drive.cards.events_p5 import write,filehash


def test_odd_even_sessions_are_chronological_and_disjoint():
    ss=[dict(session=str(i),timestamp=i) for i in reversed(range(8))]
    assert chronological_partition(ss)=={"0":"direction","1":"baseline","2":"direction","3":"baseline",
                                          "4":"later","5":"later","6":"later","7":"later"}


def session(writer,i,direction):
    vectors=np.array([[1.,0.],[0.,direction],[0.,direction] if i>=2 else [1.,0.],[1.,0.]])
    return dict(writer=writer,session=f"{writer}{i}",timestamp=i,prompt="p",model_share=0.,vectors=vectors,
                edits=[dict(ordinal=j,split="content",origin="own",before_vector=0,after_vector=1) for j in range(5)] if i==0 else [],
                sentences=[dict(writer_typed=True,content_correction_touched=False,vector=2),
                           dict(writer_typed=True,content_correction_touched=True,vector=3)])


def test_planted_alignment_is_positive_and_direction_shuffle_breaks_it():
    ss=[session(w,i,d) for w,d in [("a",1),("b",-1),("c",1),("d",-1)] for i in range(4)]
    rows,support,directions=build_metrics(ss)
    assert support["eligible_writers"]==4
    assert len(rows)==12
    assert all(r["sentences"]==1 for r in rows)  # corrected sentences excluded
    result=primary_from_rows(rows,bootstrap=50)
    # Each residual direction is +/-1/sqrt(2), and excluding self makes the
    # three-donor mean the opposite direction divided by three.
    assert result["effect"]==pytest.approx(2*np.sqrt(2)/3)
    assert result["state"]=="positive"
    assert result["writer_shuffled_direction_effect"]<result["effect"]


def test_no_change_is_exact_null_with_zero_width_interval():
    rows=[dict(writer=w,prompt="p",phase=phase,model_share=0.,projection_gap=0.,shuffled_projection_gap=0.)
          for w in ("a","b","c") for phase in (0,1)]
    result=primary_from_rows(rows,bootstrap=20)
    assert result["effect"]==0
    assert result["ci95"]==[0,0]
    assert result["state"]=="null"
    assert result["standard_error"]==0 and result["z"] is None and result["p_approx"] is None


def test_opposite_known_answer_is_negative():
    rows=[dict(writer=w,prompt="p",phase=phase,model_share=0.,projection_gap=-phase,shuffled_projection_gap=0.)
          for w in ("a","b","c") for phase in (0,1)]
    result=primary_from_rows(rows,bootstrap=20)
    assert result["effect"]==pytest.approx(-1)
    assert result["state"]=="negative"


def test_equal_writer_phase_weight_ignores_duplicate_sessions():
    rows=[dict(writer=w,prompt="p",phase=phase,model_share=0.,projection_gap=effect*phase,shuffled_projection_gap=0.)
          for w,effect in (("a",1),("b",3)) for phase in (0,1)]
    one=primary_from_rows(rows,bootstrap=30)
    many=primary_from_rows(rows+rows[:2]*9,bootstrap=30)
    assert one["effect"]==pytest.approx(2)
    assert many["effect"]==pytest.approx(one["effect"])
    assert one["standard_error"]>0
    assert one["p_approx"]==pytest.approx(math.erfc(abs(one["effect"]/one["standard_error"])/np.sqrt(2)))


def test_prompt_phase_confound_is_invalid_not_null():
    rows=[dict(writer=w,prompt=str(phase),phase=phase,model_share=0.,projection_gap=phase,shuffled_projection_gap=0.)
          for w in ("a","b","c") for phase in (0,1)]
    assert primary_from_rows(rows,bootstrap=20)["state"]=="invalid"


def test_one_writer_has_no_population_interval():
    rows=[dict(writer="a",prompt="p",phase=phase,model_share=0.,projection_gap=phase,shuffled_projection_gap=0.) for phase in (0,1)]
    assert primary_from_rows(rows,bootstrap=20)["state"]=="invalid"


def test_training_support_exclusion_is_visible():
    rows,support,directions=build_metrics([session("a",i,1) for i in range(3)])
    assert rows==[] and directions=={}
    assert support["exclusions"]=={"fewer_than_four_sessions":1}


def test_nonfinite_covariates_cannot_reach_result():
    with pytest.raises(ValueError,match="nonfinite"):
        adjusted_change(np.array([[1.,float("nan")],[1.,0.]]),np.array([0,1]),np.array([0,1]),np.ones(2))


def test_bootstrap_refits_shared_direction_and_donor_means():
    ss=[session(w,i,d) for w,d in [("a",1),("b",-1),("c",1),("d",-1)] for i in range(4)]
    rows,_,_,moments=build_metrics(ss,retain_moments=True)
    original,_=refit_projection(rows,moments,np.ones(4,int))
    assert np.any(np.abs(original)>0)
    with pytest.raises(ValueError,match="distinct sampled writers"):
        refit_projection(rows,moments,np.array([4,0,0,0]))
    # Exclude both copies of the first recipient, not just one of them.
    multiplicity=np.array([2,1,1,0])
    projected,directions=refit_projection(rows,moments,multiplicity)
    writers=sorted(directions)
    for row,value in zip(rows,projected):
        donors=[directions[w] for w,n in zip(writers,multiplicity) if w!=row['writer'] for _ in range(n)]
        known=np.asarray(moments['session_means'][row['session']])@(directions[row['writer']]-np.mean(donors,axis=0))
        assert value==pytest.approx(known)
    result=primary_from_rows(rows,bootstrap=50,moments=moments)
    assert result["effect"]==pytest.approx(2*np.sqrt(2)/3)


def test_execute_and_fresh_process_primary_recomputation(tmp_path):
    ss=[session(w,i,d) for w,d in [("a",1),("b",-1),("c",1),("d",-1)] for i in range(4)]
    p5=[];p2=[]
    for s in ss:
        stem=s["session"]; vectors=s.pop("vectors")
        with gzip.open(tmp_path/f"{stem}.json.gz","wt",encoding="utf8") as f:
            json.dump(s,f)
        np.save(tmp_path/f"{stem}.npy",vectors,allow_pickle=False)
        write(tmp_path/f"{stem}_p2.json",dict(final_spans=[]))
        p5.append(dict(session=stem,file=f"{stem}.json.gz",sha256=filehash(tmp_path/f"{stem}.json.gz"),
                       vectors=f"{stem}.npy",vectors_sha256=filehash(tmp_path/f"{stem}.npy")))
        p2.append(dict(session=stem,file=f"{stem}_p2.json",sha256=filehash(tmp_path/f"{stem}_p2.json")))
    write(tmp_path/"p5.json",p5);write(tmp_path/"p2.json",p2);write(tmp_path/"p5_summary.json",dict(sessions=len(ss)))
    write(tmp_path/'P5_COMPLETE.json',dict(status='COMPLETE',outputs={n:filehash(tmp_path/n) for n in ('p5.json','p5_summary.json')}))
    write(tmp_path/'P2_COMPLETE.json',dict(status='COMPLETE',outputs={'p2.json':filehash(tmp_path/'p2.json')}))
    inputs=dict(p5_index=str(tmp_path/"p5.json"),p5_summary=str(tmp_path/"p5_summary.json"),p2_index=str(tmp_path/"p2.json"),
                p5_completion=str(tmp_path/'P5_COMPLETE.json'),p2_completion=str(tmp_path/'P2_COMPLETE.json'))
    config=dict(bootstrap=2000,seed=20261017)
    write(tmp_path/'out/YIELD_REQUEST.json',dict(reason='fixture saved boundary'))
    assert execute(tmp_path/'out',inputs,config)['status']=='yielded'
    assert not (tmp_path/'out/SUMMARY.json').exists()
    (tmp_path/'out/YIELD_REQUEST.json').unlink()
    result=execute(tmp_path/"out",inputs,config)
    assert result["primary"]["effect"]==pytest.approx(2*np.sqrt(2)/3)
    assert result['primary']['state']=='invalid' and result['primary']['bootstrap_invalid']>0
    write(tmp_path/"call.json",dict(inputs=inputs,config=config))
    code="import ctypes,json,sys; from pathlib import Path; ctypes.windll.kernel32.SetPriorityClass(ctypes.windll.kernel32.GetCurrentProcess(),0x4000); from runners.drive.cards.events_d35 import verify; p=Path(sys.argv[1]); a=json.loads((p/'call.json').read_text()); assert verify(p/'out',a['inputs'],a['config'])['verified']"
    env=dict(os.environ,PYTHONHASHSEED="973")
    completed=subprocess.run([sys.executable,"-B","-c",code,str(tmp_path)],capture_output=True,text=True,env=env,timeout=60)
    assert completed.returncode==0,completed.stderr
    (tmp_path/"out"/"SESSION_METRICS.json").write_text("[]",encoding="utf8")
    with pytest.raises(ValueError,match="output changed"):
        verify(tmp_path/"out",inputs,config)


def test_checkpoint_resume_preserves_bootstrap_exactly_and_refuses_mutation(tmp_path):
    rows=[dict(writer=w,prompt='p',phase=phase,model_share=0.,projection_gap=effect*phase,shuffled_projection_gap=0.)
          for w,effect in [('a',1.),('b',2.),('c',3.),('d',4.)] for phase in (0,1)]
    expected=primary_from_rows(rows,bootstrap=200)
    write(tmp_path/'YIELD_REQUEST.json',dict(reason='fixture'))
    assert primary_from_rows(rows,bootstrap=200,checkpoint=tmp_path)['status']=='yielded'
    (tmp_path/'YIELD_REQUEST.json').unlink()
    assert primary_from_rows(rows,bootstrap=200,checkpoint=tmp_path)==expected
    p=tmp_path/'D35_BOOT_00000.json'
    data=json.loads(p.read_text());data['fits'][0]+=1;p.write_text(json.dumps(data))
    with pytest.raises(ValueError,match='hash/sequence changed'):
        primary_from_rows(rows,bootstrap=200,checkpoint=tmp_path)
