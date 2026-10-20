from pathlib import Path
import numpy as np
import pytest
from runners.drive.cards import timing_d30_shared as card
from runners.drive.cards.timing_census import read,write,filehash
from runners.drive.cards.timing_p6 import gzread
from tests.test_drive_d30_paired_recovery import fixture as original_fixture,matrix

SMALL=dict(card.CONFIG,bootstrap_draws=100,permutations=200)

def evidence(signal=1):
 m=matrix(signal);return dict(full_x=m['own'],label_shuffled_x=m['fake'],full_y=m['y'],full_writers=m['writers'])

@pytest.mark.parametrize('signal,state',[(1,'positive'),(-1,'negative')])
def test_full_signed_known_answer(signal,state):
 e=evidence(signal);r=card.full_compute(e,SMALL)
 assert r['primary']['state']==state and r['primary']['effect']==pytest.approx(signal,abs=.01)
 assert r['marker_label_control']['effect']==pytest.approx(-signal,abs=.01)

def test_exact_primary_null_and_paired_null():
 e=evidence();e['full_y']=[0.]*len(e['full_y']);r=card.full_compute(e,SMALL)
 assert r['primary']==dict(effect=0.,ci_low=0.,ci_high=0.,state='null',expected_direction=1)
 assert not r['outcome_reference']['bias_flag']
 assert card.compute(matrix(identical=True),SMALL)['primary']['state']=='null'

def test_same_exact_dummy_regression():
 e=evidence();w=np.asarray(e['full_writers']);dummy=np.column_stack([w==i for i in sorted(set(w))])
 direct=np.linalg.lstsq(np.column_stack([e['full_x'],dummy]),e['full_y'],rcond=None)[0][0]
 assert card.full_compute(e,SMALL)['primary']['effect']==pytest.approx(direct,abs=1e-11)

def test_shared_dictionary_keeps_only_named_words_and_punctuation():
 rows=[dict(marker=m) for m in ('word:a','bigram:a b','word:rare','punct:!','punct:$')]
 selected,indices=card.select_shared(rows,dict(words=['a'],punctuation=['!']))
 assert selected==[rows[0],rows[3]] and indices==[0,3]
 with pytest.raises(ValueError):card.select_shared(rows,dict(words=['a','a'],punctuation=[]))
 with pytest.raises(ValueError):card.select_shared(rows,dict(words=['absent'],punctuation=[]))

def test_full_immutable_continuation_and_mutation(tmp_path):
 e=evidence();r=card.full_compute(e,SMALL,tmp_path,lambda _:True);assert r['status']=='yielded'
 first=tmp_path/'bootstrap/block-00000.json';before=first.read_bytes()
 got=card.full_compute(e,SMALL,tmp_path);assert first.read_bytes()==before and got==card.full_compute(e,SMALL)
 first.write_bytes(before+b' ')
 with pytest.raises(ValueError,match='hash'):card.full_compute(e,SMALL,tmp_path)

def fixture(root):
 root=Path(root);inputs=original_fixture(root);rows=gzread(Path(inputs['primary_completion']).parent/'output/D30_INTERMEDIATES.json.gz')['rows']
 d=root/'dictionary';words=sorted({r['token'] for r in rows})
 assert len(words)<=100
 write(d/'output/STYLE_DICTIONARY.json',dict(words=words,punctuation=[]))
 write(d/'COMPLETE.json',dict(status='COMPLETE',fresh_process_verified=True,synthetic_fixture=True,outputs={'output/STYLE_DICTIONARY.json':filehash(d/'output/STYLE_DICTIONARY.json')}))
 return dict(inputs,dictionary_completion=str((d/'COMPLETE.json').resolve()))

def test_source_maps_original_positions_and_preserves_common_rows(tmp_path):
 inputs=fixture(tmp_path);m,e=card.source(inputs,card.CONFIG)
 assert e['shared_rows']==e['unrestricted_rows']
 assert len(e['revision_flags'])==e['original_occurrences']
 assert len(e['full_x'])>len(m['own'])>0
 assert all(a[1:]==b[1:] for a,b in zip(m['own'],m['fake']))
 r=card.secondary(m,e)
 assert sum(v['occurrences'] for v in r['full_primary_population'].values())==len(e['full_y'])

def test_whole_handler_reentry_replay_and_dictionary_change(tmp_path):
 inputs=fixture(tmp_path/'source');out=tmp_path/'out';write(out/'YIELD_REQUEST.json',{})
 assert card.execute(out,inputs,card.CONFIG)['status']=='yielded'
 (out/'YIELD_REQUEST.json').unlink();r=card.execute(out,inputs,card.CONFIG)
 assert card.verify(out,inputs,card.CONFIG)['primary']==r
 assert card.execute(out,inputs,card.CONFIG)==r
 p=Path(inputs['dictionary_completion']).parent/'output/STYLE_DICTIONARY.json';p.write_bytes(p.read_bytes()+b' ')
 with pytest.raises(ValueError,match='dictionary'):card.source(inputs,card.CONFIG)

def test_wrong_configuration_refused():
 with pytest.raises(ValueError):card.validate(dict(card.CONFIG,extension=True))
 with pytest.raises(ValueError):card.validate(dict(card.CONFIG,bootstrap_draws=True))

def native_answers():
 for signal,state in ((1,'positive'),(-1,'negative')):assert card.full_compute(evidence(signal),SMALL)['primary']['state']==state
 e=evidence();e['full_y']=[0.]*len(e['full_y']);assert card.full_compute(e,SMALL)['primary']['effect']==0
 assert card.compute(matrix(identical=True),SMALL)['primary']['effect']==0
 return dict(positive=True,negative=True,exact_primary_null=True,exact_paired_null=True)

def execute(output,inputs,config):
 answers=native_answers();result=card.execute(output,inputs,config);write(Path(output)/'NATIVE_ANSWERS.json',answers);return result

def verify(output,inputs,config):
 assert read(Path(output)/'NATIVE_ANSWERS.json')==native_answers()
 return card.verify(output,inputs,config)
