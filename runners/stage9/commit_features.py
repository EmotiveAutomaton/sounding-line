"""Pure diff/candidate reader; complete declared surface rivals and no maker IDs.

DESIGN CHECK: H06/X02/X03/X05/X06; LESSONS 2--5. NULL: identical candidate
features have equal probability; copied descriptions and filenames remain rivals.
ALTERNATIVE: learned changed-code correspondence improves a new repository's
fixed menu. Every public candidate is scored under one rule. Unknown/private
fields, incomplete diffs, repeated descriptions and nonfinite parameters refuse.
No source loader, fitting library, path access or repository identifier is used.
Parser/features retain the inspected Stage9 baseline's definitions.
"""
import math,re
HUNK=re.compile(r'^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@(?:.*)$')


def distribution(values):
    if set(values)!={'0','1','2','3'} or any(type(v) not in (int,float) or not math.isfinite(v) or v<0 for v in values.values()):
        raise ValueError('invalid complete description distribution')
    if abs(math.fsum(values.values())-1)>1e-10:raise ValueError('description forecast not normalized')
    return values


def parse_diff(text):
    """Data-only parser. Never interprets paths as local paths or executes code."""
    if not isinstance(text,str) or not text.startswith('diff --git '):raise ValueError('not unified git diff')
    old=new=0;active=False;hunks=[];paths=[];added=[];removed=[];context=[]
    for line in text.splitlines():
        match=HUNK.match(line)
        if match:
            if old or new:raise ValueError('incomplete preceding hunk')
            old=int(match.group(2) or 1);new=int(match.group(4) or 1);active=True
            hunks.append({'old_start':int(match.group(1)),'old_count':old,'new_start':int(match.group(3)),'new_count':new})
            continue
        if active and (old or new):
            if line.startswith('\\ No newline at end of file'):continue
            if not line or line[0] not in ' +-':raise ValueError('invalid hunk body')
            if line[0] in ' -':old-=1
            if line[0] in ' +':new-=1
            if min(old,new)<0:raise ValueError('hunk exceeds declared range')
            {'+':added,'-':removed,' ':context}[line[0]].append(line[1:]);continue
        if line.startswith('\\ No newline at end of file'):continue
        if line.startswith(('--- ','+++ ')):paths.append(line[4:]);continue
        if line.startswith(('diff --git ','index ','new file mode ','deleted file mode ',
                            'old mode ','new mode ','similarity index ','rename from ','rename to ',
                            'dissimilarity index ','copy from ','copy to ')):continue
        if line.startswith(('Binary files ','GIT binary patch')):raise ValueError('binary change unsupported')
        if line:raise ValueError('unrecognized diff record')
    if old or new:raise ValueError('incomplete final hunk')
    if not hunks:raise ValueError('no textual hunk')
    return {'hunks':hunks,'paths':paths,'added':added,'removed':removed,'context':context}


def words(text):
    text=re.sub(r'([a-z])([A-Z])',r'\1 \2',text)
    return re.findall(r'[a-z][a-z0-9]*',text.casefold())


def pair_features(diff,message):
    parsed=parse_diff(diff);change='\n'.join(parsed['added']+parsed['removed'])
    code=set(words(change));allcode=set(words(diff));paths=set(words(' '.join(parsed['paths'])));tokens=words(message);m=set(tokens)
    def overlap(s):return len(m&s)/max(1,len(m))
    return {'change_overlap':overlap(code),'all_overlap':overlap(allcode),'path_overlap':overlap(paths),
            'change_jaccard':len(m&code)/max(1,len(m|code)),
            'message_log_words':math.log1p(len(tokens)),
            'length_ratio':len(tokens)/max(1,len(words(change))),
            'added_ratio':len(parsed['added'])/max(1,len(parsed['added'])+len(parsed['removed'])),
            'size_message_interaction':math.log1p(len(tokens))*math.log1p(len(change)),
            'first_word:'+tokens[0] if tokens else 'empty_message':1.}


def normalize(scores):
    if len(scores)!=4 or not all(math.isfinite(float(x)) for x in scores):raise ValueError('invalid candidate scores')
    top=max(scores);exp=[math.exp(x-top) for x in scores];total=sum(exp)
    return distribution({str(i):.99*x/total+.01/4 for i,x in enumerate(exp)})

FEATURES=('all','surface','description_only')


def check(evidence):
    if set(evidence)!={'diff','candidate_descriptions'} or not isinstance(evidence['diff'],str):
        raise ValueError('complete public diff/menu only; private fields forbidden')
    candidates=evidence['candidate_descriptions']
    if not isinstance(candidates,list) or len(candidates)!=4 or any(not isinstance(s,str) or not s.strip() for s in candidates) or len(set(candidates))!=4:
        raise ValueError('four distinct complete descriptions required')
    parse_diff(evidence['diff'])
    return candidates


def project(values,kind):
    if kind=='all':return values
    if kind=='surface':return {k:v for k,v in values.items() if k not in ('change_overlap','all_overlap','change_jaccard')}
    if kind=='description_only':return {k:v for k,v in values.items() if k=='message_log_words' or k=='empty_message' or k.startswith('first_word:')}
    raise ValueError('unknown description feature family')


def predict(evidence,model):
    candidates=check(evidence);method=model['method']
    if method=='uniform':return {str(i):.25 for i in range(4)}
    rows=[pair_features(evidence['diff'],candidate) for candidate in candidates]
    if method in ('lexical_overlap','filename_overlap'):
        field='change_overlap' if method=='lexical_overlap' else 'path_overlap'
        return normalize([4*r[field] for r in rows])
    if method!='logistic_pair':raise ValueError('unknown description model')
    weights=model['coefficients'];intercept=model['intercept'];kind=model['features']
    if not isinstance(weights,dict) or type(intercept) not in (int,float) or not math.isfinite(intercept) or any(type(v) not in (int,float) or not math.isfinite(v) for v in weights.values()):
        raise ValueError('invalid fitted description coefficients')
    return normalize([intercept+math.fsum(v*project(row,kind).get(k,0.) for k,v in weights.items()) for row in rows])
