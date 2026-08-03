"""Render a reading beside the artifact it came from, so a human can check it.

── WHY THIS EXISTS ───────────────────────────────────────────────────────────────────────────

The project's outputs have been JSON numbers, and the curator said the honest thing about that:
they could not personally validate them, so they could not fully trust a negative result derived
from them. That is not a limitation to accept. **It is an engineering problem, and this module is
the fix.**

A reading rendered against its artifact — every recovered decision beside the text it claims to
come from, every quote located and highlighted, every unlocatable quote marked as unlocatable —
can be checked by anyone who can read the artifact. That converts "trust the pipeline" into "look
at it", which is the only kind of trust worth having here.

It is also D-2, which the spec already required:

    D-2 — what does the demo output? Default: BOTH, with the numbers primary and the account
    clearly marked as illustration.

So the account is rendered, and it is rendered *marked* — visibly separated, labelled as feeding
no measurement, because it is the compelling part and it is the part with no severity check
behind it.

── WHAT THIS DELIBERATELY DOES NOT DO ────────────────────────────────────────────────────────

No score badge, no traffic light, no headline number. SPEC §5: the reading is the tuple. A report
that leads with one figure would reintroduce at the presentation layer exactly the defect that
C-18 introduced at the criterion layer.
"""

from __future__ import annotations

import html
import json
from dataclasses import asdict
from pathlib import Path

from soundingline.loop.run import LoopRun
from soundingline.measures.reading import Measurement, measure


def _esc(s: str) -> str:
    return html.escape(s or "")


def _bar(label: str, value: float, *, emphasis: bool = False) -> str:
    pct = max(0.0, min(1.0, value)) * 100
    cls = "bar-fill emph" if emphasis else "bar-fill"
    return (
        f'<div class="bar-row"><span class="bar-label">{_esc(label)}</span>'
        f'<span class="bar-track"><span class="{cls}" style="width:{pct:.1f}%"></span></span>'
        f'<span class="bar-val">{value:.2f}</span></div>'
    )


def _highlight(artifact_text: str, runs: list[LoopRun]) -> tuple[str, int, int]:
    """Artifact with every located evidence span marked. Returns (html, located, total)."""
    spans: list[tuple[int, int]] = []
    located = total = 0
    for run in runs:
        ev = [d.evidence for d in run.reading.decisions] + \
             [t.evidence for t in run.reading.trade_offs]
        for e in ev:
            total += 1
            hit = e.locate(artifact_text)
            if hit:
                located += 1
                spans.append((hit[0], hit[1]))

    # locate() works on a whitespace-collapsed copy, so offsets index that copy rather than the
    # original. Rebuild against the same normalisation so the highlight lands where the match did.
    import re
    norm = re.sub(r"\s+", " ", artifact_text).strip()
    merged: list[list[int]] = []
    for a, b in sorted(spans):
        if merged and a <= merged[-1][1]:
            merged[-1][1] = max(merged[-1][1], b)
        else:
            merged.append([a, b])

    out, cursor = [], 0
    for a, b in merged:
        a, b = max(a, cursor), min(b, len(norm))
        if a >= b:
            continue
        out.append(_esc(norm[cursor:a]))
        out.append(f'<mark>{_esc(norm[a:b])}</mark>')
        cursor = b
    out.append(_esc(norm[cursor:]))
    return "".join(out), located, total


def _decisions_table(run: LoopRun, artifact_text: str) -> str:
    if not run.reading.decisions:
        return ('<p class="empty">No decisions recovered. Under SPEC §4 that is a reading, not a '
                'failure — it says nothing in the artifact showed a maker choosing one thing over '
                'an available alternative.</p>')
    rows = []
    for d in run.reading.decisions:
        hit = d.evidence.locate(artifact_text)
        if hit:
            badge = f'<span class="ok">located · {hit[2]:.2f}</span>'
        else:
            badge = '<span class="bad">NOT IN ARTIFACT</span>'
        alt = _esc(d.alternative_rejected) or \
            '<span class="bad">none named — not a decision</span>'
        rows.append(
            f'<tr><td class="lvl">L{d.level}</td>'
            f'<td><div class="chose">{_esc(d.what_was_chosen)}</div>'
            f'<div class="notchose">instead of: {alt}</div>'
            f'<div class="quote">&ldquo;{_esc(d.evidence.quote)}&rdquo; {badge}</div></td></tr>'
        )
    return f'<table class="decisions">{"".join(rows)}</table>'


CSS = """
:root { color-scheme: light dark; }
* { box-sizing: border-box; }
body { font: 15px/1.55 ui-sans-serif, system-ui, -apple-system, Segoe UI, sans-serif;
       margin: 0; padding: 2rem 1.5rem 4rem; max-width: 1180px; margin-inline: auto;
       background: #fbfbfa; color: #1c1c1a; }
h1 { font-size: 1.45rem; margin: 0 0 .2rem; letter-spacing: -.01em; }
h2 { font-size: .82rem; text-transform: uppercase; letter-spacing: .09em; opacity: .55;
     margin: 2.2rem 0 .7rem; font-weight: 600; }
.sub { opacity: .6; font-size: .85rem; margin-bottom: 1.6rem; }
.grid { display: grid; grid-template-columns: 1fr 1fr; gap: 1.6rem; }
@media (max-width: 860px) { .grid { grid-template-columns: 1fr; } }
.card { background: #fff; border: 1px solid #e6e4df; border-radius: 10px; padding: 1.1rem 1.2rem; }
.artifact { white-space: pre-wrap; font: 13.5px/1.7 ui-monospace, SFMono-Regular, Menlo, monospace;
            max-height: 30rem; overflow: auto; }
mark { background: #ffe9a8; padding: .06em 0; border-radius: 2px; }
.bar-row { display: flex; align-items: center; gap: .6rem; margin: .3rem 0; font-size: .84rem; }
.bar-label { flex: 0 0 11rem; opacity: .75; }
.bar-track { flex: 1; height: 7px; background: #eceae4; border-radius: 4px; overflow: hidden; }
.bar-fill { display: block; height: 100%; background: #8a8f98; }
.bar-fill.emph { background: #c2703c; }
.bar-val { flex: 0 0 2.6rem; text-align: right; font-variant-numeric: tabular-nums; opacity: .7; }
table.decisions { width: 100%; border-collapse: collapse; }
table.decisions td { border-top: 1px solid #eeece7; padding: .65rem .3rem; vertical-align: top; }
td.lvl { width: 2.4rem; font-weight: 600; opacity: .5; font-size: .8rem; }
.chose { font-weight: 550; }
.notchose { opacity: .7; font-size: .88rem; margin-top: .15rem; }
.quote { font-size: .82rem; opacity: .62; margin-top: .35rem; font-style: italic; }
.ok { color: #2f7d4f; font-style: normal; font-size: .74rem; }
.bad { color: #b3401f; font-style: normal; font-size: .74rem; font-weight: 600; }
.empty { opacity: .6; font-size: .9rem; }
.note { font-size: .82rem; opacity: .7; border-left: 3px solid #ddd9d0; padding-left: .8rem;
        margin: .8rem 0; }
.account { background: #f6f4ef; border: 1px dashed #d9d5cb; border-radius: 8px; padding: .9rem 1rem;
           font-size: .9rem; }
.tag { display: inline-block; font-size: .68rem; letter-spacing: .07em; text-transform: uppercase;
       background: #efece5; border-radius: 3px; padding: .12rem .42rem; opacity: .7; }
@media (prefers-color-scheme: dark) {
  body { background: #16161a; color: #e8e6e1; }
  .card { background: #1e1e23; border-color: #303038; }
  .bar-track { background: #2b2b32; }
  mark { background: #6b5410; color: #fdf3d6; }
  .account { background: #201f24; border-color: #3a3942; }
  .tag { background: #2a2a31; }
  table.decisions td { border-color: #2a2a31; }
}
"""


def render(runs: list[LoopRun], artifact_text: str, artifact_id: str) -> str:
    """One artifact, k readings, rendered so a person can check the instrument's work."""
    m: Measurement = measure(runs, artifact_text)
    hl, located, total = _highlight(artifact_text, runs)
    r0 = runs[0].reading

    purpose_bars = "".join(
        _bar(k, v, emphasis=(k == r0.purpose.best))
        for k, v in sorted(r0.purpose.distribution.items(), key=lambda x: -x[1])
    )
    audience_bars = "".join(
        _bar(k, v, emphasis=(k == "machine"))
        for k, v in sorted(r0.audience.distribution.items(), key=lambda x: -x[1])
    )
    traj = " → ".join(f"{s.movement:.2f}" for s in runs[0].trajectory[1:]) or "—"

    return f"""<!doctype html><meta charset="utf-8">
<title>Reading · {_esc(artifact_id)}</title><style>{CSS}</style>
<h1>{_esc(artifact_id)}</h1>
<div class="sub">{len(runs)} independent reconstructions · {_esc(runs[0].arm)} ·
{_esc(runs[0].model)} · family v2</div>

<div class="note"><strong>There is no overall score here, and there is no longer one to
render.</strong> `fit` used to aggregate three components into a single number; each of the three
turned out to be measuring the wrong object, and the aggregate ranked the richest artifact in the
Gate 1 set dead last while four other dimensions ranked it first. SPEC §5 had already said why:
<em>the reading is the tuple &mdash; a single number invites the overclaim.</em> Artifacts are
compared by dominance now, and ones that trade off against each other are reported as
incomparable.</div>

<h2>The artifact, with everything the probe claimed to see</h2>
<div class="card artifact">{hl}</div>
<div class="note">{located} of {total} evidence quotes were located in the text and are
highlighted. Quotes that could not be located are listed below and marked — those are the
fabrication signal, and they are the first thing to check.</div>

<div class="grid">
  <div>
    <h2>What was it for</h2>
    <div class="card">{purpose_bars}</div>
    <h2>Who was it for</h2>
    <div class="card">{audience_bars}
      <div class="note" style="margin-bottom:0">Highlighted bar is <code>machine</code> — made to
      be ingested rather than read. It is a hypothesis with a probability, never a claim about who
      wrote this.</div>
    </div>
  </div>
  <div>
    <h2>Measures</h2>
    <div class="card">
      {_bar("grounding", m.fit.grounding)}
      {_bar("support", m.fit.support)}
      {_bar("recovery", m.fit.recovery)}
      {_bar("purpose breadth", m.purpose_breadth)}
      {_bar("purpose agreement", m.convergence.purpose_agreement)}
      {_bar("audience agreement", m.convergence.audience_agreement)}
      {_bar("confident disagreement", m.convergence.confident_disagreement, emphasis=True)}
      <div class="note" style="margin-bottom:0">
        depth reached <strong>L{m.depth.max_level}</strong> across
        {m.depth.levels_reached} level(s), {m.depth.n_decisions} decisions,
        {m.depth.per_1k_chars:.1f} per 1k chars ({m.depth.artifact_chars} chars) ·
        artifact effort {r0.artifact_effort}, demonstrated work {r0.demonstrated_work} ·
        posterior movement per iteration {traj}
      </div>
    </div>
  </div>
</div>

<h2>Decisions recovered — sample 0</h2>
<div class="card">{_decisions_table(runs[0], artifact_text)}</div>

<h2>The account <span class="tag">illustration only — feeds no measurement</span></h2>
<div class="card account">{_esc(r0.account) or "<em>none given</em>"}</div>
<div class="note">D-2: the numbers are the measurement; this is the pointable part and it has no
severity check behind it. It is rendered separately for that reason and must never be quoted as a
result.</div>
"""


def write_reports(runs_by_item: dict[str, tuple[list[LoopRun], str]], out_dir: Path) -> list[Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    written = []
    for item, (runs, text) in runs_by_item.items():
        if not runs:
            continue
        p = out_dir / f"{item}.html"
        p.write_text(render(runs, text, item), encoding="utf-8")
        written.append(p)
    return written
