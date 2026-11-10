"""Prepared counted constructed transfer boundary qualification, not run yet."""
from pathlib import Path
import copy
import json
import numpy as np
from threadpoolctl import threadpool_limits
from . import week5_bk_t2_transfer_model as transfer
from . import week5_bk_t2_analysis as original
from . import week5_bk_t2_wiki_text as wiki
from .week5_bk_t2_transfer_uncertainty import ArticleBank
from .timing_p6 import write_equal
from .timing_census import read


def rows(kind='signal'):
    result = []
    for writer in range(20):
        for index in range(8):
            y = index % 2
            baseline = [float(y) if kind == 'baseline_only' else 12., 3., .5]
            features = baseline + [0.] * 268 + [float(y) if kind == 'signal' else 0., 1.]
            result.append(dict(writer=f'constructed-{writer}', session=f'constructed-{writer}',
                               index=index, genre='creative', labels=dict(a=None, b=y, c=None),
                               baseline=baseline, features=features))
    return result


def refuses(callback):
    try:
        callback()
    except (ValueError, TypeError):
        return True
    raise AssertionError('Required refusal did not occur')


def calculate(check):
    models = {}
    for kind in ('signal', 'null', 'baseline_only'):
        check()
        source = rows(kind)
        selected, y, base, full = transfer.matrices(source)
        model = json.loads(json.dumps(transfer.fit(source, ['constructed', 'constructed', 273], check)))
        bp, fp = transfer.predict(model, base, full)
        oracle_b = original.predict(base, y, np.full(len(y), -1), 'ridge', check)
        oracle_f = original.predict(full, y, np.full(len(y), -1), 'ridge', check)
        if not np.allclose(bp, oracle_b, atol=1e-12, rtol=0) or not np.allclose(fp, oracle_f, atol=1e-12, rtol=0):
            raise AssertionError('Serialized model differs from original T2 pooled prediction')
        gain = original.auc(y, fp) - original.auc(y, bp)
        if (kind == 'signal' and gain <= .45) or (kind != 'signal' and abs(gain) > 1e-12):
            raise AssertionError('Constructed signal/null/baseline oracle failed')
        changed = copy.deepcopy(source)
        for item in changed:
            item['labels']['b'] = 1 - item['labels']['b']
            item['writer'] = 'changed-external-metadata'
        changed_bp, changed_fp = transfer.predict(model, [r['baseline'] for r in changed], [r['features'] for r in changed])
        if not np.array_equal(changed_bp, bp) or not np.array_equal(changed_fp, fp):
            raise AssertionError('External metadata entered prediction')
        refuses(lambda: transfer.predict(model, base, full, labels=y))
        models[kind] = dict(sentences=len(selected), original_fit_equivalence=True,
                            serialized_prediction_equivalence=True, evaluation_metadata_isolation=True,
                            auc_gain=float(gain))
        article_rows = [dict(article=r['writer'], sentence=r['index'], outcome=r['labels']['b'],
                             status='eligible', prediction=float(fp[i]), baseline_prediction=float(bp[i]))
                        for i,r in enumerate(source)]
        article_rows.append(dict(article='constructed-left-censored', sentence=0, outcome=None,
                                 status='left_censored', prediction=None, baseline_prediction=None))
        roster = [f'constructed-{i}' for i in range(20)] + ['constructed-left-censored', 'constructed-inactive']
        bank = ArticleBank(article_rows, roster)
        draws = []
        for i in range(2000):
            check()
            draws.append(bank.draw(i))
        summary = bank.summary(draws)
        if (summary['counts']['roster_articles'] != 22
                or summary['counts']['labelled_articles'] != 20
                or summary['counts']['undefined_outcomes'] != 1
                or summary['undefined_draws'] != 0
                or summary['point'] != [original.auc(y, fp), original.auc(y, bp), gain]):
            raise AssertionError('Article denominator or uncertainty oracle failed')
        expected = .5 if kind == 'signal' else 0.
        if abs(summary['interval'][0][2]-expected) > 1e-12 or abs(summary['interval'][1][2]-expected) > 1e-12:
            raise AssertionError('Known complete article interval differs')
        models[kind]['complete_article_uncertainty'] = summary
    check()
    value = "A {{outer|{{inner|x}}|{{{fallback|z}}}}} [[Target|visible]] statement.<ref name='n'>Secret {{citation}}</ref>\n{| class='wikitable'\n| nested {|x|}\n|}\nAn [https://example.org external] '''ending'''."
    text, counts = wiki.clean_wikitext(value)
    if text != 'A visible statement.\nAn external ending.':
        raise AssertionError('Constructed wikitext projection differs')
    for name in ('dropped_templates', 'dropped_tables', 'dropped_ref', 'visible_internal_links', 'external_links'):
        if counts.get(name) != 1:
            raise AssertionError('Constructed markup accounting differs')
    malformed = ['A {{broken.', 'A <ref>broken.', 'A <unknown>x</unknown>.',
                 'A [[missing.', 'A __TOC__.', 'A <nowiki>{{literal}}</nowiki>.', 'A <ref']
    for value in malformed:
        check()
        refuses(lambda value=value: wiki.final_sentences(value))
    before = wiki.final_sentences('The first sentence. The old second sentence.')
    after = wiki.final_sentences('The first sentence. The rewritten final sentence.')
    if (before['sentences'][0]['text'] != after['sentences'][0]['text']
            or before['sentences'][-1]['text'] == after['sentences'][-1]['text']
            or after['labels_computed'] or after['feature_time'] != 'final_current_version'):
        raise AssertionError('Final-version retrospective feature contract changed')
    refuses(lambda: wiki.final_sentences('Final sentence.', history=[]))
    for kind in ('one_class', 'duplicate', 'nonfinite', 'baseline'):
        sample = rows()
        if kind == 'one_class':
            for item in sample:
                item['labels']['b'] = 0
        elif kind == 'duplicate':
            sample.append(copy.deepcopy(sample[0]))
        elif kind == 'nonfinite':
            sample[0]['features'][-1] = float('nan')
        else:
            sample[0]['baseline'][0] += 1
        refuses(lambda sample=sample: transfer.fit(sample, []))
    return dict(constructed=True, models=models,
                markup_exact_oracle=True, malformed_structure_refusals=len(malformed),
                model_input_refusals=4, label_creation=False,
                final_text_contract='retrospective detection, not future prediction',
                source_scope_admitted=False, human_execution=False)


def run(output, inputs, config, verification=False):
    if inputs or config != dict(constructed_fixture=True):
        raise ValueError('Constructed fixture only')
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    def check():
        if (output/'YIELD_REQUEST.json').exists():
            raise InterruptedError('Owner fixture stop')
    try:
        with threadpool_limits(limits=2):
            proof = calculate(check)
    except InterruptedError:
        return dict(status='yielded', reason='restart the entire constructed fixture in fresh empty output')
    if verification:
        if not original.same(proof, read(output/'FIXTURE.json')):
            raise ValueError('Full constructed refit/parser replay differs')
        return dict(verified=True, all_models_and_parser_checks_recomputed=True)
    write_equal(output/'FIXTURE.json', proof)
    return dict(status='complete')


def execute(output, inputs, config):
    return run(output, inputs, config)


def verify(output, inputs, config):
    return run(output, inputs, config, True)
