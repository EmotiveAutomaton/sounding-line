"""Bind prospective diary sources to the event–feeling atlas from ADM2.

Only the published dictionary and the original table header are interpreted.
The original-file digest authenticates the edition. This does not score data or
change the participants or cells of the frozen Week 8 split-half study.
"""
import csv
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from runners.stage14.common import atomic, filehash, read
from runners.drive.cards.week8_adm2 import data_root

DESTINATION = ROOT / 'results/phase_2_4_stage_15/WEEK8/ADM2_ATLAS_ROUTES.json'
# One documented example is sufficient for a source-level roster decision.
# Numeric endpoints and label maps are a separate, cell-specific binding.
EXAMPLES = {
    '0001': ('social_offline', 'angry', 'Duration of in-person contact, recorded in ordered categories.'),
    '0004': ('social_number', 'sadornot', 'Contact concerns the previous day. The release gives a separate yes/no sadness question and a conditional intensity item. Verify the yes/no codes before scoring.'),
    '0014': ('act_what', 'frightened', 'The activity is nominal. Each documented category is a separate exposure.'),
    '0015': ('learning_goal_achievement', 'pa', 'Both are daily reports. Achievement is an appraisal and the feeling is a three-item mean.'),
    '0022': ('what', 'tense', 'The event is the main work activity in the previous ten minutes. Any activity without a labelled value is void.'),
    '0026': ('social_media_pre', 'loneliness', 'The exposure is recorded app use in the hour before the prompt.'),
    '0028': ('criticism', 'sad', 'Criticism is perceived. The released item list gives nine response options without numeric endpoints. A feeling-occurrence fit requires a documented floor.'),
    '0033': ('avoid_activity', 'angry', 'Avoidance is reported on a graded scale.'),
    '0035': ('conflict', 'angry', 'Both questions are current ratings from zero to one hundred.'),
    '0037': ('cigs', 'angry', 'The event is a reported count since the previous survey.'),
    '0039': ('social_interaction', 'loneliness', 'Both are same-day graded reports.'),
    '0040': ('covid_support_others', 'stressed', 'Use the immediate stress item. Check the support item’s reference period before treating the pair as simultaneous.'),
    '0050': ('helping_binary', 'valence_mood', 'The provider identifies this as a second study burst. Establish cohort independence before counting it separately from member 0049.'),
    '0051': ('social_media_use', 'happy', 'The exposure is seconds of use in the half-hour before the probe. The outcome is one bipolar item.'),
    '0053': ('thins_exposure', 'anxious', 'This indicator names thinspiration-only exposure. Combined exposure has separate fields.'),
    '0061': ('interaction_type', 'connected', 'Feeling connected is its own descriptive construct. Channel and absence of an interaction have distinct codes.'),
    '0066': ('prevent_activity_stool', 'angry', 'Daily interference is yes/no. Both items use 99 for refusal, excluded before scoring.'),
}


def inspect(base, entries, rights, member, event, feeling, scope):
    slug = 'openesm-' + member
    record = entries[slug]
    if record['path'] != 'open/' + slug:
        raise ValueError('Unexpected source location for ' + slug)
    directory = (base / record['path']).resolve()
    info_path = (base / record['source']).resolve()
    info_path.relative_to(directory)
    info = read(info_path)
    dictionary = directory / 'DOCUMENTED_METADATA.json'
    meta = read(dictionary)
    features = {item['name']: item for item in meta['features']}
    release = rights.get(slug, {})
    licence = info.get('license') or info.get('licence')
    if isinstance(licence, dict):
        licence = licence.get('name')
    if record['status'] != 'held' or release.get('r48_class') != 'P' or not isinstance(licence, str) or not licence.strip():
        return dict(member=member, status='withheld', reason='This source lacks a reviewed held edition and reporting-terms card.')
    files = [f for f in info['local_files'] if f['path'].lower().endswith('_ts.tsv')]
    if len(files) != 1:
        return dict(member=member, status='void', reason='One original longitudinal table could not be identified.')
    file = (base / files[0]['path']).resolve()
    file.relative_to(directory)
    if filehash(file) != files[0]['sha256']:
        return dict(member=member, status='void', reason='Original table digest differs from the source receipt.')
    with file.open(encoding='utf-8-sig', newline='') as stream:
        header = next(csv.reader(stream, delimiter='\t'))
    dictionary_names = [item['name'] for item in meta['features']]
    required = ('id', event, feeling)
    if any(header.count(k) != 1 or dictionary_names.count(k) != 1 for k in required):
        return dict(member=member, status='void', reason='Original header or dictionary has an absent or repeated binding.')
    return dict(member=member, status='atlas catalogue', event=event, feeling=feeling,
                event_occasion=features[event]['assessment_type'], feeling_occasion=features[feeling]['assessment_type'],
                day_field_in_header=header.count('day') == 1,
                source_title=record['title'], licence=licence, dictionary_sha256=filehash(dictionary),
                source_sha256=files[0]['sha256'], reporting_terms_sha256=release['card_sha256'], scope=scope)


def main():
    base = data_root()
    entries = {r['slug']:r for r in read(base/'_registry/REGISTRY.json')['sources']}
    rights = {r['slug']:r for r in read(base/'_registry/REPORTING_R48_INDEX.json')['sources']}
    rows = [inspect(base, entries, rights, member, *items) for member, items in EXAMPLES.items()]
    held = entries['openesm-0075']
    if held['status'] == 'stopped':
        rows.append(dict(member='0075', status='withheld', reason='The archive stopped acquisition at the modified rights statement. Only the event and feeling metadata are available.'))
    output = dict(scope='Prospective ATL catalogue. One example per diary. These intake records add no cells or participants to the frozen ATL2 analysis.',
                  release='Source dictionaries, original headers and terms. No participant value or fitted result is returned.',
                  rows=rows)
    atomic(DESTINATION, output)
    print(sum(r['status']=='atlas catalogue' for r in rows), 'diaries entered', len(rows), 'source dispositions')


if __name__ == '__main__':
    main()
