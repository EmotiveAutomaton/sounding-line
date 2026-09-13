"""Approximate executable ScholaWrite rules, separate from annotator intent.

DESIGN CHECK: LESSONS2-5. Constants reproduce their declared lapse mixture;
known feature changes switch the expected action. Future fields, unknown labels
and duplicate candidates refuse. A plausible goal sentence never changes execution.
The fixed .15 lapse matches the existing human instrument, not a fitted human law.
"""
import math
import re
from .contracts import canonical, digest
from .revision_source import DESCRIPTIONS
from runners.stage9.program_inference import noisy_action, predictive_mixture

FEATURES = {
    'constant': 'Always zero; threshold one makes a constant rule.',
    'draft_words': 'Word count of the current visible editor text.',
    'draft_characters': 'Character count of current visible editor text.',
    'draft_lines': 'Line count of current visible editor text.',
    'citation_markers': 'Count of literal LaTeX cite markers in current editor text.',
    'section_markers': 'Count of literal LaTeX section markers in current editor text.',
    'prior_artifact_available': 'One if a genuinely earlier editor state is supplied.',
    'previous_words': 'Words in the supplied earlier editor state, otherwise zero.',
    'absolute_word_change': 'Absolute difference between previous/current word count, otherwise zero.',
    'prior_record_available': 'One if released labels of the prior edit are supplied.',
    **{'previous_'+key: 'One if the supplied prior edit label is '+key+'; zero without that record.'
       for mapping in DESCRIPTIONS.values() for key in mapping}}


def descriptions(task):
    if task.family not in DESCRIPTIONS or set(dict(task.choices).values()) != set(DESCRIPTIONS[task.family].values()):
        raise ValueError('undeclared source-native revision target')
    return DESCRIPTIONS[task.family]


def features(task):
    descriptions(task)
    e=task.evidence; expected={'document'}; previous=None
    if task.evidence_view=='earlier-artifacts':
        expected.add('earlier_drafts')
        if not isinstance(e.get('earlier_drafts'),list) or len(e['earlier_drafts'])!=1: raise ValueError('one actual earlier editor state required')
        previous=e['earlier_drafts'][0]
    elif task.evidence_view=='process-record':
        expected|={'previous_document','previous_category','previous_location'};previous=e.get('previous_document')
        if e.get('previous_category') not in DESCRIPTIONS['schola_category'] or e.get('previous_location') not in DESCRIPTIONS['schola_location']:
            raise ValueError('unknown previous source labels')
    elif task.evidence_view!='artifact':raise ValueError('undeclared evidence view')
    if set(e)!=expected or not isinstance(e['document'],str) or (previous is not None and not isinstance(previous,str)):
        raise ValueError('unexpected or nontext evidence fields')
    words=lambda text:len(re.findall(r'\w+',text))
    current=words(e['document']);old=words(previous) if previous is not None else 0
    result={'constant':0,'draft_words':current,'draft_characters':len(e['document']),
        'draft_lines':len(e['document'].splitlines()),'citation_markers':e['document'].count('\\cite'),
        'section_markers':e['document'].count('\\section'),'prior_artifact_available':int(previous is not None),
        'previous_words':old,'absolute_word_change':abs(current-old) if previous is not None else 0,
        'prior_record_available':int(task.evidence_view=='process-record')}
    for key in set(FEATURES)-set(result):
        result[key]=int(key[9:] in {e.get('previous_category'),e.get('previous_location')})
    return result


def validate(program, task):
    actions=descriptions(task)
    if not isinstance(program,dict) or set(program)!={'feature','threshold','below','otherwise'}:
        raise ValueError('invalid revision program fields')
    if program['feature'] not in FEATURES or type(program['threshold']) not in {int,float} or not math.isfinite(program['threshold']) or not 0<=program['threshold']<=100000:
        raise ValueError('invalid public feature or threshold')
    if program['below'] not in actions or program['otherwise'] not in actions:raise ValueError('program action outside this target')
    return program


def execute(program, observed, task):
    validate(program,task)
    if set(observed)!=set(FEATURES):raise ValueError('incomplete feature record')
    action=program['below'] if observed[program['feature']]<program['threshold'] else program['otherwise']
    return {'action':action,'probabilities':noisy_action(action,tuple(descriptions(task)),.15)}


def evaluate(task,candidates):
    observed=features(task)
    if not isinstance(candidates,list) or not 1<=len(candidates)<=8:raise ValueError('one to eight candidates required')
    programs=[]
    for item in candidates:
        if not isinstance(item,dict) or set(item)!={'goal_hypothesis','program'} or not isinstance(item['goal_hypothesis'],str) or len(item['goal_hypothesis'])>100:
            raise ValueError('separate bounded goal conjecture required')
        programs.append(validate(item['program'],task))
    if len({canonical(p) for p in programs})!=len(programs):raise ValueError('duplicate candidate changes mixture weight')
    executed={str(i):execute(p,observed,task) for i,p in enumerate(programs)}
    weights={key:1/len(executed) for key in executed}
    mixture=predictive_mixture(weights,{key:value['probabilities'] for key,value in executed.items()})
    ids={v:k for k,v in task.choices};mapping=descriptions(task)
    return {'features':observed,'executed':executed,'weights':weights,
        'probabilities':{ids[mapping[a]]:p for a,p in mixture.items()},'executor_evaluations':len(programs),
        'programs_sha256':digest(programs),'readout':'equal mixture of proposed consequences with fixed total lapse .15',
        'meaning':'approximate forecasts of released edit labels; no inferred historical intent truth'}
