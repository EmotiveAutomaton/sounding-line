from types import SimpleNamespace
import pytest
from runners.stage8.reader import logfmt as LF
from runners.stage9.mixed_recipes import candidate


class Tokenizer:
    eos_token='!'
    def __call__(self,text,add_special_tokens):
        return SimpleNamespace(input_ids=([1] if add_special_tokens else [])+[ord(c) for c in text])


def example():
    previous=LF.EARLIER+'\nCORRECT OLD WORK\n'+LF.NOW+'\n'
    source={'key':'source','lineages':['source','old'],'input_ids':[1,2,3],
            'raw_record':{'n_earlier':1,'text':previous+'ORIGINAL CURRENT','domain':'essay'}}
    state={'learner_actions_applied':1,'prefix':previous+'ACTUAL LEARNER HISTORY',
           'targets':[{'target':'TRUE TAIL'},{'target':'ANOTHER TRUE TAIL'}],'actual_state_sha256':'state'}
    return source,{'lineage':'source','domain':'essay','examples':[state]}


def test_only_unchanged_expert_context_and_correct_tails_are_targets():
    source,collected=example();row=candidate(Tokenizer(),source,collected)
    start,end=row['earlier_expert_span']
    assert row['labels'][start:end]==row['input_ids'][start:end]
    assert row['complete_continuations_retained']==2
    for span in row['spans']:
        a,b=span['context'];assert all(v==-100 for v in row['labels'][a:b])
        a,b=span['correct_target'];assert row['labels'][a:b]==row['input_ids'][a:b]
    assert row['lineages']==source['lineages']


def test_absent_or_changed_prior_context_and_impossible_cap_cannot_pass():
    source,collected=example()
    with pytest.raises(ValueError,match='fits'):
        candidate(Tokenizer(),source,collected,maximum_tokens=3)
    collected['examples'][0]['prefix']='OTHER PRIOR'
    with pytest.raises(ValueError,match='earlier-work'):
        candidate(Tokenizer(),source,collected)


def test_four_correct_tails_preserve_masks_and_fixed_expert_budget_on_reentry(tmp_path):
    from runners.stage9.common import freeze,read,file_hash
    from runners.stage9.matching import mixture_keys,replay_row,target_positions
    from runners.stage9.mixed_recipes import build
    pool=[{'key':key,'lineages':[key],'input_ids':[1,2,3,4],
           'raw_record':{'domain':'essay','n_earlier':0,'text':'EXPERT'}} for key in ('a','b')]
    chosen=mixture_keys(pool);expert=[replay_row(s) for s in pool]
    records={key:{'lineage':key,'domain':'essay','examples':[{'learner_actions_applied':1,
        'prefix':'LEARNER HISTORY','targets':[{'target':tail} for tail in ('FIRST','SECOND','THIRD','FOURTH')],
        'actual_state_sha256':'state'}]} for key in chosen}
    budget=sum(len(target_positions(r)) for r in expert)
    rows,matching=build(Tokenizer(),pool,expert,records,budget)
    changed=next(r for r in rows if r['key'] in chosen)
    assert changed['complete_continuations_retained']==4 and matching['dose']=={'0':2}
    assert matching['fixed_expert_rows_byte_preserved'] and sum(len(target_positions(r)) for r in rows)==budget
    for span in changed['spans']:
        a,b=span['context'];assert all(v==-100 for v in changed['labels'][a:b])
    value={'rows':rows,'matching':matching};path=tmp_path/'PACKED.json';freeze(path,value);before=file_hash(path)
    rows2,matching2=build(Tokenizer(),pool,expert,records,budget)
    freeze(path,{'rows':rows2,'matching':matching2})
    assert read(path)==value and file_hash(path)==before
