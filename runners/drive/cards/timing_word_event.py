"""Bounded word-event validity witnesses; not an admitted GPT-2 scorer.

READ: Pimentel & Meister 2024, arxiv:2406.14561v1, sections4.1-4.3,
Theorem2/equation25 and section5.4. Exact support is an explicit assumption;
non-exact token models require marginalization over alternative paths.

DESIGN CHECK: LESSONS3-5. A finite normalized token tree independently
enumerates word events. Both boundary masses must appear; alternate spellings
and token paths must aggregate under the cache's event map. Token overlap or a
canonical spelling alone must fail this witness. No corpus rows are dropped,
contexts changed, probability floors introduced, or model calls performed.
"""
from __future__ import annotations

from collections import defaultdict
import math


def checked_distribution(value):
    if not value or any(not math.isfinite(p) or p<0 for p in value.values()) or not math.isclose(sum(value.values()),1.,abs_tol=1e-12):
        raise ValueError('invalid next-token distribution')
    return value


def boundary_probability(token_probabilities,before_mass,after_mass):
    """Equation25 path contribution, conditional on the declared start set."""
    probabilities=list(token_probabilities)
    if not probabilities or not all(math.isfinite(x) and 0<=x<=1 for x in probabilities+[before_mass,after_mass]) or before_mass<=0:
        raise ValueError('invalid boundary probability')
    value=math.prod(probabilities)*after_mass/before_mass
    if value>1+1e-12:raise ValueError('non-normalized path contribution')
    return value


def enumerate_events(tree,pieces,start_tokens,boundary_tokens,eos,normalizer=lambda x:x,max_depth=12):
    """Exact finite autoregressive path sum with explicit start/boundary sets.

    `pieces` strips the toy start marker. EOS is a separate empty event. The
    caller supplies a complete finite tree; absence is refusal, not a floor.
    Changing tokenizer/start semantics requires a different validated mapping.
    """
    first=checked_distribution(tree[()]); start=set(start_tokens)|{eos};boundary=set(boundary_tokens)|{eos}
    denominator=sum(p for token,p in first.items() if token in start)
    if denominator<=0:raise ValueError('no start-event probability')
    events=defaultdict(float);paths=[]
    if first.get(eos,0):events['<EOS>']+=first[eos]/denominator

    def visit(path,probability,text,probabilities):
        if len(path)>max_depth:raise ValueError('finite witness depth exceeded')
        if path not in tree:raise ValueError('incomplete finite event tree')
        next_tokens=checked_distribution(tree[path])
        end_mass=sum(p for t,p in next_tokens.items() if t in boundary)
        if end_mass:
            value=probability*end_mass/denominator
            event=normalizer(text)
            if not event:raise ValueError('empty non-EOS word event')
            events[event]+=value
            paths.append(dict(tokens=list(path),surface=text,event=event,probability=value,
                token_probabilities=probabilities,before_mass=denominator,after_mass=end_mass))
        for token,p in sorted(next_tokens.items()):
            if p and token not in boundary:
                if token not in pieces:raise ValueError('token lacks exact spelling')
                visit(path+(token,),probability*p,text+pieces[token],probabilities+[p])
    for token,p in sorted(first.items()):
        if token!=eos and token in start and p:
            visit((token,),p,pieces[token],[p])
    if not math.isclose(sum(events.values()),1.,abs_tol=1e-12):raise ValueError('event mapping loses probability mass')
    return dict(events=dict(sorted(events.items())),paths=paths,start_mass=denominator,total=sum(events.values()))


def finite_witness():
    # 'a' can arise as [Ba] OR [Bempty,a]; 'A' shares its casefold event.
    # No tree history is merged; all six terminal word paths are enumerated.
    pieces={'Ba':'a','BA':'A','Bb':'b','Bempty':'','a':'a','x':'x'}
    starts={'Ba','BA','Bb','Bempty'};eos='EOS'
    tree={():{'Ba':.15,'BA':.15,'Bb':.2,'Bempty':.1,'x':.3,'EOS':.1},
        ('Ba',):{'EOS':.8,'x':.2},('Ba','x'):{'EOS':1.},
        ('BA',):{'EOS':.8,'x':.2},('BA','x'):{'EOS':1.},
        ('Bb',):{'EOS':1.},('Bempty',):{'a':1.},('Bempty','a'):{'EOS':1.}}
    surface=enumerate_events(tree,pieces,starts,starts,eos)
    folded=enumerate_events(tree,pieces,starts,starts,eos,str.casefold)
    ratios=[boundary_probability(p['token_probabilities'],p['before_mass'],p['after_mass']) for p in surface['paths']]
    if any(not math.isclose(a,p['probability'],abs_tol=1e-12) for a,p in zip(ratios,surface['paths'])):
        raise ValueError('ratio disagrees with independent path sum')
    return dict(surface=surface,casefold=folded,
        trailing_only_total=surface['start_mass'],
        canonical_lowercase_only=next(p['probability'] for p in surface['paths'] if p['tokens']==['Ba']),
        actual_casefold_a=folded['events']['a'],
        native_gpt2_admitted=False,
        limitation='Finite witness validates algebra and exposes event mismatch; it neither establishes native tokenizer coverage nor measures corpus marginalization cost.')
