"""Training-only exported B-roll word/POS preferences with equal person mass.

DESIGN CHECK: H03/X01/X03/X06; LESSONS 2--5. NULL: equal selections do not
create a personal preference, and an unsupported/missing outcome refuses.
ALTERNATIVE: learned commission and word preferences can defeat personal context.
Canonical people are weighted equally, without treating words as new people.
"""
from collections import Counter
from .broll_reader import GOALS,TAGS,stimulus,validate_model,digest


def fit(rows):
    if not rows or len({r['key'] for r in rows})!=len(rows):raise ValueError('unique nonempty fitting records required')
    if len({(r['person'],digest(r['stimulus'])) for r in rows})!=len(rows):raise ValueError('a canonical participant cannot see one script twice')
    opportunities=Counter()
    for row in rows:
        words=stimulus(row['stimulus']);ys=row['labels']
        if row['goal'] not in GOALS or len(ys)!=len(words) or any(type(y) is not int or y not in (0,1) for y in ys):
            raise ValueError('invalid canonical fitting commission or target')
        opportunities[row['person']]+=len(words)
    average=sum(opportunities.values())/len(opportunities)
    model={'version':'broll-selection-rivals-v1','pos':{g:{tag:[0.,0.] for tag in TAGS} for g in GOALS},
        'words':{g:{} for g in GOALS},'global':{g:[0.,0.] for g in GOALS}}
    for row in rows:
        weight=average/opportunities[row['person']];goal=row['goal'];source=row['stimulus']
        for word,y in zip(source['support'],row['labels']):
            for value in (model['global'][goal],model['pos'][goal][source['pos'][word]],model['words'][goal].setdefault(word,[0.,0.])):
                value[0]+=weight*y;value[1]+=weight
    validate_model(model);return model
