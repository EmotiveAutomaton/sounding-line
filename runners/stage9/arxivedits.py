"""Canonical annotated spans and explicit-license paper/version preparation.

DESIGN CHECK: LESSONS sections 2-5 read; Stage 9 H02/I02/X01.
NULL: wrong spans, versions or counts must fail; alternatives cannot inflate units.
ALTERNATIVE: released canonical edits reproduce exactly, with complete provenance.
Bands: invalid schema/count raises; unsupported rights/correspondence excludes the
whole pair; retained records are development-only for this three-paper selection.
No source text, identity, alternative decomposition or label enters a reader except
through the explicit text-only projection. No downloaded code is executed.
"""
from collections import Counter
import time

from runners.stage9.common import REPO,ROOT,closure,digest,file_hash,freeze,read

LABELS=('Content','Format','Improve-grammar-Typo','Lang-accurate-spefific',
        'Lang-professional-Improve-style','Lang-improve-readability-Simplify','Lang-other')
LICENSES={
 'http://creativecommons.org/licenses/by/3.0/',
 'http://creativecommons.org/licenses/by/4.0/',
 'http://creativecommons.org/licenses/by-sa/4.0/',
 'http://creativecommons.org/licenses/by-nc-sa/4.0/',
 'http://creativecommons.org/publicdomain/zero/1.0/',
 'http://creativecommons.org/licenses/publicdomain/',
}


def span(tokens,indices,required):
    if not required:
        if indices is not None:raise ValueError('unexpected nonempty absent side')
        return ''
    if not isinstance(indices,list) or len(indices)!=2 or any(type(v) is not int for v in indices):
        raise ValueError('invalid source span')
    start,end=indices
    if not 0<=start<end<=len(tokens):raise ValueError('span outside source sentence')
    return ' '.join(tokens[start:end])


def canonical_edits(pair):
    """Release classifier uses combination zero. Other combinations stay in pair."""
    if any(not isinstance(pair[f'sentence-{i}'],str) for i in (1,2)):
        raise ValueError('sentence text required')
    edits=[]
    for index,edit in pair['edits-combination-0'].items():
        kind=edit['type'];label=edit['intention']
        if kind not in ('Insertion','Deletion','Substitute') or label not in LABELS:
            raise ValueError('unknown canonical operation or annotation')
        before=span(pair['sentence-1'].split(),edit['sentence-1-token-indices'],kind!='Insertion')
        after=span(pair['sentence-2'].split(),edit['sentence-2-token-indices'],kind!='Deletion')
        edits.append({'edit_index':index,'kind':kind,'label':label,'before':before,'artifact':after,
                      'source_span_1':edit['sentence-1-token-indices'],'source_span_2':edit['sentence-2-token-indices']})
    return edits


def correspondence(pair,paper):
    matches=[];licenses=[]
    for side in (1,2):
        version=str(pair[f'sentence-{side}-level']);licenses.append(paper['license'].get(version))
        compact=''.join(pair[f'sentence-{side}'].split())
        matches.append([key for key,text in paper.get(version,{}).items()
                        if ''.join(text.split())==compact])
    reason='outside_explicit_license_selection' if not all(x in LICENSES for x in licenses) else None
    if reason is None and any(len(x)!=1 for x in matches):reason='unverified_unique_version_sentence'
    return {'licenses':licenses,'sentence_matches':matches,'exclusion':reason}


def visible(record,view):
    if view=='artifact':return {'text':record['artifact']}
    if view=='pair':return {'text':record['artifact'],'before':record['before']}
    raise ValueError('unknown revision evidence view')


def raw_inputs():
    source=read(ROOT/'intake/ARXIVEDITS_SOURCE_FILES.json')
    objects=ROOT/'private/intake/objects';paths={}
    for f in source['files']:
        path=objects/f['receipt']['sha256']
        if file_hash(path)!=f['receipt']['sha256'] or not f['receipt']['complete_eof']:
            raise ValueError('source changed or incomplete')
        paths[f['path']]=path
    identity={'release_pin':source['pin'],'input_files':{k:file_hash(v) for k,v in paths.items()},
              'sources':closure([REPO/'runners/stage9'/n for n in ('arxivedits.py','common.py')]),
              'canonical_rule':'release classifier combination zero, whitespace token offsets [start,end)',
              'rights_selection':sorted(LICENSES),'correspondence':'unique exact sentence after whitespace removal in each claimed version',
              'split':'all retained papers development-only; no new reserve; whole paper/version lineage',
              'limits':'coauthors not disentangled; supplied annotated segments, not localization or privileged intentions'}
    return paths,identity


def reconstruct(paths,release_pin):
    """Original released spans and exclusions, without writing prepared evidence."""
    counts={};attempts=[];records=[];lineages={};versions=0;all_papers=set();pair_payloads={}
    for lane,expected_pairs,expected_papers,expected_edits in [('train',600,526,1254),('dev',200,75,438),('test',200,150,430)]:
        pairs=read(paths[f'data/edits/{lane}.json']);papers=read(paths[f'data/sentence_alignment/{lane}.json'])
        if len(pairs)!=expected_pairs or len(papers)!=expected_papers:raise ValueError('source pair/paper count mismatch')
        if all_papers & set(papers):raise ValueError('source paper crosses original splits')
        all_papers.update(papers);versions+=sum(sum(k.isdigit() for k in p) for p in papers.values())
        labels=Counter();alternative_counts=Counter();kept=0
        for index,pair in pairs.items():
            paper=papers[pair['arxiv-id']];edits=canonical_edits(pair);labels.update(e['label'] for e in edits)
            check=correspondence(pair,paper);key=digest({'release':release_pin,'lane':lane,'pair':index})
            for n in (1,2):alternative_counts[str(n)]+=len(pair[f'edits-combination-{n}'])
            attempt={'key':key,'original_split':lane,'source_index':index,'paper':pair['arxiv-id'],
                     'canonical_edits':len(edits),**check}
            attempts.append(attempt)
            if check['exclusion']:continue
            unit='arxiv:'+pair['arxiv-id'];kept+=1
            lineages.setdefault(unit,{'source_paper':pair['arxiv-id'],'pairs':[]})['pairs'].append(key)
            # Preserve the full annotation/alternative record privately; no silent relabeling.
            pair_payloads[key]={'source_pair':pair,'correspondence':check}
            for edit in edits:
                records.append(edit|{'key':digest({'pair':key,'edit':edit['edit_index']}),'pair':key,
                                    'independent_unit':unit,'split':'development','licenses':check['licenses']})
        if sum(labels.values())!=expected_edits:raise ValueError('canonical edit count mismatch')
        counts[lane]={'papers':len(papers),'sentence_pairs':len(pairs),'canonical_edits':sum(labels.values()),
                      'label_counts':dict(labels),'alternative_edit_counts':dict(alternative_counts),'selected_pairs':kept}
    if len(all_papers)!=751 or versions!=1790:raise ValueError('published paper/version count mismatch')
    result={'source_counts_match':True,'source_counts':counts,'versions':versions,
            'attempted_pairs':len(attempts),'selected_pairs':sum(x['exclusion'] is None for x in attempts),
            'pair_exclusions':dict(Counter(x['exclusion'] for x in attempts if x['exclusion'])),
            'usable_edits':len(records),'paper_lineages':len(lineages),'reserve_groups':0,
            'baseline_ready':False,
            'limits':['three-paper qualitative selection','annotator purposes, not maker statements',
                      'full paper lineage grouping','cross-source arXiv/IteraTeR duplicate audit owed']}
    return pair_payloads,attempts,records,lineages,result


def prepare():
    started=time.time();paths,identity=raw_inputs()
    directory=ROOT/'private/prepared/arxivedits-v1'
    freeze(directory/'IDENTITY.json',identity)
    if (directory/'COMPLETE.json').exists():return read(directory/'COMPLETE.json')
    pairs,attempts,records,lineages,summary=reconstruct(paths,identity['release_pin'])
    for key,value in pairs.items():freeze(directory/'pairs'/(key+'.json'),value)
    freeze(directory/'ATTEMPTS.json',attempts);freeze(directory/'RECORDS.json',records);freeze(directory/'LINEAGES.json',lineages)
    result={'identity_sha256':digest(identity),**summary,
        'output_hashes':{n:file_hash(directory/n) for n in ('ATTEMPTS.json','RECORDS.json','LINEAGES.json')},
        'elapsed_seconds':time.time()-started,'completed_at':time.time()}
    freeze(directory/'COMPLETE.json',result);freeze(ROOT/'intake/ARXIVEDITS_PREPARATION.json',result)
    return result


if __name__=='__main__':
    print(prepare())
