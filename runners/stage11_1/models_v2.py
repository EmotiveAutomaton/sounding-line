"""Versioned interface repair: visible schema, explicit slot order, legacy numeric grammar.

DESIGN CHECK: LESSONS 2-5. NULL: exposing syntax supplies no historical answers;
invalid numbers/references still fail. ALTERNATIVE: the reader can see the same
schema enforced by the parser. Unique reordered slots preserve their semantic
identity; duplicate/missing slots fail. Original requests and parses stay frozen.
"""
import copy
import json
from .models import *
from . import models as v1


def request_for(evidence,kind='direct',retained=None,threads=4):
    q=v1.request_for(evidence,kind,retained,threads)
    body=json.loads(q['messages'][1]['content'])
    body['slot_order']=list(SLOTS)
    body['response_schema']=schema(evidence,kind)
    q['messages'][1]['content']=canonical(body)
    q['messages'][0]['content']+=' JSON only. A probability is between 0 and 1; NEVER use -1 as a missing-value code. Use the unknown category instead. If span_ids is nonempty, span_state MUST be located. For absent, unknown or unlocated spans, span_ids MUST be empty.'
    # Keep the already working Stage 11 numeric grammar: range validation remains
    # strict in the semantic parser and the actual visible schema.
    grammar=copy.deepcopy(q['format'])
    def visit(x):
        if isinstance(x,dict):
            if x.get('type')=='number':x.pop('minimum',None);x.pop('maximum',None)
            for y in x.values():visit(y)
        elif isinstance(x,list):
            for y in x:visit(y)
    visit(grammar);q['format']=grammar
    if sum(len(m['content'].encode('utf-8')) for m in q['messages'])+MAX_TOKENS+512>CONTEXT:raise ValueError('v2 declared context ceiling')
    return q


def parse(raw,evidence,kind):
    if kind=='account':return v1.parse(raw,evidence,kind)
    body=json.loads(raw['message']['content'])
    if isinstance(body,dict) and isinstance(body.get('facts'),list):
        slots=[x.get('slot') for x in body['facts'] if isinstance(x,dict)]
        if len(slots)==len(SLOTS) and set(slots)==set(SLOTS):
            body['facts'].sort(key=lambda x:SLOTS.index(x['slot']))
    normalized=copy.deepcopy(raw);normalized['message']['content']=canonical(body)
    return v1.parse(normalized,evidence,kind)
