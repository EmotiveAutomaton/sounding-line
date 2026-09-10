"""Exact bounded-language compression/distinction operations, standard library only.

DESIGN CHECK: I05/C04/X10. Vafa et al. 2024, Sections 2.3-2.4, definitions
2.4-2.6: https://arxiv.org/html/2406.03689v3 (primary text read).
Compare minimal directed distinguishing suffixes with accepted-language differences,
not merely intersection of two boundary sets. The finite horizon and query cap are
explicit; an exhausted cap raises and cannot claim exact equivalence. This is an
operation adaptation, not reproduction of their trained maps/Othello experiments.
"""
from collections import deque
import math


def validate(graph):
    if set(graph)!={'alphabet','transitions','accepting','initial'}:
        raise ValueError('finite graph requires complete declared schema')
    alphabet=graph['alphabet'];states=graph['transitions']
    if not alphabet or len(alphabet)>128 or len(set(alphabet))!=len(alphabet) or len(states)>4096:
        raise ValueError('finite graph alphabet/state cap invalid')
    if graph['initial'] not in states or not set(graph['accepting'])<=states.keys():
        raise ValueError('unknown initial/accepting state')
    for source,row in states.items():
        if not set(row)<=set(alphabet) or any(target not in states for target in row.values()):
            raise ValueError('transition outside declared graph')
    return graph


def accepts(graph,start,sequence):
    """Unlisted transitions lead to an implicit rejecting sink."""
    state=start
    for token in sequence:
        state=graph['transitions'].get(state,{}).get(token)
        if state is None:return False
    return state in graph['accepting']


def shortest_separator(graph,left,right,maximum_pairs=100000):
    """Product-graph BFS proves equivalence only after exhausting reachable pairs."""
    validate(graph)
    if left not in graph['transitions'] or right not in graph['transitions']:
        raise ValueError('unknown compared graph state')
    pending=deque([(left,right,())]);seen=set();accepting=set(graph['accepting'])
    while pending:
        a,b,path=pending.popleft()
        if (a,b) in seen:continue
        if len(seen)>=maximum_pairs:raise ValueError('product-state budget exhausted; equivalence unknown')
        seen.add((a,b))
        if (a in accepting)!=(b in accepting):
            return {'equivalent':False,'suffix':list(path),'left_accepts':a in accepting,'visited_pairs':len(seen)}
        for token in graph['alphabet']:
            na=graph['transitions'].get(a,{}).get(token)
            nb=graph['transitions'].get(b,{}).get(token)
            if (na,nb) not in seen:pending.append((na,nb,path+(token,)))
    return {'equivalent':True,'suffix':None,'visited_pairs':len(seen)}


def boundary(left,right,alphabet,maximum_length,query_cap=50000):
    """All left-only first separating suffixes up to the declared finite horizon."""
    if not 1<=maximum_length<=16 or not 1<=len(alphabet)<=128 or len(set(alphabet))!=len(alphabet):
        raise ValueError('invalid bounded language dimensions')
    pending=deque([()]);result=[];queries=0
    while pending:
        prefix=pending.popleft()
        for token in alphabet:
            if queries+2>query_cap:raise ValueError('language query budget exhausted; boundary incomplete')
            sequence=prefix+(token,);a=left(sequence);b=right(sequence);queries+=2
            if type(a) is not bool or type(b) is not bool:
                raise ValueError('language acceptance must be an explicit valid Boolean')
            if a and not b:result.append(sequence)
            elif a and b and len(sequence)<maximum_length:pending.append(sequence)
    return {'suffixes':result,'queries':queries,'maximum_length':maximum_length,'exhaustive_within_horizon':True}


def evaluate(true_left,true_right,model_left,model_right,alphabet,maximum_length,query_cap=50000):
    true=boundary(true_left,true_right,alphabet,maximum_length,query_cap)
    model=boundary(model_left,model_right,alphabet,maximum_length,query_cap)
    # Equations 2/3 test the other language's DIFFERENCE, not minimality in both.
    recalled=sum(model_left(s) and not model_right(s) for s in true['suffixes'])
    precise=sum(true_left(s) and not true_right(s) for s in model['suffixes'])
    return {'true_boundary_size':len(true['suffixes']),'model_boundary_size':len(model['suffixes']),
            'recall':recalled/len(true['suffixes']) if true['suffixes'] else None,
            'precision':precise/len(model['suffixes']) if model['suffixes'] else 1.,
            'recalled':recalled,'precise':precise,'maximum_length':maximum_length,
            'boundary_queries':true['queries']+model['queries'],
            'scope':'directed bounded-language comparison; empty true boundary has undefined recall',
            'exhaustive_within_horizon':True}


def threshold_language(predict,history,alphabet,epsilon=.01):
    """Accept iff EVERY successive action exceeds epsilon on the full shared support.

    All component probabilities must be valid; an absent option is an invalid
    query, not a zero/fallback. Caches never combine different initial histories.
    """
    if not 0<epsilon<1:raise ValueError('declared positive acceptance threshold required')
    cache={}
    def accept(sequence):
        for i,token in enumerate(sequence):
            prefix=tuple(history)+tuple(sequence[:i])
            if prefix not in cache:
                p=predict(prefix)
                if (set(p)!=set(alphabet) or any(not math.isfinite(v) or not 0<=v<=1 for v in p.values())
                        or abs(sum(p.values())-1)>1e-8):
                    raise ValueError('incomplete or invalid full-support model prediction')
                cache[prefix]=p
            if cache[prefix][token]<=epsilon:return False
        return True
    return accept
