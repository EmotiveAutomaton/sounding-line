"""Executed four-action makers, public histories, independent evaluator.

DESIGN CHECK: LESSONS 3–5. NULL: uninformative history leaves competing policies;
ALTERNATIVE: discriminating histories update policy weights and future choices.
Known-answer gates compare enumeration with a separate direct implementation.
No hidden target enters public projection. Duplicate renderings cluster together.
"""
from __future__ import annotations
import itertools
import math
import random
from pathlib import Path
from .common import digest, freeze, read

POLICIES = list(itertools.product(range(2), repeat=2))  # preference, learned skill
FAMILIES = {'train': ['switch', 'bypass'], 'dev':['interlock'], 'test':['dual']}
RENDERINGS = {'train':'log', 'dev':'narrative', 'test':'cards'}
LETTERS = 'ABCD'

def tool_effect(family, tools):
    a,b = tools
    return {'switch':a, 'bypass':1-b, 'interlock':a*b, 'dual':int(a!=b)}[family]

def distribution(preference, skill, goal, belief, family, tools):
    """Maker executes the rule with a fixed 10% uniform lapse distribution."""
    row = goal ^ belief
    column = preference ^ (skill & tool_effect(family,tools))
    probs = [.025]*4
    probs[2*row+column] += .9
    return probs

def reference(preference, skill, goal, belief, family, tools):
    enabled = {'switch': bool(tools[0]), 'bypass': not tools[1],
               'interlock': all(tools), 'dual':tools[0]!=tools[1]}[family]
    location = goal if belief == 0 else 1-goal
    style = 1-preference if (skill and enabled) else preference
    winner = {(0,0):0,(0,1):1,(1,0):2,(1,1):3}[(location,style)]
    return [.925 if i==winner else .025 for i in range(4)]

def observe(goal, belief, family, tools, reader_belief=None):
    return dict(requested_item=['red','blue'][goal],
                last_notice_seen_by_maker=['red above blue','blue above red'][belief],
                tools=list(tools), world_family=family,
                reader_only_notice=None if reader_belief is None else ['red above blue','blue above red'][reader_belief])

def decode(obs):
    # Explicit observations are permitted evidence, not private state labels.
    return (['red','blue'].index(obs['requested_item']),
            ['red above blue','blue above red'].index(obs['last_notice_seen_by_maker']))

def enumerate_predict(history, obs, prior=None):
    weights = [1/4]*4 if prior is None else list(prior)
    versions=[]
    for event in history:
        g,b=decode(event['observation'])
        likelihood=[distribution(p,k,g,b,event['observation']['world_family'],event['observation']['tools'])[event['action']] for p,k in POLICIES]
        evidence=sum(w*l for w,l in zip(weights,likelihood))
        new=[w*l/evidence for w,l in zip(weights,likelihood)]
        versions.append(dict(observation_sha256=digest(event), before=weights, after=new,
                             surprise=-math.log(evidence), mismatch=evidence<.04))
        weights=new
    g,b=decode(obs)
    options=[distribution(p,k,g,b,obs['world_family'],obs['tools']) for p,k in POLICIES]
    probs=[sum(w*v[a] for w,v in zip(weights,options)) for a in range(4)]
    latent={name:[sum(w for w,pk in zip(weights,POLICIES) if pk[j]==v) for v in range(2)]
            for j,name in enumerate(['preference','skill'])}
    return dict(probabilities=probs, weights=weights, latent=latent, updates=versions)

def make_unit(split,index,seed=112):
    rng=random.Random((seed+{'train':10000,'dev':20000,'test':30000}[split])*1000+index)
    family=FAMILIES[split][index%len(FAMILIES[split])]
    pref,skill = POLICIES[index%4]
    history=[]
    for t in range(12):
        goal=rng.randrange(2); belief=rng.randrange(2); tools=[rng.randrange(2),rng.randrange(2)]
        obs=observe(goal,belief,family,tools)
        probs=distribution(pref,skill,goal,belief,family,tools)
        action=rng.choices(range(4),weights=probs)[0]
        history.append(dict(sequence=t, observation=obs, action=action))
    initial_goal=rng.randrange(2); initial_belief=rng.randrange(2)
    # Four probes share a maker/world cluster. Goal and belief changes are distinct.
    query_states=[(initial_goal,initial_belief,[0,1]),
                  (1-initial_goal,initial_belief,[0,1]),
                  (1-initial_goal,1-initial_belief,[0,1]),
                  (1-initial_goal,1-initial_belief,[1,1])]
    public=[]; truth=[]
    for t,(goal,belief,tools) in enumerate(query_states):
        obs=observe(goal,belief,family,tools,reader_belief=1-belief if t%2 else belief)
        public.append(dict(encounter=t, observation=obs))
        probs=distribution(pref,skill,goal,belief,family,tools)
        truth.append(dict(encounter=t, goal=goal,belief=belief,preference=pref,skill=skill,
                          probabilities=probs, action=rng.choices(range(4),weights=probs)[0]))
    content=dict(history=history,queries=public)
    cluster=digest(content)
    row=dict(unit=f'{split}-{index:04d}',split=split,cluster=cluster,maker=f'{split}-maker-{index:04d}',
             rendering=RENDERINGS[split],world_family=family, **content)
    return row,dict(unit=row['unit'],cluster=cluster,queries=truth)

def prepare(root, counts=None):
    root=Path(root); counts=counts or dict(train=96,dev=64,test=128)
    inventory={}; clusters=set()
    for split,n in counts.items():
        pairs=[make_unit(split,i) for i in range(n)]
        public=[p for p,t in pairs]; truth=[t for p,t in pairs]
        for row in public:
            if row['cluster'] in clusters: raise ValueError('duplicate construction')
            clusters.add(row['cluster'])
        freeze(root/f'{split}-public.json',public)
        freeze(root/f'{split}-evaluator.json',truth)
        inventory[split]=dict(n=n,public_sha256=digest(public),evaluator_sha256=digest(truth),
                              families=FAMILIES[split],rendering=RENDERINGS[split])
    return freeze(root/'FIXTURE.json',dict(splits=inventory, policy='four-action switchboard v1',
        substrate='constructed; exact executed maker, no human claims',
        independent_unit='unique maker/world history; four probes nested',
        split_limit='policy primitives shared across splits; distinct world mechanics and rendering grammar',
        lapse=.10, candidates=POLICIES))

def rules(family):
    enabling={'switch':'first tool is on','bypass':'second tool is off',
              'interlock':'both tools are on','dual':'exactly one tool is on'}[family]
    return ('Four choices: A=upper left; B=upper right; C=lower left; D=lower right. '
            'The maker chooses the row containing the requested item according to the LAST notice the maker saw. '
            'A later notice seen only by the reader does not change the maker\'s information. '
            'The maker normally uses a preferred column, left or right. A trained maker reverses that column '
            f'when the routing device is enabled. Here it is enabled when {enabling}. '
            'An untrained maker never reverses. Training and preferred column persist across requests. '
            'There is a 10% chance of a random choice; predict the most likely choice. ')

def render_observation(obs, rendering='log'):
    a,b=obs['tools']; tools=f'first tool {"on" if a else "off"}; second tool {"on" if b else "off"}'
    notice=obs['last_notice_seen_by_maker']; goal=obs['requested_item']
    private='' if obs['reader_only_notice'] is None else f' Reader alone later sees: {obs["reader_only_notice"]}. Maker absent.'
    if rendering=='narrative':
        return f'The maker read "{notice}" and was asked for the {goal} item. Equipment: {tools}.'+private
    if rendering=='cards':
        return f'Request card: {goal}. Equipment card: {tools}. Witnessed maker notice: {notice}.'+private
    return f'Goal request={goal}; observed notice="{notice}"; {tools}.'+private

def prompt(public, encounter, arm='raw_history', explicit=None, question='action'):
    obs=public['queries'][encounter]['observation']
    parts=[rules(obs['world_family'])]
    if arm!='no_history':
        history=public['history'][-12:]
        parts += [render_observation(e['observation'], public['rendering'])+f' Chosen {LETTERS[e["action"]]}.' for e in history]
    if explicit is not None:
        p,k=explicit
        parts.append(f'Current maker facts: preferred column is {"left" if p==0 else "right"}; maker is {"trained" if k else "untrained"}.')
    parts.append('Current case: '+render_observation(obs,public['rendering']))
    asks={'action':'Which choice will the maker most likely take? Answer only A, B, C, or D.',
          'belief':'According to the last notice the maker saw, where is red? A=upper; B=lower. Answer only A or B.',
          'goal':'Which item is requested now? A=red; B=blue. Answer only A or B.',
          'skill':'Is this maker trained? A=untrained; B=trained. Answer only A or B.',
          'preference':'What is the usual preferred column? A=left; B=right. Answer only A or B.'}
    parts.append(asks[question])
    return '\n'.join(parts)
