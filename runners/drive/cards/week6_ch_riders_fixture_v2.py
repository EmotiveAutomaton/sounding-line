"""Invented literal choice-menu controls with analytically known held-out gain.

DESIGN CHECK: LESSONS 3-5. All observed choice counts are specified before fitting.
At-bar recency: 54/46 versus count-only50/50 gives KL(.54||.5)=0.003203421...
nats. Null:50/50 gives exact zero. Preference trap:75/25 with count contrast
log3 gives a positive count coefficient without any use effect, zero gain.
These isolated menus qualify the estimator; separate history tests qualify its
field construction. The supplied CH14 in-sample fixture is a reference only.
"""
import math
import zlib
import numpy as np
from . import week6_ch14_math_v2 as model
from . import week6_ch13_math_v1 as fade


def literal_menus(world,players=24,repetitions=1):
    if world not in ('recency_at_bar','null','fixed_preference'):raise ValueError('Unknown literal world')
    x=[];starts=[];selected=[];person=[];train=[];week=[]
    for p in range(players):
        for is_train in (True,False):
            for count_sign in (-1,1):
                for recent_sign in (-1,1):
                    count=math.log(3) if world=='fixed_preference' else count_sign*math.log(2)
                    recent=recent_sign*math.log(27/23)
                    chosen_ones=75 if world=='fixed_preference' else 50 if world=='null' else 46 if recent_sign==1 else 54
                    for repeat in range(repetitions):
                        for index in range(100):
                            start=len(x);starts.append(start)
                            x.extend([[-count/2,-recent/2,-recent/2],[count/2,recent/2,recent/2]])
                            selected.append(start+int(index<chosen_ones));person.append(p);train.append(is_train)
                            week.append(not is_train and repeat==0 and count_sign==1)
    return dict(names=[f'constructed-{p:03}' for p in range(players)],x=np.asarray(x),
        starts=np.asarray(starts),selected=np.asarray(selected),person=np.asarray(person),
        train=np.asarray(train),week=np.asarray(week),census=dict(constructed_choices=len(starts)))


def qualify(check=lambda:None):
    records={}
    target=.54*math.log(.54/.5)+.46*math.log(.46/.5)
    for world,truth in [('recency_at_bar',target),('null',0.),('fixed_preference',0.)]:
        check();prepared=literal_menus(world);sets=model.model_sets(prepared)
        point=model.draw(prepared,sets,np.ones(len(prepared['names'])),False,check)
        if any(v['status']!='complete' for v in point['fits'].values()):raise AssertionError('Constructed fit not certified')
        observed=point['gains']['hours']['point']
        if abs(observed-truth)>1e-7:raise AssertionError('Known held-out gain not recovered')
        if world=='fixed_preference' and point['fits']['count']['beta'][0]<.9:
            raise AssertionError('Standing-preference count trap was not expressed')
        if world=='recency_at_bar' and not observed>.003:raise AssertionError('At-bar fixture did not clear its planted gain')
        records[world]=dict(expected_gain=truth,observed_gain=observed,fits=point['fits'],constructed_only=True)
    return dict(status='constructed_controls_passed',records=records,
                human_admission=False,supplied_CH14_fixture_reproduced=False)


def qualify_ch13_supplied(check=lambda:None):
    """Recreate exactly the supplied CH13 worlds, then feed this handler.

    Does not import or execute the supplied script, which also runs other cards.
    Expected rounded answers were independently supplied before this builder.
    """
    records={}
    for label,chosen,null,expected,truth in [
        ('CH13a',False,False,-.0302,-.0255),
        ('CH13b',True,False,-.0211,-.0251),
        ('CH13null',False,True,-.0008,0.)]:
        check();rng=np.random.default_rng(zlib.crc32(label.encode()));people,games=6000,200
        sensitivity=None if null else np.abs(.03*(1+.5*rng.standard_normal(people)))
        losses=rng.random((people,games))<.5
        waits=rng.lognormal(np.log(6),1.6,(people,games))
        if chosen:waits=np.where(losses,waits*np.exp(-.8*(sensitivity[:,None]-.03)/.015),waits)
        outcomes=.45*rng.standard_normal((people,games))
        if not null:outcomes-=sensitivity[:,None]*np.exp(-waits/15)*losses
        values=[]
        for person in range(people):
            check()
            rows=[dict(analysis=True,previous_score=0. if losses[person,j] else 1.,
                outcome=float(outcomes[person,j]),wait=float(waits[person,j])) for j in range(games)]
            value=fade.player_summary(rows)['contrast']
            if value is not None:values.append(value)
        observed=math.fsum(values)/len(values)
        if abs(observed-expected)>0.000051:raise AssertionError('Supplied CH13 rounded known answer differs')
        if abs(observed-truth)>.006:raise AssertionError('CH13 planted fade not recovered at its declared tolerance')
        records[label]=dict(expected_rounded=expected,observed=observed,planted_reference=truth,
                            tolerance=.006,eligible_players=len(values))
    return dict(status='constructed_controls_passed',card='CH13',records=records,human_admission=False)
