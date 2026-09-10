"""Bounded genetic-edition preparation, explicitly local and partial-order only.

DESIGN CHECK: Stage 9 I02/H04. Source: SGA encoding guidelines sections 5–8 and restore.
NULL: ambiguous spans, multiple stages or uncertain transcription cannot become a
clean ordered replacement. ALTERNATIVE: a self-contained mod with del then add yields
its exact two local readings. Unsupported encodings remain counted with reasons.
The output is reconstructed LOCAL text, not a complete chronological manuscript draft.
"""
from collections import Counter
from pathlib import Path
import re
import xml.etree.ElementTree as ET

from runners.stage9.common import ROOT, digest, file_hash, freeze, read, write

NS = '{http://www.tei-c.org/ns/1.0}'
UNSAFE = {'unclear', 'damage', 'restore', 'delSpan', 'addSpan', 'alt', 'transpose', 'listTranspose', 'handShift'}
INLINE = {'hi', 'retrace'}


def tag(element):
    return element.tag.split('}')[-1]


def safe_parse(raw):
    if len(raw) > 1024**2:
        raise ValueError('TEI record exceeds parser cap')
    # Do not resolve entities, DTDs, schemas, image links, XIncludes or network paths.
    if re.search(br'<!\s*(DOCTYPE|ENTITY)', raw, re.I):
        raise ValueError('DTD/entity declarations refused')
    root = ET.fromstring(raw)
    if root.tag != NS + 'surface':
        raise ValueError('expected a released TEI surface record')
    return root


def inline(element):
    parts = [element.text or '']
    for child in element:
        if tag(child) == 'metamark' and child.get('function') == 'insert':
            pass  # editorial caret, never language shown to the reader
        elif tag(child) in INLINE:
            parts.append(inline(child))
        else:
            raise ValueError('unsupported or ambiguous nested inline encoding: ' + tag(child))
        parts.append(child.tail or '')
    return ''.join(parts)


def replacements(raw, source_sha):
    root = safe_parse(raw)
    elements = list(root.iter())
    positions = {e: i for i, e in enumerate(elements)}
    anchors = {e.get('{http://www.w3.org/XML/1998/namespace}id'): i for i, e in enumerate(elements)
               if e.get('{http://www.w3.org/XML/1998/namespace}id')}
    spans = [(i, anchors.get(e.get('spanTo', '').lstrip('#'), len(elements)))
             for i, e in enumerate(elements) if tag(e) in ('delSpan', 'addSpan', 'mod') and e.get('spanTo')]
    parents = {child: parent for parent in root.iter() for child in parent}
    cases, exclusions = [], Counter()
    mods = list(root.iter(NS + 'mod'))
    for index, mod in enumerate(mods):
        if any(start <= positions[mod] < end for start, end in spans):
            exclusions['inside linked or unresolved cross-line span'] += 1
            continue
        ancestors, node = [], mod
        while node in parents:
            node = parents[node]
            ancestors.append(node)
        if any(tag(a) in {'del', 'add', 'restore', 'mod'} for a in ancestors):
            exclusions['nested or later-cancelled intervention'] += 1
            continue
        if any(tag(e) in UNSAFE or 'spanTo' in e.attrib or 'next' in e.attrib or e.get('type') == 'alternative' for e in mod.iter()):
            exclusions['uncertain, linked or multistage intervention'] += 1
            continue
        # Surrounding line-level span pointers can make the local reading uncertain.
        line = next((a for a in ancestors if tag(a) == 'line'), None)
        if line is not None and any(tag(e) in UNSAFE or 'spanTo' in e.attrib for e in line.iter() if e is not mod):
            exclusions['surrounding line has unresolved span or uncertainty'] += 1
            continue
        children = list(mod)
        kinds = [tag(e) for e in children]
        if not kinds or any(k not in ('del', 'add') for k in kinds) or 'del' not in kinds or 'add' not in kinds:
            exclusions['not a direct del-then-add replacement'] += 1
            continue
        boundary = kinds.index('add')
        if any(k != 'del' for k in kinds[:boundary]) or any(k != 'add' for k in kinds[boundary:]):
            exclusions['multiple interleaved change stages'] += 1
            continue
        try:
            before = re.sub(r'\s+', ' ', ''.join(inline(e) + (e.tail or '') for e in children[:boundary])).strip()
            after = re.sub(r'\s+', ' ', ''.join(inline(e) + (e.tail or '') for e in children[boundary:])).strip()
        except ValueError as exc:
            exclusions[str(exc)] += 1
            continue
        if not before or not after or before == after:
            exclusions['empty or unchanged local reading'] += 1
            continue
        hands = sorted({e.get('hand') for e in mod.iter() if e.get('hand')})
        cases.append({'key': digest([source_sha, index]), 'work': 'Frankenstein manuscripts',
                      'local_before': before, 'local_after': after, 'hands': hands,
                      'hand_status': 'editorial attribution retained' if hands else 'unspecified in local markup',
                      'source_sha256': source_sha, 'source_mod_index': index,
                      'order': 'local deletion precedes addition under published encoding; no global chronology',
                      'limits': ['local reconstructed readings only', 'unknown broader chronology', 'famous-text memorization possible']})
    return cases, {'mod_elements': len(mods), 'eligible_local_replacements': len(cases), 'exclusions': dict(exclusions)}


def prepare(records_path, output):
    source_records = read(records_path)
    cases, source_counts = [], []
    for source in source_records:
        if 'receipt' not in source:
            source_counts.append({'path': source['path'], 'acquisition_failure': source['error']})
            continue
        sha = source['receipt']['sha256']
        path = ROOT / 'private/intake/objects' / sha
        if file_hash(path) != sha:
            raise ValueError('acquired TEI bytes changed')
        found, counts = replacements(path.read_bytes(), sha)
        for case in found:
            case['source_path'] = source['path']
        cases.extend(found)
        source_counts.append({'path': source['path'], 'sha256': sha, **counts})
    # Fixed seed/key order is chosen before any model or baseline performance is read.
    cases.sort(key=lambda r: digest([90604, r['key']]))
    selected = cases[:24]
    tasks = []
    for case in selected:
        true = case['local_after']
        candidates = sorted({r['local_after'] for r in cases if r['key'] != case['key'] and r['local_after'] != true},
                            key=lambda text: (abs(len(text.split()) - len(true.split())), digest([case['key'], text])))[:3]
        if len(candidates) != 3:
            raise ValueError('insufficient distinct replacement alternatives')
        offered = sorted([true, *candidates], key=lambda text: digest([90604, case['key'], text]))
        options = {'choice_' + str(i): text for i, text in enumerate(offered)}
        truth = next(k for k, text in options.items() if text == true)
        tasks.append({'key': case['key'], 'unit': case['work'],
                      'evidence': {'prefix': 'A local manuscript reading before a documented revision:\n' + case['local_before'] + '\nA possible replacement is:\n', 'options': options},
                      'truth': truth, 'case': case, 'claim_ceiling': 'qualitative, one known work; no population inference',
                      'candidate_design': 'one documented replacement plus three other replacements matched first on word count; offered-set diagnostic'})
    output = Path(output)
    identity = {'source_receipts': digest(source_records), 'source': file_hash(__file__), 'seed': 90604,
                'selected_keys': [r['key'] for r in selected], 'max_tasks': 24, 'candidate_count': 4}
    freeze(output / 'IDENTITY.json', identity)
    freeze(output / 'cases.json', cases)
    freeze(output / 'tasks.json', tasks)
    receipt = {'identity_sha256': digest(identity), 'source_counts': source_counts, 'acquired_surfaces': sum('receipt' in r for r in source_records),
               'local_replacements': len(cases), 'selected_tasks': len(tasks), 'independent_works': 1,
               'published_count_reproduction': False, 'schema_based_local_pair_reconstruction': True,
               'chronology': 'partial local order only; page sequence never used as production order',
               'predictive_baseline': 'pending', 'population_or_confirmation_claim': 'ineligible: one famous work'}
    write(ROOT / 'intake/SGA_PREPARATION.json', receipt)
    return receipt


if __name__ == '__main__':
    import argparse
    import json
    parser = argparse.ArgumentParser()
    parser.add_argument('records', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    print(json.dumps(prepare(args.records, args.output), sort_keys=True))
