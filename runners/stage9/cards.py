"""Manually translated Stage 9 card inventory; not the executable cell manifest.

DESIGN CHECK: the owner's 42 cards stay individually visible when branches fail.
No automatic TODO/spec parsing. Runtime estimates and concrete cell identities must
be attached after actual pilots; this inventory alone can never launch science.
"""
from dataclasses import dataclass

from runners.stage9.common import ROOT, REPO

# Current authority moved byte-for-byte at the curator's request. Keep common.py
# unchanged: completed source audits bind its historical bytes.
SPEC = REPO / 'docs/design/PHASE_2_4_STAGE_9_CONTEXT.md'


@dataclass(frozen=True)
class Card:
    key: str
    hypothesis: str
    method: str
    primary_contrast: str
    independent_unit: str
    permitted_evidence: str
    strongest_rival: str
    prerequisite_scope: str
    source: str

    @property
    def produces(self):
        return str(ROOT / self.key / 'COMPLETE.json')


CARDS = (
    Card('I01', 'Current evidence and dependencies can be reconstructed without inventing historical provenance.',
         'Reconcile current state, inherited failures, actual source files and dependency scope.', 'actual versus claimed provenance',
         'source or result artifact', 'evaluator-only records', 'original preserved receipts', 'no scientific acceptance from inventory', str(SPEC)),
    Card('I02', 'A released source is usable only if its actual records traverse the loader and a baseline.',
         'Bounded acquisition, rights and schema inspection, source-count reconciliation, grouped baseline.', 'actual predictive readiness versus inventory',
         'source-defined independent group', 'per-source whitelist', 'source baseline and training-only cheap rival', 'each corpus independently', str(SPEC)),
    Card('I03', 'Every offered option and invalid component is measured by the repaired readout.',
         'Actual maximum supports, ties, STOP, permutations, omissions, batch and precision calibration.', 'complete versus corrupted component evidence',
         'known-answer fixture', 'common prefix and complete offered continuations', 'serial CPU reference', 'specific model/scorer/context/support package', str(SPEC)),
    Card('I04', 'Raw surprise, individual benefit and attribution need not order events alike.',
         'Exact population and individual predictors on predictable signatures, absent individuality, noise and equifinality.', 'individual minus population held-out score',
         'independent constructed maker series', 'declared artifact/context budget', 'exact population predictor', 'known null and alternative per quantity', str(SPEC)),
    Card('I05', 'Borrowed methods are useful only when their defining operations actually execute.',
         'Separate released-anchor reproduction from independently checked operation adaptation.', 'defining operation versus disabled operation',
         'released task or exact operation fixture', 'matched operation inputs', 'independent exact implementation', 'one verdict per borrowed component', str(SPEC)),
    Card('I06', 'Explicit execution may help even when direct and executable routes receive the same operative information.',
         'Freeze common numeric state, rules and support; compare direct evaluation and execution; ablate information separately.', 'explicit versus direct use of identical operative inputs',
         'constructed world', 'explicit supplied-state diagnostic', 'direct model with identical numeric inputs', 'actual repaired scorer and kernel boundary', str(SPEC)),
    Card('C01', 'Prediction can fail specifically after the learner generates its own history.',
         'Score genuine, equally legal altered and generated prefixes at matched current states.', 'generated-history versus genuine-history next-action log score',
         'constructed maker series', 'declared prefix view and common support', 'capable population and matched-state genuine prefix', 'offered-choice apparatus; independent of broad-generation passage', str(SPEC)),
    Card('C02', 'Action choice, outcome production and termination can fail separately.',
         'Compare offered actions, free actions with environment outcomes and full generated logs; retain all attempts.', 'free action versus full log feasibility; stopping separate',
         'constructed maker series', 'same task context with assistance declared', 'exact executor and blind/story controls', 'operation-specific gates; retain original broad comparator', str(SPEC)),
    Card('C03', 'A useful local repair need not imply sustained generation competence.',
         'Predict unseen-edit consequences, propose and execute a repair, measure improvement and collateral damage.', 'prospective repair consequence gain over strongest cheap rival',
         'independent constructed fixable case', 'visible rules and current artifact', 'cheap repair and exact executor', '95 percent legal, 80 percent correct fixable, 5 percent collateral, .05 nats and positive interval', str(SPEC)),
    Card('C04', 'One-step accuracy can coexist with inconsistent longer process predictions.',
         'Finite-state compression and distinction tests, including longer distinguishing continuations.', 'equivalent versus distinguishable history consequences',
         'independent finite-state case', 'permitted histories and supported finite rules', 'exact finite executor', 'known equivalence/distinction truth; no stochastic theorem transfer', 'https://arxiv.org/html/2406.03689v3'),
    Card('C05', 'Training breadth and learner-state exposure can have different effects on competence.',
         'Two law coverages by expert versus learner-state mixture, two pinned bases, three seeds, matched supervision.', 'breadth effect, state-distribution effect and their interaction',
         'independent evaluation maker series; seeds are repeated fits', 'training-only sources and fixed evaluation views', 'old-recipe replay and base/reference adapters', '24 complete fits, actual collection, matching and operation gates', 'https://proceedings.mlr.press/v15/ross11a.html'),
    Card('C06', 'State resets can distinguish compounding failure from immediate inability.',
         'Horizons 1, 4, 8 and 16; compare uninterrupted generation with periodic genuine-state reset.', 'uninterrupted versus reset-assisted failure by horizon',
         'constructed maker series', 'matched task with reset assistance explicit', 'exact executor and immediate one-step error', 'supported action horizon; no assisted-to-unaided admission', str(SPEC)),
    Card('C07', 'Training-family fit may fail to transfer to withheld rules or parameter combinations.',
         'Narrow arms retain the second-family challenge; broad arms face withheld combinations and instances.', 'held-out transfer versus in-coverage competence',
         'held-out constructed maker series', 'same permitted task view', 'population reference on separately frozen expanded distribution', 'separate old and expanded population gates', str(SPEC)),
    Card('C08', 'Artifact projection can erase information that supports process operation.',
         'Pair finished outputs, partial artifacts and full logs on the same underlying series.', 'artifact versus process-record performance',
         'constructed maker series', 'separate explicit evidence views', 'strongest cheap rival within each view', 'view-specific reader capabilities and projection known answers', str(SPEC)),
    Card('M01', 'A model of this maker can predict another work beyond generic process knowledge.',
         'Compare population, cheap individual adaptation, executable program mixture and differentiated maker inference.', 'individual held-out score minus strongest budget-matched rival',
         'independent maker series', 'artifact, ordinary context and permitted earlier works', 'cheap individual adaptation and matched-other-maker history', 'relevant local capabilities; no global generation veto', str(SPEC)),
    Card('M02', 'Hypothesis coverage and hypothesis evaluation can independently limit prediction.',
         'Cross shared candidate pools and evaluators, then widen proposals beside an explicit known-support ceiling.', 'proposal expansion versus evaluator change at fixed budget',
         'independent maker series', 'identical permitted evidence and candidate pool within evaluator contrast', 'executable behavioral mixture', 'common support and resource envelope; oracle ceiling stays diagnostic', str(SPEC)),
    Card('M03', 'Uncertain purpose may help where premature purpose commitment harms.',
         'Compare no purpose, inferred distribution, single selection, true purpose and matched false purpose.', 'purpose mixture versus committed purpose and no-purpose baseline',
         'independent maker series', 'artifact primary; supplied true/false purpose separate', 'population and cheap purpose-conditioned predictor', 'realized purpose interventions and prospective scoring', str(SPEC)),
    Card('M04', 'Distinct earlier works may improve prediction even when surprise falls.',
         'Dose 0, 1, 3 and 7 distinct works, with wrong-maker and duplicate controls; predict a new work.', 'distinct same-maker history versus token-matched repetition',
         'independent maker series', 'permitted previous works only', 'cheap adaptation and matched-other-maker context', 'actual context capacity and real distinct source works', str(SPEC)),
    Card('M05', 'Calibrated ambiguity can remain useful without identifying a unique history.',
         'Identical-output/different-history cases followed by contexts that distinguish only some candidates.', 'equivalence-preserving predictive score versus forced point history',
         'independent equifinal maker-series set', 'artifact and later permitted context', 'exact compatible-history mixture', 'verified observational equivalence and separating continuation', str(SPEC)),
    Card('M06', 'Maker-specific predictive gain depends on decision freedom, constraint and artifact lossiness.',
         'Cross only existing supported manipulations and verify realized freedom before reader evaluation.', 'individual gain across verified constraint/projection cells',
         'independent maker series', 'artifact primary and separately labeled diagnostic views', 'capable population and cheap individual rival', 'constructor manipulation validity per cell', str(SPEC)),
    Card('T01', 'Purpose can persist when a familiar means is unavailable.',
         'Hold purpose fixed, remove a tool or operation and predict an alternative supported route.', 'adaptation prediction versus repeated surface technique',
         'constructed maker series', 'artifact plus verified changed context', 'persistent-technique and population predictors', 'one-factor realized tool intervention', str(SPEC)),
    Card('T02', 'Familiar authorship does not require surprising choices.',
         'Cross maker familiarity and expectedness; report recognition, gain and entry choice separately.', 'recognition and gain at low versus high surprise',
         'independent maker series', 'artifact and budget-matched earlier work', 'surface signature and population predictor', 'independent surprise and attribution known answers', str(SPEC)),
    Card('T03', 'An existing skill can be reused for a changed purpose.',
         'Keep an operation reusable, reverse its intended use and include unchanged-goal harder controls.', 'changed-goal reuse versus persistence and difficulty controls',
         'constructed maker series', 'same artifact and verified task context', 'persistence and generic-difficulty baseline', 'realized goal change without hidden extra intervention', str(SPEC)),
    Card('T04', 'Causally broad context can improve or damage prospective predictions more than local detail.',
         'Supply true, false and irrelevant cues with global or local causal reach.', 'prospective improvement or harm by cue truth and reach',
         'constructed maker series', 'source-identified context cue plus common artifact', 'context-free and reliability-aware cheap predictor', 'realized cue validity and same evidence budgets', str(SPEC)),
    Card('T05', 'Persistent signatures may belong to collaborators rather than the focal maker.',
         'Use only already supported mixed-control cases with separate maker and collaborator interventions.', 'focal-maker versus collaborator contribution',
         'supported mixed-control production series', 'permitted artifact and explicit role information', 'collaborator signature and population predictor', 'independently identifiable supported contrast; otherwise design note or descriptive', str(SPEC)),
    Card('T06', 'Later endorsement of a better move cannot identify why it was not taken earlier.',
         'Separate observed non-consideration, misvaluation, changed information and mere endorsement.', 'prospective discrimination among verified earlier-process conditions',
         'independent constructed decision series', 'permitted artifact and later evidence', 'endorsement-only story and population predictor', 'independently observed process condition; no retrospective inference from endorsement alone', str(SPEC)),
    Card('H01', 'Revision-pair access may improve human purpose-label recovery beyond the artifact alone.',
         'ArgRewrite canonical grouped labels, actual pairs and genuine later versions where present.', 'pair versus artifact recovery and genuine next-revision prediction',
         'document/version lineage', 'artifact or explicit actual pair', 'majority, prior-label and before/after lexical features', 'ArgRewrite real loader, multi-purpose and chronology gates', str(SPEC)),
    Card('H02', 'Evidence-view and domain transfer effects can be tested on genuine linked revisions.',
         'IteraTeR HUMAN and eligible arXivEdits; retain disagreement and actual successive versions.', 'view and cross-domain prospective prediction differences',
         'deduplicated paper/version lineage', 'artifact or actual revision pair', 'training prior and lexical difference baseline', 'separate human/model labels and cross-source duplicate audit', str(SPEC)),
    Card('H03', 'Earlier selections from a person may predict selections on another script.',
         'B-roll held-out script selection under the stated commission, preserving actual trial order where used.', 'person conditioning versus strongest matched selection baseline',
         'participant crossed with script', 'script, commission and permitted prior selections', 'POS, word preference, highlight budget and wrong-person histories', 'repeated-person/script structure and rights verified; Bernoulli selection score', str(SPEC)),
    Card('H04', 'A genetic edition can support a usable local reconstruction without complete historical recovery.',
         'Predict documented local changes from permitted text, retaining hand and transcription uncertainty.', 'bounded reader versus copied-text replacement prediction',
         'independent manuscript work', 'local artifact or documented revision view', 'copied text and famous-text familiarity', 'Shelley-Godwin then eligible Woolf; small work counts remain qualitative', str(SPEC)),
    Card('H05', 'Earlier finished drawings may predict another drawing beyond object and device.',
         'Use only a calibrated actual visual interface and permitted drawing features.', 'same-maker history versus object/device and wrong-maker rivals',
         'drawing maker crossed with object family', 'finished images; trace stays evaluator-only', 'object geometry, population drawing features and skill/device metadata', 'Drawings of THINGS access, source schema and visual measurement gates', str(SPEC)),
    Card('H06', 'Diff-based change-purpose recovery can transfer across repositories.',
         'Bounded permitted CommitBench slice, with repository-held-out prediction and nuisance controls.', 'cross-repository purpose prediction beyond lexical retrieval',
         'repository', 'sanitized diff under frozen view', 'message vocabulary, boilerplate, size, filenames and topic', 'complete acquired slice and rights; no individual accumulation without stable permitted maker IDs', str(SPEC)),
    Card('H07', 'Reconstructed writing state can support prospective suggestion-handling prediction.',
         'CoAuthor replay with real accept/edit/dismiss/ignore semantics and mixed agency retained.', 'artifact versus explicit-record next-handling prediction',
         'writer/session lineage', 'current document or explicit prior event record', 'action rate, previous decision and suggestion-quality proxies', 'actual document reconstruction and action semantics before modeling', str(SPEC)),
    Card('H08', 'Current drafts and prior revisions may predict the next recorded edit category or location.',
         'ScholaWrite and eligible NewsEdits 2.0 with grouped evaluation and exposure provenance.', 'prospective reader versus persistence and lexical difference',
         'paper/project or article/version lineage', 'current draft and permitted prior context', 'previous label and lexical-difference predictors', 'actual edition, sequence and split eligibility; retain below-baseline failures', str(SPEC)),
    Card('S01', 'Learning a technique and predicting a maker can justify different evidence choices.',
         'Compare acquisition and stopping objectives over the same permitted pool and cost.', 'objective-specific future gain at matched acquisition cost',
         'independent maker series', 'same permitted evidence pool', 'fixed and random acquisition', 'relevant capability and prospective objective-specific scoring', str(SPEC)),
    Card('S02', 'Entry heuristics can save effort without improving the eventual answer.',
         'Compare anomaly, signature, affordance, random and full-view entry at fixed budgets.', 'quality at fixed cost and cost to fixed quality',
         'independent maker series', 'same permitted observation pool', 'random and full-view entry', 'no extra evidence hidden in route construction', str(SPEC)),
    Card('S03', 'Consequential disagreement may select more useful evidence than uncertainty alone.',
         'Compare random selection, model entropy and disagreement about future actions.', 'realized future predictive gain per observation cost',
         'independent maker series', 'permitted existing observations or supported constructor contexts', 'random and entropy acquisition', 'selection cannot see withheld outcomes or acquire new human data', 'https://proceedings.mlr.press/v235/kleine-buening24a.html'),
    Card('S04', 'A reader can stop usefully only if it predicts the value of additional evidence.',
         'Predict uncertainty reduction and improvement before requesting another work or stopping.', 'predicted versus realized marginal improvement',
         'independent maker series', 'permitted prior evidence only at each decision', 'fixed budget and repeated-evidence confidence baseline', 'prospective freeze before acquisition; calibrated stopping', str(SPEC)),
    Card('B01', 'Confirmatory claims can be frozen without selecting on their reserve.',
         'Freeze zero to three exact packages, targets, rivals, scope, untouched reserve and one power-based size.', 'eligible versus ineligible discovery claim packets',
         'claim packet with independent reserve units', 'discovery/development only', 'strongest adversary and cheap comparator', 'exact identity and 90 percent planning power at .05 nats for family of three', str(SPEC)),
    Card('B02', 'Frozen claims must retain every reserve outcome.',
         'Execute selected confirmations once with frozen sample sizes and all required seed evidence.', 'prespecified confirmation contrast with Holm correction',
         'untouched independent reserve unit', 'frozen permitted view', 'frozen strongest rival', 'B01 identities; no claim replacement after reserve inspection', str(SPEC)),
    Card('B03', 'Final integrity requires fresh calculation after every scientific and repair output.',
         'Check source/data/adapter/split closure, live gates, counts, isolation and costs; recalculate selected statistics in a fresh process.', 'actual final calculations and provenance versus declared receipts',
         'final result and source artifact', 'evaluator-only closure', 'independent fresh-process calculation', 'after all science and repairs; never mere rehash as reproduction', str(SPEC)),
    Card('B04', 'The final packet must preserve failures, limits and unresolved decisions.',
         'Produce internal write-through, coverage/readiness maps, eight fixed case types and the next decision with a real objection.', 'complete scope versus missing or overstated evidence',
         'card, capability, substrate and preselected case type', 'final frozen evidence only', 'explicit absent case and not-run dispositions', 'B03 actual final integrity; no automatic next stage', str(SPEC)),
)

BY_ID = {card.key: card for card in CARDS}
OUTCOME_BANDS = ('IMPLEMENTATION INVALID', 'DESCRIPTIVE', 'PRACTICALLY SMALL', 'INCONCLUSIVE',
                 'COUNTEREVIDENCE', 'SUPPORT CANDIDATE', 'CONFIRMED WITHIN SCOPE', 'NOT RUN WITH REASON')


def validate_inventory():
    expected = {f'{prefix}{i:02d}' for prefix, count in [('I', 6), ('C', 8), ('M', 6), ('T', 6), ('H', 8), ('S', 4), ('B', 4)] for i in range(1, count+1)}
    if set(BY_ID) != expected or len(CARDS) != 42 or len({c.produces for c in CARDS}) != 42:
        raise ValueError('Stage 9 inventory missing cards or reusing produces')
    return {'cards': len(CARDS), 'unique_produces': 42, 'executable_manifest': False,
            'remaining': 'manually enumerate actual cells, null/alternative fixtures, measured runtimes and prerequisite verdict identities'}
