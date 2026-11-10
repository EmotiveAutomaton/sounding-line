"""Article-cluster uncertainty kernel; no source-label creation or human handler.

Prepared for the commissioned T2.r contrast. Admission still requires an
authenticated complete prediction/label bank and the owner's source mapping.
Every bootstrap draw resamples the entire frozen article roster, including
articles with no eligible labelled sentence. Undefined draws remain undefined.
"""
from collections import Counter
import numpy as np
from .week5_bk_t2_analysis import auc, SEED


class ArticleBank:
    def __init__(self, rows, article_roster):
        self.roster = list(article_roster)
        if not self.roster or len(set(self.roster)) != len(self.roster):
            raise ValueError('Empty or duplicate frozen article roster')
        lookup = {value:i for i,value in enumerate(self.roster)}
        keys, selected, statuses = set(), [], Counter()
        for row in rows:
            if set(row) != {'article', 'sentence', 'outcome', 'status', 'prediction', 'baseline_prediction'}:
                raise ValueError('Unexpected prediction-bank field')
            if row['article'] not in lookup or type(row['sentence']) is not int or row['sentence'] < 0:
                raise ValueError('Sentence does not belong to the frozen article roster')
            key = row['article'], row['sentence']
            if key in keys:
                raise ValueError('Repeated final sentence in external prediction bank')
            keys.add(key)
            if not isinstance(row['status'], str) or not row['status']:
                raise ValueError('Missing source/lineage status')
            statuses[row['status']] += 1
            if row['outcome'] is None:
                if row['status'] == 'eligible':
                    raise ValueError('Eligible outcome cannot be undefined')
                continue
            if type(row['outcome']) is not int or row['outcome'] not in (0, 1) or row['status'] != 'eligible':
                raise ValueError('Unknown lineage cannot become a binary outcome')
            for field in ('prediction', 'baseline_prediction'):
                value = row[field]
                if not isinstance(value, (int, float)) or not np.isfinite(value) or not 0 <= value <= 1:
                    raise ValueError('Eligible sentence has invalid probability')
            selected.append(row)
        self.y = np.asarray([r['outcome'] for r in selected], int)
        self.prediction = np.asarray([r['prediction'] for r in selected], float)
        self.baseline = np.asarray([r['baseline_prediction'] for r in selected], float)
        self.article_index = np.asarray([lookup[r['article']] for r in selected], int)
        self.counts = dict(roster_articles=len(self.roster),
                           labelled_articles=len(set(self.article_index.tolist())),
                           articles_without_labelled_sentence=len(self.roster)-len(set(self.article_index.tolist())),
                           all_final_sentence_rows=len(rows), labelled_sentences=len(selected),
                           undefined_outcomes=len(rows)-len(selected), positive_sentences=int(self.y.sum()),
                           negative_sentences=int(len(self.y)-self.y.sum()), statuses=dict(sorted(statuses.items())))

    def point(self, weights=None):
        full, base = auc(self.y, self.prediction, weights), auc(self.y, self.baseline, weights)
        return None if full is None or base is None else [full, base, full-base]

    def draw(self, ordinal):
        if type(ordinal) is not int or not 0 <= ordinal < 2000:
            raise ValueError('Primary requires exactly the frozen 2000 draws')
        rng = np.random.default_rng(np.random.SeedSequence([SEED, ordinal]))
        copies = np.bincount(rng.integers(0, len(self.roster), len(self.roster)), minlength=len(self.roster))
        # Retain no-outcome articles in sampling; they contribute zero sentences.
        return self.point(copies[self.article_index])

    def summary(self, draws):
        if len(draws) != 2000:
            raise ValueError('Incomplete article uncertainty is not a result')
        for value in draws:
            if value is not None and (len(value) != 3 or not np.isfinite(value).all()
                                       or not 0 <= value[0] <= 1 or not 0 <= value[1] <= 1
                                       or abs(value[2]-(value[0]-value[1])) > 1e-12):
                raise ValueError('Invalid saved article draw')
        point = self.point()
        undefined = sum(value is None for value in draws)
        interval = None if undefined else np.quantile(np.asarray(draws), [.025, .975], axis=0).tolist()
        return dict(counts=self.counts, statistic_columns=['auc', 'baseline_auc', 'gain'],
                    point=point, interval=interval, bootstrap_draws=2000,
                    undefined_draws=undefined, whole_frozen_roster_resampled=True,
                    conditional_on_frozen_training_and_prediction_bank=True,
                    training_uncertainty_included=False, support_floor=20,
                    support_scope='article-cluster external comparison' if self.counts['labelled_articles'] >= 20
                                  else 'below floor, descriptive',
                    practical_bar=.05,
                    point_crosses_bar=point is not None and point[2] >= .05,
                    interval_above_zero=interval is not None and interval[0][2] > 0,
                    scientific_status='requires separately authenticated source and instrument qualification')
