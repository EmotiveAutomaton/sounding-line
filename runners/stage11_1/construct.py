"""Executed same-visible-endpoint twins for the separate S2 ambiguity branch.

DESIGN CHECK: LESSONS 2-5. NULL: identical visible fields cannot disclose which
executed history occurred. ALTERNATIVE: a neutral insertion record differentiates
model insertion from human typing. Every transformation replays and both tiers
match byte for byte before release; context perturbations remain interventions.
"""
from runners.stage11.replay import replay
from .common import PRIVATE,freeze,digest
from .targets import public,project,units


def delta(source,ops):return dict(eventName='text-insert',eventSource=source,textDelta=dict(ops=ops))


def twins():
    rows=[]
    for template,(before,offer) in enumerate([
        ('The keeper watched the sea.',' A lamp appeared.'),
        ('The workshop opened at dawn.',' A visitor arrived.'),
        ('The report needs a conclusion.',' The result remains uncertain.'),
        ('The path crossed the orchard.',' A gate stood open.')]):
        for version in range(6):
            prefix=before+'\n';suggestion=offer+f' [{version}]';pair=f'twin-{template}-{version}'
            produced=[]
            for selected in (True,False):
                trace=[dict(eventName='system-initialize',currentDoc=prefix),
                    dict(eventName='suggestion-open',currentSuggestions=[dict(index=0,original=suggestion,trimmed=suggestion)])]
                trace += [dict(eventName='suggestion-select',currentSuggestionIndex=0)] if selected else [dict(eventName='suggestion-close')]
                trace.append(delta('api' if selected else 'user',[{'retain':len(units(prefix))-1},{'insert':suggestion}]))
                if version==1:trace.append(delta('user',[{'retain':len(units(prefix))+2},{'delete':1},{'insert':'X'}]))
                elif version==2:trace.append(delta('user',[{'retain':len(units(prefix+suggestion))-1},{'insert':' Then it ended.'}]))
                elif version==3:trace.append(delta('user',[{'insert':'Earlier, '}]))
                elif version==4:trace.append(delta('user',[{'retain':len(units(prefix))-1},{'delete':len(units(suggestion))}]))
                elif version==5:trace.append(delta('user',[{'retain':len(units(prefix))+1},{'insert':' '}]))
                result=replay(trace);e=result['events'][0]
                if not e['usable']:raise ValueError('constructed transformation failed')
                views={v:public(e,v) for v in ('artifact','alternatives')}
                r=dict(key=pair+('-model' if selected else '-human'),pair=pair,writer=f'family-{template}',
                    session=pair,prompt=f'template-{template}',domain='constructed',trace=trace,
                    views=views,target=project(e,trace),exposure='new constructed task; not human confirmation')
                # The cue states source telemetry, never the target handling label.
                neutral=dict(event='text-insert',source=trace[3]['eventSource'],operations=trace[3]['textDelta']['ops'])
                r['observations']=dict(before=prefix,alternatives=[suggestion],insertion=neutral)
                r['cues']=dict(true=neutral,irrelevant={'setting':'The editor window had a gray border.'},
                    misleading=dict(neutral,source='user' if selected else 'api'))
                rows.append(r);produced.append(r)
            if produced[0]['views']!=produced[1]['views']:raise ValueError('twin visible evidence differs')
            if produced[0]['target']==produced[1]['target']:raise ValueError('histories failed to differ')
    return rows


def prepare(root=PRIVATE):
    rows=twins();freeze(root/'S2/CONSTRUCTED.json',rows)
    result=dict(status='PREPARED',pairs=24,episodes=48,construction_families=4,visible_tiers_equal=True,
        digest=digest(rows),new_model_calls=0,scope='constructed ambiguity only; no real-writing prevalence claim',
        interventions=['true source cue','irrelevant setting cue','misleading source cue'],
        next_action='S2 leading-reader and CPU comparisons after S1 viability disposition')
    freeze(root/'S2/PREPARED.json',result);return result


if __name__=='__main__':print(prepare())
