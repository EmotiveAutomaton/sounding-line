"""Occurrence-identity engineering recovery for commissioned D30.fake and D30-extension.fake, with revision timing secondaries.

DESIGN CHECK: LESSONS 3-5 and CONTROLS 1-6 reread October 19. Null paired
identical designs must produce exactly zero in every draw; a known positive
or reversed local-slowing difference must retain its sign. Reassignment keeps
the original outcomes, covariates and real-writer bootstrap clusters. Missing
classification is an explicit supported subset, never imputation. Every fixed
draw must fit; false source bindings, missing revision occurrences and changed
checkpoints refuse. Raw within-writer outcome shuffles are descriptive and can
fail the absolute-mean > quarter-SD bias rule under either scientific outcome.
No automaticity or attention mechanism is admitted by this comparison.
"""
from collections import Counter,defaultdict
from pathlib import Path
import hashlib
import json
import math
import time
import numpy as np
from . import timing_d30 as original, timing_d30_specification as spec
from .timing_stats import sufficient,fit,bind,check_binding
from .timing_census import read,filehash
from .timing_p6 import gzread,gzip_equal,write_equal
from .states_v2 import contrast_state
from runners.stage14.common import atomic

CONFIG=dict(card='D30.fake',extension=False,bootstrap_draws=2000,permutations=200,seed=20261017,permutation_seed=20261018)
LABELS=('immediate_user_deletion','later_user_edit','within_burst_user_insertion','non_user_change')

def validate(config):
 expected=dict(CONFIG,card='D30-extension.fake',extension=True) if config.get('extension') is True else CONFIG
 if config!=expected or any(type(config[k]) is not type(v) for k,v in expected.items()):
  raise ValueError('exact commissioned paired configuration required')

def eligible_rows(rows,mode):
 if mode not in ('per_character','per_word'):raise ValueError('valid original pause clock required')
 labels,evidence=original.classify_markers(rows)
 eligible=[]
 for index,row in enumerate(rows):
  label=labels.get((row['writer'],row['marker']))
  if label is None or row['pause_seconds'] is None or row['pause_seconds']<=0 or row['population_surprisal'] is None:continue
  if mode=='per_character' and row['first_delta_characters']!=1:continue
  eligible.append(dict(row,**label,source_index=index))
 kinds=defaultdict(set)
 for row in eligible:kinds[row['writer']].add(row['label'])
 return [r for r in eligible if kinds[r['writer']]=={'local','pervasive'}],evidence

def paired_design(rows,mode,extension):
 eligible,markers=eligible_rows(rows,mode)
 if len({r['writer'] for r in eligible})<3:raise ValueError('fewer than three original supported writers')
 x=[[int(r['label']=='local'),r['length'],r['population_log_frequency'],int(r['sentence_start']),int(r['after_punctuation']),r['population_surprisal']]+([r['own_count']] if extension else []) for r in eligible]
 y=[math.log(r['pause_seconds']) for r in eligible];writers=[r['writer'] for r in eligible]
 # Reproduce the original writer-shuffle assignment, including its preceding
 # marker-label RNG consumption. Only the classification changes in this arm.
 rng=np.random.default_rng(CONFIG['seed']);original.shuffle_marker_labels(eligible,rng)
 sessions=sorted({r['session'] for r in rows});owners={r['session']:r['writer'] for r in rows}
 if any(owners[r['session']]!=r['writer'] for r in rows):raise ValueError('multiple real owners in one session')
 assignment=dict(zip(sessions,rng.permutation([owners[s] for s in sessions]).tolist()))
 fake_labels,fake_evidence=original.classify_markers([dict(r,writer=assignment[r['session']]) for r in rows])
 keep=[i for i,r in enumerate(eligible) if (assignment[r['session']],r['marker']) in fake_labels]
 own=[x[i] for i in keep]
 fake=[[int(fake_labels[assignment[eligible[i]['session']],eligible[i]['marker']]['label']=='local')]+x[i][1:] for i in keep]
 matrix=dict(own=own,fake=fake,y=[y[i] for i in keep],writers=[writers[i] for i in keep])
 if len(set(matrix['writers']))<3:raise ValueError('fewer than three paired real writers')
 for arm in ('own','fake'):fit(sufficient(matrix[arm],matrix['y'],matrix['writers'],within=True))
 return matrix,dict(full_x=x,full_y=y,full_writers=writers,primary_source_indices=[r['source_index'] for r in eligible],paired_primary_indices=keep,
  original_occurrences=len(eligible),paired_occurrences=len(keep),excluded_occurrences=len(eligible)-len(keep),
  paired_real_writers=len(set(matrix['writers'])),session_writer_assignment=assignment,original_markers=markers,fake_markers=fake_evidence),eligible

def revision_join(rows,labels_by_session,p6_records):
 """Replay original occurrence order; a reused first word does not identify a pair."""
 identities=[]
 for session in p6_records:
  words=session['words'];sid=session['session']
  for word in words:
   if words[word['index']]!=word:raise ValueError('original occurrence index differs')
   identities.append((sid,word['index'],('word:' if word['is_word'] else 'punct:')+word['token'],[word['index']]))
   previous=word.get('previous_typed_token_index')
   if previous is None or not word['is_word'] or not words[previous]['is_word']:continue
   first=words[previous]
   identities.append((sid,first['index'],'bigram:'+first['token']+' '+word['token'],[first['index'],word['index']]))
 result=[]
 for row in rows:
  ix=row['source_index']
  if type(ix) is not int or not 0<=ix<len(identities):raise ValueError('missing original occurrence position')
  sid,index,marker,indices=identities[ix]
  if (sid,index,marker)!=(row['session'],row['index'],row['marker']):raise ValueError('original constituent position differs')
  record=labels_by_session[sid];flags={k:False for k in LABELS}
  for i in indices:
   if record['rows'][i]['index']!=i:raise ValueError('revision identity differs')
   for k in LABELS:flags[k]|=record['rows'][i]['counts'][k]>0
  result.append(flags)
 return result

def source(inputs,config):
 validate(config)
 if set(inputs)!={'primary_completion','extension_completion','revision_complete','revision_proof'}:raise ValueError('exact paired inputs required')
 original_inputs={k:inputs[k] for k in ('primary_completion','extension_completion')}
 baseline=spec.source(original_inputs,spec.CONFIG)
 root=Path(inputs['primary_completion']).parent;saved=gzread(root/'output/D30_INTERMEDIATES.json.gz')
 matrix,evidence,eligible=paired_design(saved['rows'],saved['timing_mode'],config['extension'])
 expected=baseline['designs'][int(config['extension'])]
 if evidence['full_x']!=expected or evidence['full_y']!=baseline['y'] or evidence['full_writers']!=baseline['writers']:
  raise ValueError('original design changed')
 previous=read(Path(inputs['extension_completion'] if config['extension'] else inputs['primary_completion']).parent/'output/D30_PRIMARY.json')
 effect=fit(sufficient(expected,baseline['y'],baseline['writers'],within=True))[0]
 if not math.isclose(effect,previous['effect'],rel_tol=1e-12,abs_tol=1e-12):raise ValueError('original point differs')
 complete=read(inputs['revision_complete']);proof=read(inputs['revision_proof']);labels_root=Path(inputs['revision_complete']).parent
 if complete.get('status')!='COMPLETE' or not complete.get('fresh_process_verified') or not proof.get('verified') or not proof.get('write_through_complete') or proof.get('complete_sha256')!=filehash(inputs['revision_complete']):raise ValueError('revision source not admitted')
 for name,digest in complete['outputs'].items():
  if filehash(labels_root/name)!=digest:raise ValueError('revision output changed')
 label_index=read(labels_root/'output/INDEX.json');label_records={r['session']:gzread(labels_root/'output'/r['file']) for r in label_index}
 if len(label_records)!=len(label_index):raise ValueError('duplicate revision sessions')
 plan=read(root/'PLAN.json');p6=Path(plan['inputs']['p6_index']);p6_records=[]
 for record in read(p6):
  path=p6.parent/record['file']
  if filehash(path)!=record['sha256']:raise ValueError('original P6 output changed')
  value=gzread(path);p6_records.append(value)
  if value['session']!=record['session'] or label_records[value['session']]['occurrence_count']!=len(value['words']):raise ValueError('revision/P6 population differs')
 if set(label_records)!={r['session'] for r in p6_records}:raise ValueError('revision source population differs')
 evidence['revision_flags']=revision_join(eligible,label_records,p6_records)
 evidence['full_original_effect']=effect;evidence['timing_mode']=saved['timing_mode']
 return matrix,evidence

def interval(point,draws,direction=1):
 a=np.asarray(draws,float)
 if a.ndim!=1 or len(a)<2 or not np.isfinite(a).all():raise ValueError('incomplete bootstrap')
 low,high=np.quantile(a,[.025,.975]).tolist()
 return dict(effect=point,ci_low=low,ci_high=high,state=contrast_state(point,low,high,direction),expected_direction=direction)

def reference(point,values):
 a=np.asarray(values,float)
 if a.ndim!=1 or len(a)<2 or not np.isfinite(a).all():raise ValueError('incomplete null reference')
 mean,sd=float(a.mean()),float(a.std(ddof=1));low,high=np.quantile(a,[.025,.975]).tolist()
 return dict(permutations=len(a),upper_tail_permutation_p=(1+int(np.count_nonzero(a>=point)))/(1+len(a)),mean=mean,sd=sd,ci_low=low,ci_high=high,bias_flag=abs(mean)>.25*sd,
  limit='raw outcome shuffling also destroys nuisance associations; descriptive reference')

def compute(matrix,config,output=None,checkpoint=None):
 y=np.asarray(matrix['y'],float);writers=matrix['writers'];levels=sorted(set(writers))
 if len(levels)<3:raise ValueError('fewer than three paired writers')
 if len(matrix['own'])!=len(matrix['fake']) or any(a[1:]!=b[1:] for a,b in zip(matrix['own'],matrix['fake'])):raise ValueError('paired rows or nuisance covariates differ')
 groups=[sufficient(matrix[k],y,writers,within=True) for k in ('own','fake')]
 points=[fit(g)[0] for g in groups];binding=hashlib.sha256(json.dumps(dict(matrix=matrix,config=config),sort_keys=True,allow_nan=False).encode()).hexdigest()
 rng=np.random.default_rng(config['seed'])
 def draw(run):
  selected=rng.integers(0,len(levels),len(levels))
  return [fit([g[i] for i in selected])[0] for g in groups] if run else None
 samples=spec.draw_series(Path(output)/'bootstrap' if output else None,binding,config['bootstrap_draws'],draw,
  on_tenth=(lambda *_:checkpoint('bootstrap-tenth')) if checkpoint else None,
  yield_requested=(lambda:checkpoint('bootstrap-boundary')) if checkpoint else None)
 if samples is None:return dict(status='yielded',phase='bootstrap')
 samples=np.asarray(samples,float);gap=points[0]-points[1];difference=samples[:,0]-samples[:,1]
 weights=[spec.coefficient_weights(matrix[k],writers) for k in ('own','fake')]
 owners=np.asarray(writers);indices=[np.flatnonzero(owners==w) for w in levels]
 rng=np.random.default_rng(config['permutation_seed'])
 if checkpoint:checkpoint('bootstrap-complete')
 def permute(run):
  changed=y.copy()
  for ix in indices:changed[ix]=rng.permutation(changed[ix])
  return [float(w@changed) for w in weights] if run else None
 permutations=spec.draw_series(Path(output)/'permutations' if output else None,binding+'-permutation',config['permutations'],permute,
  on_tenth=(lambda:checkpoint('permutation-tenth')) if checkpoint else None,
  yield_requested=(lambda:checkpoint('permutation-boundary')) if checkpoint else None)
 if permutations is None:return dict(status='yielded',phase='permutations')
 permutations=np.asarray(permutations,float)
 return dict(primary=interval(gap,difference),paired_own=interval(points[0],samples[:,0]),paired_fake=interval(points[1],samples[:,1]),
  controls=dict(paired_gap=reference(gap,permutations[:,0]-permutations[:,1]),own=reference(points[0],permutations[:,0]),fake=reference(points[1],permutations[:,1])),
  bootstrap_draws=config['bootstrap_draws'],permutations=config['permutations'],paired_writers=len(levels),paired_occurrences=len(y),
  bootstrap_unit='real writers; both arms use identical resampled writer indices')

def secondary(matrix,evidence):
 flags=[evidence['revision_flags'][i] for i in evidence['paired_primary_indices']];out={}
 for arm in ('own','fake'):
  out[arm]={}
  for category,label in ((1,'local'),(0,'pervasive')):
   selected=[f for f,x in zip(flags,matrix[arm]) if x[0]==category]
   out[arm][label]=dict(occurrences=len(selected),counts={k:sum(f[k] for f in selected) for k in LABELS},rates={k:sum(f[k] for f in selected)/len(selected) if selected else None for k in LABELS})
 return dict(paired_population=out,scope='descriptive occurrence proportions on the same paired population; categories can overlap within an occurrence; no psychological burst or attention identification')

def work(output,inputs,config,operation):
 output=Path(output);output.mkdir(parents=True,exist_ok=True);start=time.monotonic();timing=output/'ACTIVE_TIME.json'
 prior=read(timing)['seconds'] if timing.exists() else 0.
 permutation_start=None
 def checkpoint(phase):
  nonlocal permutation_start
  seconds=prior+time.monotonic()-start
  if seconds>3600:raise TimeoutError('paired execution/replay ceiling')
  if phase=='bootstrap-complete':permutation_start=seconds
  if operation=='execute' and phase=='permutation-tenth' and not (output/'FIRST_TENTH.json').exists():
   projected=2*(permutation_start+10*(seconds-permutation_start))
   write_equal(output/'FIRST_TENTH.json',dict(active_seconds=seconds,projected_cpu_seconds=projected,forecast_cpu_seconds=600,projection_exceeds_twice_forecast=projected>1200,
    method='full source and bootstrap observed plus first tenth of 200 permutations extrapolated; doubled for fresh full replay'))
  if operation=='execute':atomic(output/'PROGRESS.json',dict(phase=phase,active_seconds=seconds))
  return operation=='execute' and (output/'YIELD_REQUEST.json').exists()
 try:
  checkpoint('starting')
  if operation=='verify':check_binding(output,inputs,config)
  matrix,evidence=source(inputs,config);checkpoint('prepared')
  saved=dict(matrix=matrix,evidence=evidence)
  if operation=='execute':gzip_equal(output/'DESIGN.json.gz',saved)
  elif gzread(output/'DESIGN.json.gz')!=saved:raise ValueError('paired design or revision source changed')
  result=compute(matrix,config,output if operation=='execute' else None,checkpoint)
  if result.get('status')=='yielded':return result
  result.update(card=config['card'],full_original_effect=evidence['full_original_effect'],original_occurrences=evidence['original_occurrences'],excluded_occurrences=evidence['excluded_occurrences'],secondary=secondary(matrix,evidence),descriptive=True,scientific_admission=False)
  checkpoint('complete')
  if operation=='execute':
   write_equal(output/'PRIMARY.json',result)
   artifacts=['DESIGN.json.gz','PRIMARY.json']+[p.relative_to(output).as_posix() for p in output.rglob('block-*')]
   if (output/'TIMING_BINDINGS.json').exists():check_binding(output,inputs,config)
   else:bind(output,inputs,config,artifacts)
   return result
  if read(output/'PRIMARY.json')!=result:raise ValueError('fresh complete paired calculation differs')
  return dict(verified=True,full_source_and_fit_replay=True,primary=result)
 finally:atomic(timing,dict(seconds=prior+time.monotonic()-start))

def execute(output,inputs,config):return work(output,inputs,config,'execute')
def verify(output,inputs,config):return work(output,inputs,config,'verify')
