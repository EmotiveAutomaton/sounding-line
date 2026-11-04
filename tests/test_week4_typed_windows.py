from runners.drive.cards.week4_typed_windows import produced_words,connected,skeleton_grams,session_windows,classify

def words(n=24):
    return [dict(index=i,ordinal=i*2+1,completed_ordinal=i*2+2,is_word=True,token='the' if i%4==0 else 'x',
        previous_typed_token_index=i-1 if i else None,sentence_start=i==0,length=3,seconds=float(i),revised=False) for i in range(n)]

def intervals(rows,stop=(0,8,16)):
    return [dict(ordinal=w['ordinal'],onset=True,stop=i in stop,fast=.2 if i in stop else .9,interval_seconds=1.) for i,w in enumerate(rows)]

def test_stops_nonoverlap_and_first_interval_exclusion():
    w=words();t=intervals(w,tuple(range(24)));t[0]['interval_seconds']=100
    out,c=session_windows(dict(words=w),t,{'the'})
    assert [r['indices'][0] for r in out]==[0,8,16]
    assert len(out)==3 and abs(out[0]['hesitancy']-.8)<1e-12
    t[1]['interval_seconds']=60.01
    out,c=session_windows(dict(words=w),t,{'the'})
    assert c['window_break']==1 and [r['indices'][0] for r in out]==[8,16]

def test_no_prompt_bridge_or_backwards_production():
    w=words(8);w[4]['previous_typed_token_index']=None
    out,c=session_windows(dict(words=w),intervals(w),{'the'})
    assert not out and c['stop_with_disconnected_window']==1
    w=words(8);lookup={r['index']:r for r in w};w[4]['ordinal']=2
    assert not connected(w[3],w[4],lookup)

def test_punctuation_chain_allowed_and_grammar_not_across_sentences():
    a,b=words(2);punct=dict(index=8,ordinal=2,completed_ordinal=2,is_word=False,previous_typed_token_index=0)
    b['previous_typed_token_index']=8
    assert connected(a,b,{0:a,1:b,8:punct})
    w=words(8);w[4]['sentence_start']=True
    assert len(skeleton_grams(w,{'the'}))==2
    assert not skeleton_grams(w,set())

def test_future_revision_flag_cannot_select_the_window():
    w=words(8);t=intervals(w);before=session_windows(dict(words=w),t,{'the'})
    for r in w:r['revised']=True
    assert before==session_windows(dict(words=w),t,{'the'})
    duplicate=dict(w[0],index=99,completed_ordinal=999,token='later')
    chosen,c=produced_words(w+[duplicate])
    assert chosen[0]['index']==0 and c['repeated_original_onset_versions']==1

def test_terciles_are_writer_specific_and_ties_disjoint():
    s=[dict(writer='a',windows=[dict(hesitancy=x,grams=[['the']]) for x in range(9)]),
       dict(writer='b',windows=[dict(hesitancy=.5,grams=[['the']]) for x in range(9)])]
    support=classify(s)
    assert support['a']['classes']=={'flow':3,'middle':3,'hesitant':3}
    assert support['b']['classes']=={'middle':9}
