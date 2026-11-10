"""GO2 source healing: a copied proposal begins at its copy, not its origin.

Git --follow may infer a copy from a different proposal's template. Keep the
copy-target version, stop before its origin history, and count that boundary.
Deletion revisions break adjacency. Missing nondeleted objects still fail.
"""
from collections import Counter
from pathlib import Path
from types import FunctionType
from . import week5_go as core
from . import week5_go_history as original


class SourceCore:
    def __init__(self):self.counts=Counter();self.deleted=set()

    def __getattr__(self,name):return getattr(core,name)

    def git(self,repo,*args):
        if args[0]=='show' and (str(repo),args[1]) in self.deleted:
            self.counts['deletion_boundaries']+=1
            return ''  # An absent version fails parsing and breaks adjacency.
        result=core.git(repo,*args)
        if args[0]!='log' or '--follow' not in args:return result
        current=args[-1];commit=None;lines=result.splitlines();stop=None
        for index,line in enumerate(lines):
            if line.startswith('COMMIT '):commit=line.split()[1]
            elif line.startswith(('R','C')):
                fields=line.split('\t')
                if len(fields)!=3:raise ValueError('ambiguous Git copy/rename record')
                if fields[2]!=current:raise ValueError('Git follow path differs from current document')
                if fields[0].startswith('C'):
                    self.counts['copy_creation_boundaries']+=1
                    stop=next((j for j in range(index+1,len(lines)) if lines[j].startswith('COMMIT ')),len(lines))
                    self.counts['copy_origin_revisions_excluded']+=sum(l.startswith('COMMIT ') for l in lines[stop:])
                    break
                current=fields[1]
            elif line.startswith('D\t'):
                fields=line.split('\t')
                if len(fields)!=2 or fields[1]!=current:raise ValueError('ambiguous Git deletion record')
                self.deleted.add((str(repo),commit+':'+current))
        return '\n'.join(lines if stop is None else lines[:stop])+'\n'


def source(output,inputs):
    adapter=SourceCore()
    run=FunctionType(original.source.__code__,dict(original.source.__globals__,core=adapter),
                     original.source.__name__,original.source.__defaults__,original.source.__closure__)
    result=run(output,inputs)
    for key,value in adapter.counts.items():result['counts'][key]=result['counts'].get(key,0)+value
    result['history_semantics']='renames followed; copy-target creation retained, unrelated origin history excluded; deletions break adjacency'
    result['successor_module_sha256']=core.sha(__file__)
    core.write(Path(output)/'SOURCE.json',result);return result


def execute(output,inputs,config):
    if config.get('phase')!='prepare':raise ValueError('source-only successor')
    return source(Path(output),inputs)


def verify(output,inputs,config):
    import json
    output=Path(output);actual=source(output/'independent-replay',inputs)
    if actual!=json.loads((output/'SOURCE.json').read_text('utf8')):raise ValueError('healed history complete replay differs')
    return {'verified':True,'complete_same_document_source_replay':True}
