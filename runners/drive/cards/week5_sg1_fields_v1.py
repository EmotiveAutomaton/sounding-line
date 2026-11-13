"""SG1 game and session fields; no engine or identity-bearing output.

DESIGN CHECK: independently authored examples must fail a shared wrong parser.
The previous CH7 payload is preserved exactly, including its -1/0/1 result.
New score is explicitly 0/.5/1. Missing clocks never become observed time.
"""
from collections import defaultdict
import hashlib
import json
import math
import re

import chess

from . import week5_ch_source as source
from . import week5_ch7_source_v1 as ch7

CH7_COLUMNS = ('game', 'month', 'start', 'end', 'initial', 'increment',
               'time_control', 'rating_change', 'result', 'first_clock',
               'rows', 'rating', 'opponent_rating', 'source_ordinal')
SESSION_COLUMNS = ('session_id', 'index_in_session', 'seconds_to_next', 'stop',
                   'rematch', 'censored', 'provisional_session',
                   'session_field_status')
TOURNAMENT = re.compile(r'https?://(?:www\.)?lichess\.org/tournament/([A-Za-z0-9_-]+)')


def header_fields(text, salt):
    headers = dict((m[1], m[2]) for line in text.splitlines()
                   if (m := source.HEADER.match(line)))
    event = headers.get('Event', '')
    match = TOURNAMENT.search(event)
    tournament = bool(match or re.search(r'\btournament\b', event, re.I))
    return dict(tournament=tournament,
                tournament_id=source.pseudonym('tournament:' + match[1], salt) if match else None,
                termination=headers.get('Termination'))


def duration(rows, meta, termination):
    """Clock-based estimate, excluding each unmeasured first-move latency.

    First clock is an observed effective starting bank. It is not subtracted
    from nominal initial time: doing so would count a berserk reduction as time.
    Increment controls with a subinitial first clock are ambiguous and missing.
    """
    by_side = [[r for r in rows if r['side'] == side] for side in (0, 1)]
    if not all(by_side):
        return None, 'missing_side_moves'
    total = 0.
    for moves in by_side:
        clocks = [r['clock_after'] for r in moves]
        if any(v is None or not math.isfinite(v) or v < 0 for v in clocks):
            return None, 'missing_or_invalid_clock'
        if meta['increment'] and clocks[0] < meta['initial']:
            return None, 'increment_or_clock_reduction_ambiguous'
        for before, after in zip(clocks, clocks[1:]):
            elapsed = before - after + meta['increment']
            if elapsed < 0:
                return None, 'negative_clock_difference'
            total += elapsed
    if termination == 'Time forfeit':
        loser = 1 if meta['result'] == '1-0' else 0 if meta['result'] == '0-1' else None
        if loser is None:
            return None, 'forfeit_without_decisive_result'
        total += by_side[loser][-1]['clock_after']
    return total, 'clock_estimate_excludes_two_first_move_latencies'


def project(text, month, ordinal, prior_payload, salt):
    """Extend one authenticated source game, retaining every CH7 column."""
    old = json.loads(prior_payload)
    meta, reason = source.decode_headers(text, salt)
    if reason or meta != old['meta']:
        raise ValueError('Raw header does not reproduce authenticated history')
    rows, dispositions, first = source.parse_game(text, meta)
    chosen = {r['player'] for r in old['rows']}
    if ([r for r in rows if r['player'] in chosen] != old['rows'] or
            first != old['first_clocks'] or dispositions != old['dispositions']):
        raise ValueError('Raw moves do not reproduce authenticated history')
    extras = header_fields(text, salt)
    estimate, duration_status = duration(rows, meta, extras['termination'])
    final = chess.Board(rows[-1]['fen']) if rows else chess.Board()
    if rows:
        final.push_uci(rows[-1]['uci'])
    white_material = sum(weight * (len(final.pieces(piece, chess.WHITE)) -
                                  len(final.pieces(piece, chess.BLACK)))
                         for piece, weight in ((chess.PAWN, 1), (chess.KNIGHT, 3),
                                               (chess.BISHOP, 3), (chess.ROOK, 5),
                                               (chess.QUEEN, 9)))
    side_rows = [[r for r in rows if r['side'] == side] for side in (0, 1)]
    for player, value in ch7.projected(month, ordinal, prior_payload):
        side = meta['players'].index(player)
        own, opponent = side_rows[side], side_rows[1-side]
        # Use the actual first ply's clock for new measurements. The old CH7
        # first_clock remains unchanged even if the first comment was missing.
        own_first = own[0]['clock_after'] if own else None
        other_first = opponent[0]['clock_after'] if opponent else None
        ratio = own_first / meta['initial'] if own_first is not None else None
        value.update(extras)
        value.update(player=player, opponent_key=meta['players'][1-side],
                     colour='white' if side == 0 else 'black',
                     opponent_rating_change=meta['rating_changes'][1-side],
                     plies=len(rows), own_first_clock=own_first,
                     opponent_first_clock=other_first,
                     own_last_clock=own[-1]['clock_after'] if own else None,
                     opponent_last_clock=opponent[-1]['clock_after'] if opponent else None,
                     duration_est=estimate, duration_status=duration_status,
                     own_first_move=own[0]['uci'] if own else None,
                     opponent_first_move=opponent[0]['uci'] if side == 1 and opponent else None,
                     last_move_checkmate=bool(rows and final.is_checkmate()),
                     final_material_balance=white_material if side == 0 else -white_material,
                     score=None if value['result'] is None else (value['result'] + 1) / 2,
                     first_clock_ratio=ratio,
                     berserk_candidate=(extras['tournament'] and meta['increment'] == 0 and
                                        ratio is not None and .45 <= ratio <= .55),
                     berserk_instrument_admitted=False)
        yield player, value


def session_rows(games, gap=1800):
    """One player's complete three-month history; no outcome-dependent selection."""
    groups = defaultdict(list)
    output = []
    for game in games:
        row = dict(game)
        if row['start'] is None:
            row.update({key: None for key in SESSION_COLUMNS})
            row['session_field_status'] = 'missing_start'
            output.append(row)
        else:
            groups[(row['time_control'], row['month'])].append(row)
    for key in sorted(groups):
        ordered = sorted(groups[key], key=lambda r: (r['start'], r['game']))
        sessions = []
        for row in ordered:
            if not sessions or row['start'] - sessions[-1][-1]['start'] >= gap:
                sessions.append([])
            sessions[-1].append(row)
        index = 0
        for session in sessions:
            sid = hashlib.sha256(('SG1-session|' + session[0]['player'] + '|' +
                                  '|'.join(key) + '|' + session[0]['game']).encode()).hexdigest()
            provisional = any(r['rating_change'] is not None and abs(r['rating_change']) > 25
                              for r in session)
            for number, row in enumerate(session, 1):
                following = ordered[index+1] if index+1 < len(ordered) else None
                censored = following is None
                seconds = None if censored else following['start'] - row['start']
                same = not censored and seconds < gap
                row.update(session_id=sid, index_in_session=number,
                           seconds_to_next=seconds, stop=None if censored else not same,
                           rematch=None if censored else same and row['opponent_key'] == following['opponent_key'],
                           censored=censored, provisional_session=provisional,
                           session_field_status='observed_start_gap_month_censored')
                output.append(row)
                index += 1
    return sorted(output, key=lambda r: (r['month'], r['game']))


def histogram(rows):
    """SG1.v data only; the two-mode scientific check is a separate review gate."""
    result = {name: dict(bins=[0]*20, in_band=0, denominator=0, missing=0, outside=0)
              for name in ('tournament', 'other')}
    for row in rows:
        if row['increment'] != 0:
            continue
        group = result['tournament' if row['tournament'] else 'other']
        ratio = row['first_clock_ratio']
        if ratio is None:
            group['missing'] += 1
            continue
        group['denominator'] += 1
        group['in_band'] += int(.45 <= ratio <= .55)
        if 0 <= ratio <= 1:
            group['bins'][min(19, int(ratio*20))] += 1
        else:
            group['outside'] += 1
    return result
