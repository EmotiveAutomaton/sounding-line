"""TR3 matched recurrence statistics with rebuilt permutation histories.

DESIGN CHECK: LESSONS 2-5 and CONTROLS read 2026-10-27. NULL: independent
typing with fixed writer/prompt baselines must not systematically route either
direction. ALTERNATIVE: planted later use/avoidance must route its own direction.
Permutation histories, practice and matches are rebuilt from reassigned typing.
No history, ambiguous chronology, zero characters or absent matches remain
unsupported, never zero effects. Failed calibration stops scientific admission.
"""
from collections import Counter, defaultdict
import math
import numpy as np

METRICS = ('primary', 'dismissed_minus_placebo', 'accepted_minus_dismissed',
           'without_current_reexposure', 'dose')


class Study:
    def __init__(self, census, selection, units):
        self.roster = {r['session']: r for r in census['roster']}
        if len(self.roster) != len(census['roster']) or set(units) != set(self.roster):
            raise ValueError('complete unique source population required')
        self.units = units
        self.features = {r['feature']: (r['family'], r['frequency_decile']) for r in selection['features']}
        if len(self.features) != len(selection['features']):
            raise ValueError('duplicate selection')
        self.targets = sorted(s for s,r in self.roster.items() if r['half']=='test')
        self.writers = sorted({self.roster[s]['writer'] for s in self.targets})
        self.outcomes = {}; by_writer = defaultdict(list); donor = defaultdict(dict)
        for sid, r in self.roster.items():
            u = units[sid]
            if any(u[k] != r[k] for k in ('session','writer','prompt','half')):
                raise ValueError('prepared identity differs')
            if (type(u['typed_characters']) is not int or u['typed_characters'] < 0 or
                    u['typed_characters'] != r['typed_inserted_characters']):
                raise ValueError('character denominator differs')
            if not set(u['human_counts']) <= set(self.features) or not set(u['offers']) <= set(self.features):
                raise ValueError('unselected feature in prepared input')
            if any(type(v) is not int or v <= 0 for v in u['human_counts'].values()):
                raise ValueError('invalid prepared count')
            if not all(type(r[k]) in (int,float) and math.isfinite(r[k]) for k in ('start','end')) or r['end'] < r['start']:
                raise ValueError('invalid source chronology')
            self.outcomes[sid] = (u['human_counts'], u['typed_characters'])
            by_writer[r['writer']].append(sid)
            for f, counts in u['offers'].items():
                if (set(counts)-{'shown','accepted','dismissed','other','unknown'} or
                        any(type(n) is not int or n <= 0 for n in counts.values()) or
                        counts.get('shown',0) != sum(counts.get(k,0) for k in ('accepted','dismissed','other','unknown'))):
                    raise ValueError('inconsistent offer counts')
                key = (r['prompt'], self.features[f], f)
                donor[key][r['writer']] = min(r['end'], donor[key].get(r['writer'], math.inf))
        # Only the first two distinct writers are needed to exclude a recipient.
        gallery = defaultdict(list)
        for (prompt, bucket, feature), times in donor.items():
            gallery[(prompt,bucket)].append((feature, sorted((t,w) for w,t in times.items())[:2]))
        self.contexts = {}
        for sid in self.targets:
            r = self.roster[sid]; group = by_writer[r['writer']]
            prior = sorted(s for s in group if self.roster[s]['end'] < r['start'])
            overlaps = sorted(s for s in group if s != sid and
                max(r['start'],self.roster[s]['start']) <= min(r['end'],self.roster[s]['end']))
            if prior != sorted(r['strict_prior_sessions']) or overlaps != sorted(r['overlapping_or_touching_sessions']):
                raise ValueError('strict history differs from census')
            seen = defaultdict(Counter); prompts = defaultdict(set)
            for earlier in prior:
                for f,c in units[earlier]['offers'].items():
                    seen[f].update(c); prompts[f].add(self.roster[earlier]['prompt'])
            kinds = {f:('accepted' if c.get('accepted',0) and not c.get('dismissed',0) else
                         'dismissed' if c.get('dismissed',0) and not c.get('accepted',0) else
                         'mixed' if c.get('accepted',0) and c.get('dismissed',0) else 'other')
                     for f,c in seen.items()}
            possible = {}; accepted_matches = {}
            for f in sorted(seen):
                matches = set()
                for prompt in prompts[f]:
                    for candidate, dates in gallery.get((prompt,self.features[f]), []):
                        if candidate in seen:
                            continue
                        if any(w != r['writer'] and t < r['start'] for t,w in dates):
                            matches.add(candidate)
                possible[f] = tuple(sorted(matches))
                if kinds[f]=='accepted':
                    accepted_matches[f] = tuple(sorted(g for g in seen if kinds[g]=='dismissed' and
                        self.features[f]==self.features[g] and not prompts[f].isdisjoint(prompts[g])))
            self.contexts[sid] = dict(prior=prior,overlaps=overlaps,seen=dict(seen),kinds=kinds,
                possible=possible,accepted_matches=accepted_matches)
        self.blocks = [sorted(g) for g in self._blocks().values()]

    def _blocks(self):
        blocks = defaultdict(list)
        for sid in self.targets:
            r = self.roster[sid]; blocks[(r['writer'],r['prompt'])].append(sid)
        return blocks

    def evaluate(self, outcomes=None, details=False):
        outcomes = self.outcomes if outcomes is None else outcomes
        if set(outcomes) != set(self.outcomes):
            raise ValueError('outcome reassignment population differs')
        sessions = []; grouped = {m:defaultdict(list) for m in METRICS}; exclusions = Counter()
        for sid in self.targets:
            r = self.roster[sid]; c = self.contexts[sid]; current, denominator = outcomes[sid]
            # Both eligibility and placebo/accepted matches depend on the
            # reassigned earlier typing, and are rebuilt for every reference.
            earlier_typed = set().union(*(outcomes[s][0].keys() for s in c['prior']))
            practice = sum(outcomes[s][1] for s in c['prior'])
            reason = ('ambiguous-chronology' if c['overlaps'] else 'no-prior-session' if not c['prior'] else
                      'zero-typed-characters' if denominator==0 else None)
            values = {m:None for m in METRICS}; accepted = []; paired = []; no_reoffer = []; dismissed = []; doses = []
            eligible = sorted(set(c['seen'])-earlier_typed); match_counts = {}
            if reason is None:
                scale = 10000/denominator
                for f in eligible:
                    matches = [g for g in c['possible'][f] if g not in earlier_typed]
                    match_counts[f] = len(matches)
                    if matches:
                        difference = scale*(current.get(f,0)-sum(current.get(g,0) for g in matches)/len(matches))
                        paired.append(difference); doses.append(math.log1p(c['seen'][f]['shown']))
                        if c['kinds'][f]=='dismissed':
                            dismissed.append(difference)
                        if f not in self.units[sid]['offers']:
                            no_reoffer.append(difference)
                    if c['kinds'][f]=='accepted':
                        others = [g for g in c['accepted_matches'][f] if g not in earlier_typed]
                        if others:
                            accepted.append(scale*(current.get(f,0)-sum(current.get(g,0) for g in others)/len(others)))
                for metric,data in [('primary',paired),('dismissed_minus_placebo',dismissed),
                                    ('accepted_minus_dismissed',accepted),('without_current_reexposure',no_reoffer)]:
                    if data:
                        values[metric] = (float(np.mean(data)),1.0)
                if len(doses)>1:
                    x = np.asarray(doses)-np.mean(doses); xx = float(np.mean(x*x))
                    if xx > 1e-14:
                        values['dose'] = (float(np.mean(x*np.asarray(paired))),xx)
                if not eligible:
                    reason='no-eligible-feature'
                elif not paired:
                    reason='no-placebo-match'
            if reason:
                exclusions[reason] += 1
            for metric,value in values.items():
                if value is not None:
                    grouped[metric][r['writer']].append(value)
            if details:
                sessions.append(dict(session=sid,writer=r['writer'],prompt=r['prompt'],
                    session_index=len(c['prior']),practice_characters=practice,typed_characters=denominator,
                    eligibility=len(eligible),exclusion=reason,matches=match_counts,
                    exposure_kinds=dict(Counter(c['kinds'][f] for f in eligible)),values=values))
        writer_values = {}; estimates = {}; support = {}
        for metric, groups in grouped.items():
            writer_values[metric] = {w:tuple(map(float,np.mean(v,axis=0))) for w,v in sorted(groups.items())}
            support[metric] = dict(writers=len(groups),sessions=sum(len(v) for v in groups.values()))
            estimates[metric] = ratio(list(writer_values[metric].values()))
        return dict(estimates=estimates,writer_values=writer_values,support=support,
                    exclusions=dict(exclusions),sessions=sessions)

    def permute(self, rng):
        outcomes = dict(self.outcomes)
        for block in self.blocks:
            for target,source in zip(block,rng.permutation(block)):
                outcomes[target] = self.outcomes[source]
        return outcomes


def ratio(values):
    if not values:
        return None
    numer,denom = np.mean(values,axis=0)
    return float(numer/denom) if denom > 0 else None


def intervals(real, writers, seed=20261026, draws=2000):
    rng=np.random.default_rng(seed); samples={m:[] for m in METRICS}
    for indices in rng.integers(0,len(writers),size=(draws,len(writers))) if writers else []:
        for metric in METRICS:
            bank=real['writer_values'][metric]
            samples[metric].append(ratio([bank[writers[i]] for i in indices if writers[i] in bank]))
    result={}
    for metric,values in samples.items():
        valid=[v for v in values if v is not None]
        result[metric]=dict(draws=draws,defined=len(valid),interval=(list(map(float,np.quantile(valid,[.025,.975])))
            if len(valid)==draws and real['support'][metric]['writers']>=2 else None))
    return result


def describe(study, permutations=200, bootstraps=2000, seed=20261026):
    real=study.evaluate(details=True); ci=intervals(real,study.writers,seed,bootstraps)
    rng=np.random.default_rng(seed); references=[]
    for i in range(permutations):
        shuffled=study.evaluate(study.permute(rng))
        references.append(dict(index=i,estimates=shuffled['estimates'],support=shuffled['support'],exclusions=shuffled['exclusions']))
    metrics={}
    for metric in METRICS:
        observed=real['estimates'][metric]; bank=[r['estimates'][metric] for r in references]
        defined=[v for v in bank if v is not None]
        varying=bool(defined) and max(defined)-min(defined)>1e-12
        supported=len(defined)==permutations and varying and observed is not None
        pplus=(1+sum(v>=observed for v in defined))/(permutations+1) if supported else None
        pminus=(1+sum(v<=observed for v in defined))/(permutations+1) if supported else None
        band=ci[metric]['interval']; direction=('positive' if band and band[0]>0 else 'negative' if band and band[1]<0 else 'not-detected' if band else 'unsupported')
        route=(direction if supported and ((direction=='positive' and pplus<.05) or (direction=='negative' and pminus<.05)) else
               'not-detected' if direction=='not-detected' else 'unsupported' if observed is None else 'descriptive-only')
        metrics[metric]=dict(estimate=observed,interval=band,support=real['support'][metric],bootstrap=ci[metric],
            reference_defined=len(defined),reference_varying=varying,reference_supported=supported,
            reference_mean=float(np.mean(defined)) if defined else None,
            reference_band=list(map(float,np.quantile(defined,[.025,.975]))) if defined else None,
            p_positive=pplus,p_negative=pminus,direction=direction,route=route)
    return dict(metrics=metrics,real=real,references=references,seed=seed,permutations=permutations,
                bootstrap_draws=bootstraps,reference_histories_rebuilt=True,
                scope='Descriptive conditional-gallery matched recurrence; not causal capture or automaticity')


def world(seed, effect, writers=20, sessions=4):
    """Independent future typing under null; known later use/avoidance otherwise."""
    if effect not in (-1,0,1):
        raise ValueError('unknown planted direction')
    rng=np.random.default_rng(seed); names=[f'w1:feature-{w}-{k}' for w in range(writers) for k in range(sessions)]
    selection=dict(features=[dict(feature=f,family='w1',frequency_decile=5) for f in names]); rows=[]; units={}
    for w in range(writers):
        prior=[]; typed=set(); prior_offers=set(); prompt='p'+str(w%2)
        for k in range(sessions):
            sid=f'{w}:{k}'; writer=f'writer-{w}'; denominator=5000+200*w+100*(w%2)
            counts=dict(zip(names,map(int,rng.poisson(.3+.02*(w%5)+.05*(w%2),len(names)))))
            for f in prior_offers-typed:
                if effect==1:counts[f]+=4
                elif effect==-1:counts[f]=0
            counts={f:n for f,n in counts.items() if n}
            offer=names[w*sessions+k]; kind='accepted' if k%2==0 else 'dismissed'
            row=dict(session=sid,writer=writer,prompt=prompt,half='test',start=k*100,end=k*100+10,
                strict_prior_sessions=list(prior),overlapping_or_touching_sessions=[],typed_inserted_characters=denominator)
            rows.append(row);units[sid]=dict(session=sid,writer=writer,prompt=prompt,half='test',
                typed_characters=denominator,human_counts=counts,offers={offer:dict(shown=1,**{kind:1})})
            prior.append(sid);typed.update(counts);prior_offers.add(offer)
    return dict(census=dict(roster=rows),selection=selection,units=units)
