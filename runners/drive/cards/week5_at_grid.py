"""Prospective AT/LA configuration grid; declarations are not launch authority."""
from .week5_at_scoring import MODELS,ENGINE_MODELS


def grid(genres):
    cells=[]
    def add(family,card,module,config,dependency=None):
        cells.append(dict(family=family,card=card,module='runners.drive.cards.'+module,config=config,
                          dependency=dependency,ready_only_after_owner_design_fixture_review=True))
    add('AT','AT1','week5_at_history',dict(draws=2000,k=5,match='genre'))
    cells[-1]['block_execution']=dict(draw_start=0,draw_count=100,total_draws=2000,first_five_percent='global indices 0..99')
    for k in (1,3,20):add('AT','AT1.k'+str(k),'week5_at_history',dict(draws=200,k=k,match='genre'))
    for match in ('random','same_prompt'):add('AT','AT1.'+match,'week5_at_history',dict(draws=200,match=match))
    for outcome in ('hesitancy','stop'):add('AT','AT1.'+outcome,'week5_at_history',dict(draws=200,outcome=outcome))
    for genre in genres:add('AT','AT1.genre.'+genre,'week5_at_history',dict(draws=200,genre=genre))
    add('AT','AT1.prompt','week5_at_history',dict(draws=200,prompt_included=True))
    for representation in ('vocabulary','bigram'):
        add('AT','AT1.p.'+representation,'week5_at_history',dict(draws=200,representation=representation),'AT1 personal route')
    add('AT','AT1.s','week5_at_shared',dict(draws=200),'AT1 shared route')
    for context in ('final','at_typing'):
        for length in (64,256,1024):
            add('AT',f'AT2.{context}.{length}','week5_at_analysis',dict(card='AT2',draws=2000 if (context,length)==('final',1024) else 200,
                models=list(MODELS),context=context,context_length=length),'Complete matching ten-reader score bank')
    for genre in genres:add('AT','AT2.genre.'+genre,'week5_at_analysis',dict(card='AT2',draws=200,models=list(MODELS),genre=genre),'Complete final score bank')
    for outcome in ('hesitancy','stop'):add('AT','AT2.'+outcome,'week5_at_analysis',dict(card='AT2',draws=200,models=list(MODELS),outcome=outcome),'Complete final score bank')
    add('AT','AT2.e','week5_at_engine_analysis',dict(card='AT2.e',draws=2000),'Engine pair below selected reader by bar; exact engine exports')
    for card in ('AT3','AT4'):
        add('AT',card,'week5_at_analysis',dict(card=card,draws=2000,model='$AT2.selected_model'),'Admissible primary AT2 selection')
        for genre in genres:add('AT',card+'.genre.'+genre,'week5_at_analysis',dict(card=card,draws=200,model='$AT2.selected_model',genre=genre),'Primary AT2 selection')
    for model in MODELS:add('AT','AT3.reader.'+model,'week5_at_analysis',dict(card='AT3',draws=200,model=model),'Complete model bank')
    for position in ('sentence_start','inside'):add('AT','AT3.'+position,'week5_at_analysis',dict(card='AT3',draws=200,model='$AT2.selected_model',position=position),'Primary AT2 selection')
    add('AT','AT3.residualized','week5_at_analysis',dict(card='AT3',draws=200,model='$AT2.selected_model',residualized=True),'Primary AT2 selection')
    for threshold in (.3,.7):add('AT','AT4.threshold.'+str(threshold),'week5_at_analysis',dict(card='AT4',draws=200,model='$AT2.selected_model',threshold=threshold),'Primary AT2 selection')
    for model in ENGINE_MODELS:add('AT','AT4.reader.'+model,'week5_at_analysis',dict(card='AT4',draws=200,model=model),'Complete engine-reader score bank')
    add('AT','AT4.engine','week5_at_engine_analysis',dict(card='AT4.engine',draws=2000),'Complete exact product exports')
    add('LA','LA1','week5_la',dict(card='LA1',draws=2000),'Primary AT2 selection + complete paired masked bank')
    for left,window in ((1.,1.),(1.,3.),(5.,5.)):
        add('LA',f'LA1.window.{left}.{window}','week5_la_pipeline',dict(card='LA1',left=left,window=window),'Prepared/scored variant then LA1 200 refits')
    for n in (3,10):add('LA','LA1.history.'+str(n),'week5_la_pipeline',dict(card='LA1',history_acts=n),'Re-score paired masked bank then LA1 200 refits')
    for corpus in ('AMI','ICSI'):add('LA','LA1.corpus.'+corpus,'week5_la_pipeline',dict(card='LA1',corpus=corpus),'Complete source then matching score bank')
    for scope in ('own','others'):add('LA','LA1.s.'+scope,'week5_la_pipeline',dict(card='LA1',laugh_scope=scope),'Others texture unconditional; ownership branch if resolution carries')
    add('LA','LA1.i','week5_la_followup',dict(draws=200),'Surprise carries laughter')
    for corpus,background in (('AMI','native_language'),('ICSI','english_variety'),('ICSI','region')):
        add('LA','LA2.'+corpus+'.'+background,'week5_la_pipeline',dict(card='LA2',corpus=corpus,background=background),'Verified LA0 then LA2 2000 primary / 200 texture refits')
    return cells
