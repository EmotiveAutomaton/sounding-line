from copy import deepcopy
from pathlib import Path
from collections import defaultdict
import math
import json
import numpy as np
import pytest
from runners.drive.cards import timing_d30_paired as card
from runners.drive.cards import timing_d30_specification as spec
from runners.drive.cards.timing_census import read,write,filehash
from runners.drive.cards.timing_p6 import gzwrite,gzread
from runners.drive.cards.timing_stats import sufficient,fit

SMALL=dict(card.CONFIG,bootstrap_draws=100,permutations=200)

def matrix(signal=1,identical=False):
 rng=np.random.default_rng(81);own=[];fake=[];y=[];writers=[]
 for w in range(8):
  for j in range(100):
   x=j%2;z=float(rng.normal());own.append([x,z]);fake.append([x if identical else 1-x,z])
   y.append(signal*x+.5*z+w+float(rng.normal(0,.02)));writers.append(str(w))
 return dict(own=own,fake=fake,y=y,writers=writers)

@pytest.mark.parametrize('signal,state',[(1,'positive'),(-1,'negative')])
def test_known_signed_pair(signal,state):
 got=card.compute(matrix(signal),SMALL)
 assert got['primary']['state']==state
 assert got['primary']['effect']==pytest.approx(2*signal,abs=.01)
 assert got['controls']['paired_gap']['permutations']==200

def test_identical_pairs_are_exact_null():
 got=card.compute(matrix(identical=True),SMALL)
 assert got['primary']==dict(effect=0.,ci_low=0.,ci_high=0.,state='null',expected_direction=1)
 assert got['controls']['paired_gap']['upper_tail_permutation_p']==1
 assert not got['controls']['paired_gap']['bias_flag']

def test_sufficient_fit_matches_independent_dummy_regression():
 m=matrix();writers=np.asarray(m['writers']);dummies=np.array([[w==level for level in sorted(set(writers))] for w in writers],float)
 for arm in ('own','fake'):
  design=np.column_stack([m[arm],dummies]);expected=np.linalg.lstsq(design,m['y'],rcond=None)[0][0]
  assert fit(sufficient(m[arm],m['y'],writers,True))[0]==pytest.approx(expected,abs=1e-11)
  assert float(spec.coefficient_weights(m[arm],writers)@m['y'])==pytest.approx(expected,abs=1e-11)

def test_pairs_use_same_real_writer_draws(monkeypatch):
 m=matrix();seen=[];actual=card.fit;build=card.sufficient;identities={}
 def indexed(*args,**kwargs):
  groups=build(*args,**kwargs);identities.update({id(g):i for i,g in enumerate(groups)});return groups
 def capture(groups):seen.append([identities[id(g)] for g in groups]);return actual(groups)
 monkeypatch.setattr(card,'sufficient',indexed)
 monkeypatch.setattr(card,'fit',capture)
 card.compute(m,dict(SMALL,bootstrap_draws=10,permutations=20))
 assert len(seen)==22
 assert all(seen[i]==seen[i+1] for i in range(2,len(seen),2))

def test_saved_boundary_resume_and_mutation(tmp_path):
 m=matrix();assert card.compute(m,SMALL,tmp_path,lambda phase:phase=='bootstrap-boundary')['status']=='yielded'
 block=tmp_path/'bootstrap/block-00000.json';old=block.read_bytes()
 got=card.compute(m,SMALL,tmp_path);assert block.read_bytes()==old
 assert got==card.compute(m,SMALL)
 block.write_bytes(old+b' ')
 with pytest.raises(ValueError,match='hash'):card.compute(m,SMALL,tmp_path)

def test_refuses_nuisance_mismatch_and_unsupported_target():
 m=matrix();m['fake'][0][1]+=1
 with pytest.raises(ValueError,match='nuisance'):card.compute(m,SMALL)
 m=matrix();m['fake']=[[1,x[1]] for x in m['fake']]
 with pytest.raises(ValueError,match='support'):card.compute(m,SMALL)

def test_reference_bias_can_fail_and_null_passes():
 assert card.reference(1,[1]*200)['bias_flag']
 assert not card.reference(0,[-1,1]*100)['bias_flag']
 with pytest.raises(ValueError):card.reference(0,[float('nan')]*200)

def test_revision_bigrams_use_both_constituents():
 words=[dict(index=0,token='a',is_word=True,previous_typed_token_index=None),dict(index=1,token='b',is_word=True,previous_typed_token_index=0)]
 rows=[dict(session='s',index=0,marker='word:a'),dict(session='s',index=0,marker='bigram:a b')]
 labels={'s':dict(rows=[dict(index=i,counts={k:int(k==('immediate_user_deletion' if i==0 else 'later_user_edit')) for k in card.LABELS}) for i in range(2)])}
 out=card.revision_join(rows,labels,[dict(session='s',words=words)])
 assert out[0]['immediate_user_deletion'] and not out[0]['later_user_edit']
 assert out[1]['immediate_user_deletion'] and out[1]['later_user_edit']
 with pytest.raises(ValueError,match='constituent'):card.revision_join([dict(rows[1],marker='bigram:a c')],labels,[dict(session='s',words=words)])

def known_rows():
 rng=np.random.default_rng(17);rows=[]
 for writer in range(8):
  for prompt in range(6):
   for replicate in range(2):
    sid=f'{writer}-{prompt}-{replicate}';index=0
    counts={'word:other':200}
    for owner in range(8):
     counts[f'word:habit{owner}']=80+7*writer if owner==writer else 2
     # A distinct donor supplies the other-prompt baseline. This gives a
     # reassigned history real local support; homogeneous donors do not.
     counts[f'word:local{owner}']=(80 if prompt==0 else 0) if owner==writer else (80+3*writer if writer==(owner+1)%8 and prompt!=0 else 0)
    for marker,count in counts.items():
     for j in range(count):
      local=marker==f'word:local{writer}'
      rows.append(dict(writer=str(writer),prompt=str(prompt),session=sid,marker=marker,index=index,ordinal=index,
       token=marker[5:],is_word=True,previous_typed_token_index=None,pause_seconds=math.exp(int(local)+float(rng.normal(0,.03))),first_delta_characters=1,
       population_surprisal=float(rng.uniform(1,4)),population_log_frequency=float(rng.normal()),length=int(rng.integers(2,8)),sentence_start=j%5==0,after_punctuation=j%7==0,revised=bool(local and j%3)))
      index+=1
 return rows

def fixture(root):
 root=Path(root);rows=known_rows();by_session=defaultdict(list)
 for row in rows:by_session[row['session']].append(row)
 p6=root/'p6';index=[];labels=root/'labels';li=[]
 for sid,words in sorted(by_session.items()):
  file='sessions/'+sid+'.json.gz';gzwrite(p6/file,dict(session=sid,words=words))
  index.append(dict(session=sid,file=file,sha256=filehash(p6/file)))
  value=dict(session=sid,occurrence_count=len(words),rows=[dict(index=r['index'],counts={k:int((r['index']%13==0 and k=='later_user_edit') or (r['index']%17==0 and k=='immediate_user_deletion')) for k in card.LABELS}) for r in words])
  gzwrite(labels/'output'/file,value);li.append(dict(session=sid,file=file,sha256=filehash(labels/'output'/file)))
 write(p6/'INDEX.json',index);write(labels/'output/INDEX.json',li)
 write(labels/'COMPLETE.json',dict(status='COMPLETE',fresh_process_verified=True,synthetic_fixture=True,outputs={p.relative_to(labels).as_posix():filehash(p) for p in labels.rglob('*') if p.is_file()}))
 write(root/'proof.json',dict(verified=True,write_through_complete=True,complete_sha256=filehash(labels/'COMPLETE.json')))
 design,markers=spec.designs(rows,'per_character');inputs={}
 for name,extension in (('primary',False),('extension',True)):
  out=root/name;config=dict(spec.prior.ORIGINAL_CONFIG,extension=extension)
  write(out/'PLAN.json',dict(module='runners.drive.cards.timing_d30',config=config,pins={},inputs=dict(p6_index=str((p6/'INDEX.json').resolve()))))
  gzwrite(out/'output/D30_INTERMEDIATES.json.gz',dict(rows=rows,config=config,timing_mode='per_character'))
  write(out/'output/D30_MARKERS.json',markers)
  write(out/'output/D30_PRIMARY.json',dict(effect=fit(sufficient(design['designs'][int(extension)],design['y'],design['writers'],True))[0],observations=len(design['y']),writers=len(set(design['writers']))))
  write(out/'COMPLETE.json',dict(status='COMPLETE',fresh_process_verified=True,synthetic_fixture=True,outputs={p.relative_to(out).as_posix():filehash(p) for p in out.rglob('*') if p.is_file()}))
  inputs[name+'_completion']=str((out/'COMPLETE.json').resolve())
 return dict(inputs,revision_complete=str((labels/'COMPLETE.json').resolve()),revision_proof=str((root/'proof.json').resolve()))

def test_complete_source_preserves_primary_and_paired_population(tmp_path):
 inputs=fixture(tmp_path);m,e=card.source(inputs,card.CONFIG)
 assert e['original_occurrences']>e['paired_occurrences']>0
 assert e['full_original_effect']==pytest.approx(1,abs=.02)
 assert len(m['y'])==len(m['writers'])==len(m['own'])==len(m['fake'])
 assert len(e['revision_flags'])==e['original_occurrences']
 assert all(a[1:]==b[1:] for a,b in zip(m['own'],m['fake']))
 for ext in (False,True):
  cfg=dict(card.CONFIG,card='D30-extension.fake' if ext else 'D30.fake',extension=ext)
  assert card.source(inputs,cfg)[1]['primary_source_indices']==e['primary_source_indices']

def test_whole_handler_reentry_fresh_replay_and_changed_source(tmp_path):
 inputs=fixture(tmp_path/'source');out=tmp_path/'out';write(out/'YIELD_REQUEST.json',{})
 assert card.execute(out,inputs,card.CONFIG)['status']=='yielded'
 (out/'YIELD_REQUEST.json').unlink();result=card.execute(out,inputs,card.CONFIG)
 assert card.verify(out,inputs,card.CONFIG)['primary']==result
 assert card.execute(out,inputs,card.CONFIG)==result
 proof=read(inputs['revision_proof']);Path(inputs['revision_proof']).write_text(json.dumps(dict(proof,write_through_complete=False)),encoding='utf8')
 with pytest.raises(ValueError):card.verify(out,inputs,card.CONFIG)

def test_config_and_cap_refuse(tmp_path):
 with pytest.raises(ValueError):card.validate(dict(card.CONFIG,bootstrap_draws=True))
 write(tmp_path/'ACTIVE_TIME.json',dict(seconds=3601))
 with pytest.raises(TimeoutError):card.execute(tmp_path,{},card.CONFIG)

def native_answers():
 for signal,state in ((1,'positive'),(-1,'negative')):
  value=card.compute(matrix(signal),SMALL)
  assert value['primary']['state']==state and abs(value['primary']['effect']-2*signal)<.01
 assert card.compute(matrix(identical=True),SMALL)['primary']==dict(effect=0.,ci_low=0.,ci_high=0.,state='null',expected_direction=1)
 return dict(positive=True,negative=True,identical_exact_null=True)

def execute(output,inputs,config):
 answers=native_answers();result=card.execute(output,inputs,config)
 write(Path(output)/'NATIVE_ANSWERS.json',answers)
 return result

def verify(output,inputs,config):
 assert read(Path(output)/'NATIVE_ANSWERS.json')==native_answers()
 return card.verify(output,inputs,config)
