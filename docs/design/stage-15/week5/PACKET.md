# Sounding Line, Stage 15, week 5 (7 to 15 November): a full machine, aimed at the engine

*Spec sheet for the Sounding Line agent. It runs from handoff to Sunday 15 November, 22:00 PST (2026-11-16T06:00Z). Every decision is made here. Return to the curator only on the triggers in section 9. As of Saturday 7 November 2026, written against `origin/main` at `dcbcc26de`.*

**What this week is for.** Two things, in this order.
1. **Keep the machine full.** By this repository's own count, its four research slots sat unused for 388 of about 456 slot-hours from 2 to 7 November. The causes were the packets' rules and the turn structure, not the science (lessons below). Section 0.3 changes the rules, section 0.4 doubles the slots, and section 2 supplies work that can fill them for a week.
2. **Aim every program at ToMpathy's engine.** The engine's first flight is panels one and two (current attention; expertise flowing toward goals) shown correctly on any piece found on the internet, with panel three (core values) after. So:
   - the attention family (AT) validates panel one's attention marks against keystrokes, including the engine's own departure models;
   - the chess family (CH) tests decision time as a marker of a hard choice and of expertise, where a chess engine supplies ground truth;
   - the goals family (GO) gives the top of the engine its first real ground truth: authors' own stated goals;
   - five families test the curator's 7 November theory answers on public data: a channel's intensity (IN), comfort set points (SP), mood (MD), laughter (LA) and an identity mark in moral choices (ID);
   - the backlog family (BK) runs Week 4's held and never-started work.

**Lessons this packet is built on** (Week 4 and the theory days; quotes are this repository's):
- **No build wakes.** With nothing running, the agent woke only for six-hourly health checks, the 20:00 digest or the curator. AGENTS.md says "Do not schedule routine liveness/ETA wakes ... or invoke an agent merely because work remains", and health turns inspected without building. Amendment I fixes this.
- **Builders unused.** The 17 October packet made itself the explicit per-task request AGENTS.md requires ("This packet is that request") and allowed three card builders, and Weeks 3 and 4 kept its section 2 in force. No builder was ever started: every record closes with no delegation. Amendment J makes builders mandatory, and section 3 assigns them.
- **Readiness meant full admission.** A card counted as ready only after its design note, tests, native fixture, timing prefix, cost probe and pinned plan. 216 frozen plans and 312 records produced 23 Week 4 science rows, and the buffer read 0 of 8 at every digest. Amendment K fixes this.
- **Ceilings too small, and split inside cards.** One card was held because its source-sample replay forecast ran 20.55 seconds over a source sub-allocation, while 1,800 seconds of its analytical reserve sat unused (S2). Its successor then missed by 1.6 seconds. Four more cards were held because 2,000-resample refits with margins of 1.5 to 3 times didn't fit (T4, WD1, D7, PP3.p1), and two because verification hit the 7,200-second cap (CA1, WB1). Amendment L fixes this.
- **Floors and gates without fallbacks.** Five cards closed as "design cannot test" on support counts (S5, S4(a), T3, V3, TD7); one provider refusal sank a whole paid value-coding collection (VAL); and second failed rungs stopped three paid coders (PROC, PLAN, REV). Amendment M fixes this, and this week has no paid coders.
- **Sources.** Dryad refused downloads, holding the three Rutledge mood cards (TD1 to TD3). The same files are on Zenodo, byte-identical (section 0.5).

## 0. How to run this

### 0.1 Window and campaign

- **Names.**
  - Campaign `S15-WEEK5`.
  - Shelf `docs/design/stage-15/week5/`, with this packet at `docs/design/stage-15/week5/PACKET.md`.
  - Policy `runners/drive/cards/week5_policy.py` and calendar `runners/drive/calendar_20261107_week5.py`.
  - Ledger rows `S15-W5-<card>-<n>`; results under `results/phase_2_4_stage_15/WEEK5/`.
- **Policy is new code.** Write `week5_policy.py` with its own clock. Don't clone `runners/theory_days/policy.py`: it inherits Week 4's no-new-start boundary and would refuse every start after 2026-11-09T04:00Z.
- **Clock** (UTC):
  - opens at handoff;
  - no new starts after Sunday 15 November, 20:00 PST (2026-11-16T04:00Z);
  - drain by 22:00 PST (2026-11-16T06:00Z);
  - final digest at 20:00 PST; drain addendum by 23:00 PST (2026-11-16T07:00Z).
- **Concurrency.** Week 5 opens while Week 4 (drain Sunday 8 November, 22:00 PST) and the theory days (no new starts after 7 November, 19:00 PST; drain 8 November, 07:00 PST) are still open.
  - Their cards keep first claim on the original four leases until their drains.
  - Week 5 uses the leases section 0.4 adds, plus any of the original four that sit idle.
  - Neither campaign borrows the other's budget.
- **`transition_only`.** Only the drain of the last open campaign restores it. Don't edit or restart the Week 4 and theory-days calendars: each loaded and pinned its code at start, so an edited file changes nothing while it runs, and AGENTS.md says "Never restart valid work to refresh reports or monitoring clocks." Instead, Week 5's calendar reads `.agent-state/watch.json` on every tick and, while Week 5 is open, sets `transition_only` back to false within one tick of an older calendar setting it true (the theory days at 2026-11-08T15:00Z, Week 4 at 2026-11-09T06:00Z), logging each reset in OPS_LOG. Planned check-ins fire only while it is false.

### 0.2 Rules in force

Everything in force at the end of Week 4 stays:
- the stone rules: Gear 3 per-use approval and the $10 ceiling enforced in code; material spend only behind positive results; hash-locked files; no author contact; privacy; a null that can fail every measure; every result descriptive;
- amendments A to H;
- Week 4's identification controls (§0.4, the three-role independent-donor reference).

Section 0.3 adds five permanent amendments. Where one conflicts with an older sentence, the amendment wins, and the older sentence gets a pointer to it.

### 0.3 Standing amendments, 7 November (permanent)

Write these at handoff into `AGENTS.md` and `.agents/skills/grind/SKILL.md`, in a section headed "Standing amendments, 7 November".

**I. Build wakes.**
- While any card of an open campaign is unbuilt, unadmitted, ready or running, keep one check-in at most 60 minutes ahead.
- This carries out the 17 October row 4 rule. For those windows it overrides AGENTS.md's "Do not schedule routine liveness/ETA wakes, continue from a Stop hook, recurse through a queue rule, or invoke an agent merely because work remains" and the grind skill's "Do not add separate ETA wakes".
- A health turn that finds unbuilt work builds. While work is unbuilt, inspection alone doesn't complete a turn.
- Building section 2's cards at a check-in is implementing this packet's designs, not new research design.

**J. Builders.**
- This packet, and any later packet that lists builder assignments, is the explicit per-task delegation request AGENTS.md requires.
- Keep three card builders (subagents) running from handoff while any card in section 2 is unbuilt, on section 3's assignments. A builder that finishes takes the next unbuilt card in dispatch order. A turn that ends with unbuilt cards and fewer than three builders running records the cause in OPS_LOG.
- The owner (the Codex operating session) reviews each builder's design note and fixture before admission, as now.

**K. Ready means designed and fixtured.**
- A card is ready, and counts toward amendment A's buffer, once its design note (with its DESIGN CHECK block) is committed and its native fixture has passed.
- Its cost probe, timing prefix and any pilot run inside a counted slot, as the first stage of its run, charged to the card.
- A forecast over 7,200 CPU-seconds is met by a checkpointed in-slot pilot covering the first 5% of the work, not by a separate pilot card.
- One design note and one fixture admit a family's pipeline and its declared grid. Each grid cell is then ready.

**L. Ceilings sized to the work.**
- (a) Each card has one CPU ceiling, given in section 2. Nothing inside a card holds a separate sub-allocation.
- (b) Amendment E's sample route and S4's one doubling stay. But a card past its doubling continues under its family ceiling, checkpointed, whenever a counted slot is idle; it doesn't hold.
- (c) Uncertainty:
  - screening runs and texture cells use 200 cluster resamples;
  - primaries, and anything entering the ledger as "supported" or "against", use 2,000;
  - a texture cell whose 200-resample interval crosses its bar may rerun at 2,000 as a precision follow-up.
- (d) A reservation never blocks a start while a counted slot is idle and the family ceiling has room.
- (e) Texture cells keep amendment G's 1 CPU-hour cap, except cells that rescore or reanalyse (CH2's node counts, AT2's context lengths, LA1's preceding-act counts), which take up to a quarter of their parent card's ceiling from the family ceiling. CH2's node-count cells, whose parent ceiling leaves analysis aside, instead re-analyse a 25,000-position subset of CH1's sample within 200,000 CPU-seconds of CH's family ceiling.

**M. Fallbacks and lanes.**
- (a) Every support floor, whether stated in section 2 or added in a design note, has a declared descriptive fallback. A card with no stated floor uses 20 clusters of its unit as its floor and a pooled descriptive fit as its fallback. The fallback runs automatically when the floor fails and is reported "below floor, descriptive".
- (b) A collection gate tolerates refusals or parse failures up to 1% of items, and reports them.
- (c) A texture lane stops after seven consecutive cells whose estimates lie inside the parent's practical band around zero (between minus and plus its bar). For Week 5's grids this replaces amendment G's five-similar stop. The curator's 14 October stopping rule, recorded in `docs/design/stage-15/SOUNDING_LINE_NEXT_ROUND_SPEC_2026-10-14.md` as "stop a family after about five to seven null batches, not two", governs families of primaries and stays as the 17 October packet's six-null family stop.
- (d) Follow-ups may run two generations deep within a week. A positive, or any result outside its parent's interval, may register descendants from amendment C's menu.
- (e) A failed source moves its cards to the next fallback in section 0.5. It never holds a slot.

### 0.4 Capacity

- **Slots.** Week 5 adds four counted leases, `slot-4` to `slot-7`, in a new folder, `results/.cpu-slots-20261107/`, beside the existing four in `results/.cpu-slots-20261017/`, for up to 8.
  - Week 5's runtime needs its own claim function. `batch_runtime_v8.claim` tries only `range(slot_count())`, slots 0 to 3, and refuses once four `slot-*.json` files exist in its folder, so it can't be reused as the theory days reused it.
  - Week 5 counts leases in both folders against 8, takes an original lease only when it is idle, and writes nothing into the old folder but `slot-0` to `slot-3`. A Week 5 lease in the old folder would make Week 4's and the theory days' admission refuse every start.
  - Each slot runs at most 2 numerical threads, at below-normal priority.
  - The host has 24 logical processors, so Sounding Line uses at most 16 threads. Ghost runs up to 4 single-thread workers under its own packet, which leaves 4 for the system, the agents and Ollama.
  - This overrides the 17 October slot formula (4 at 12 or more logical processors) for Week 5's window.
- **Memory and disk.**
  - Week 4's floors stay: refuse a start below 6 GiB free RAM, 8 GiB commit headroom or 20 GiB free disk, and yield below 4, 6 and 20.
  - Every card declares `projected_peak_ram_GiB`. At each start, the new card's declared peak, plus each running card's declared peak less its current use (floored at zero), stays at least 8 GiB below free RAM.
  - ToMpathy's lock rule is unchanged.
- **CPU.** The campaign allowance is 6,000,000 CPU-seconds, about 1,667 CPU-hours: half the 16 threads' wall time over the window, so it binds only if work runs hot. Family ceilings are in section 2. If the total would pass, shed texture before primaries, and primaries in the reverse of section 3's order.
- **None this week:**
  - no GPU work (D10 stays parked);
  - no paid work and no Gear 3 campaign;
  - no Ollama calls from Week 5 cards.

### 0.5 Sources, installs and pins

This is the network lane, under `docs/design/stage-15/theory-days/DATA_INTAKE.md`'s rules: a missing field, an ambiguous licence, a changed hash or an unsafe archive path refuses. Each source's first step is a retrieval check, run at handoff. On failure, its cards move to the fallback, never to a hold.

**Installs** (pin each at first download, and record the version and SHA-256, and each model card's licence, in the intake record):
- Stockfish 19, tag `sf_19`, from the official GitHub release (Windows x86-64 universal zip). GPL v3: run it, and don't commit the binary.
- From PyPI: `chess==1.11.2` (python-chess) and `py7zr`, each pinned at first download. Read `.zst` with pyarrow, as B4 did.
- Hugging Face model weights, each pinned to the commit hash recorded at first download:
  - `openai-community/gpt2`, `gpt2-medium` and `gpt2-large`;
  - `EleutherAI/pythia-70m-deduped`, `-160m-deduped`, `-410m-deduped`, `-1b-deduped` and `-1.4b-deduped`;
  - `HuggingFaceTB/SmolLM2-360M` and `Qwen/Qwen2.5-0.5B` (the engine's two departure models);
  - `distilbert/distilroberta-base`, for LA1;
  - the CA1 encoder stays at revision `e8f8c211`.
- The HF cache already holds Qwen2.5-0.5B, gpt2-medium, gpt2-large, pythia-410m, pythia-1.4b (not deduped) and SmolLM2-360M (TOOLS.md). If Hugging Face refuses, AT2 runs on those.

Week 5's intake bounds: 35 GiB per Lichess file (as `runners/drive/intake.py`), 4 GiB per model file, 2 GiB per Stack Exchange archive, and the 50 GiB free-disk download floor. Requests name the project in the User-Agent, not a browser string.

**Sources:**

| Source | Cards | Licence | Route | Pin or check | Fallback |
|---|---|---|---|---|---|
| Rutledge risk and happiness data | MD1 to MD3 | CC0 | `https://zenodo.org/api/records/4421847/files/README_Rutledge_GBE_risk_data.md/content` and `.../Rutledge_risk_and_happiness_task_2023.zip/content` | The SHA-256s already pinned in `runners/theory_days/intake.py`: README `528ff1c9...a78c`, zip `45685917...2168`. The analyst downloaded both Zenodo files on 7 November; they are byte-identical to the Dryad files the intake pins | Zenodo record 4421847 first; otherwise the curator's local copy, under `data/external/rutledge_gbe/` (the 7 November data guide's path; `data/external/` isn't in `.gitignore` at `dcbcc26de`, so add it before any git add; the guide's paste text asks Codex to confirm it's there) or `corpora/store/external/rutledge_gbe/` (already gitignored), read through the intake's local-copy path. Dryad is not a script route (401/403) |
| Jangraw et al. 2023 mood-drift archive, OSF `km69z` | MD4 | NIMH public-domain notice in the archive's LICENSE; OSF field blank | `https://osf.io/download/6bwqj/?version=2` | SHA-256 `f1c470a3...fd4` | Held until the curator's message to Codex accepts the notice. No slot waits for it |
| Lichess standard rated games | CH | CC0 | `https://database.lichess.org/standard/lichess_db_standard_rated_YYYY-MM.pgn.zst` for 2017-05 and 2017-06 (2017-04 and 2026-07 are on disk; 2026-07 is the recent month) | Published `sha256sums.txt`, as `runners/drive/intake.py` already does | The months already on disk (2017-04; 2026-07) |
| Lichess puzzles | CH1's known answers | CC0 | `https://database.lichess.org/lichess_db_puzzle.csv.zst` | Record SHA-256 | None needed |
| Crowd-enVENT | IN | CC BY 4.0, from the LICENSE.txt inside the zip (dated 2026-11-02) | `https://www.romanklinger.de/data-sets/crowd-enVent2023.zip` | Record SHA-256; generation table 6,600 rows, validation table 6,000 rows | None |
| ASHRAE Global Thermal Comfort Database II v2.1 | SP | CC BY 4.0 as the licence of record (Dryad states CC0, its Zenodo mirror CC BY 4.0; the GitHub repository has no LICENSE file). Cite Földváry Ličina et al. 2018. | Zenodo record 4993952 first; GitHub `CenterForTheBuiltEnvironment/ashrae-db-II` raw files second. | Record SHA-256; 109,033 measurement rows | The other route |
| AMI Meeting Corpus annotations | LA | CC BY 4.0 | `https://groups.inf.ed.ac.uk/ami/AMICorpusAnnotations/ami_public_manual_1.6.2.zip` (22.9 MB; no audio) | Record SHA-256 | ICSI alone |
| ICSI Meeting Corpus annotations | LA | CC BY 4.0 | `https://groups.inf.ed.ac.uk/ami/ICSICorpusAnnotations/ICSI_core_NXT.zip` and `ICSI_plus_NXT.zip` | Record SHA-256 | AMI alone |
| Python PEPs | GO | Per PEP; most read "placed in the public domain" or CC0. Record each PEP's statement, and exclude any without one | `git clone https://github.com/python/peps` | Record the head commit | EIPs alone |
| Ethereum EIPs | GO | CC0 (LICENSE.md) | `git clone https://github.com/ethereum/EIPs`. ERCs moved to `ethereum/ERCs` (also CC0): clone it too, or recover ERCs from the EIPs history before the move | Record the head commit | PEPs alone |
| Stack Exchange data dump, 2024-04 | GO3 | CC BY-SA 3.0 per license.txt in the item (the item description says CC BY-SA 4.0); research use and aggregate results are permitted under either | `https://archive.org/details/stackexchange`: the PostHistory, Posts and Users files for writing, philosophy, worldbuilding, academia and english only, skipping any single archive over 2 GB | Record SHA-256 | Whichever sites arrive |
| IteraTeR | GO3 | Apache-2.0 | On disk from Stage 9 (pinned at `41adc0818356...`); Hugging Face `wanyu/IteraTeR_full_doc` only if the archive lacks the full-document split | Record the commit | None needed |
| Already on disk | AT, ID, BK | As recorded | n/a | n/a | n/a |

The on-disk sources are CoAuthor (private, aggregates only), ScholaWrite, ArgRewrite V.2, Moral Machine and Community Alignment. For ArgRewrite V.2, record whether the writers' pre-study goal surveys are present, and correct `corpora/public/MANIFEST.json`, which still lists ArgRewrite as unavailable.

**Identifiers.** Usernames and user IDs (Lichess, Stack Exchange, PEP and EIP authors, AMI and ICSI speaker codes, Crowd-enVENT `prolific_id`) are hashed at intake with a per-campaign salt. Nothing per-person leaves the repository. Crowd-enVENT's demographic and personality columns are never read; texts whose writer answered yes to `did_you_lie?` are excluded and counted.

### 0.6 Defaults

Unless a card says otherwise:
- **CoAuthor timing:** Week 4's defaults (its §0.5) stand.
- **Seed:** 20261107.
- **Cluster units:**
  - writer, for CoAuthor;
  - player, for Lichess;
  - author, for PEPs and EIPs, with multi-author documents assigned to the first-listed author and a texture cell that drops them;
  - user, for Stack Exchange;
  - building, for comfort data, with study as a texture cell;
  - meeting, for AMI and ICSI;
  - writer (`prolific_id`, hashed), for Crowd-enVENT; text, for IN4;
  - fingerprint, for Moral Machine.
- **Three-way rule:**
  - "supports" when the whole 95% interval lies beyond the card's practical bar in the predicted direction;
  - "against" when the whole interval is on the other side of zero, or entirely inside the bar's band around zero;
  - "inconclusive" otherwise.
- **Exposure:** every card reports its counts before any restriction, and its supported cohort after.

### 0.7 Privacy

- Outputs are aggregate only.
- Identifiers stay hashed.
- No raw text from any corpus leaves the repository.
- No transfer to any paid provider.

## 1. State on 7 November (`dcbcc26de`)

| Item | State |
|---|---|
| Solid descriptions | A writer's pause rhythm, place by place, identifies her (theory days and Week 4) |
| Supported on one cohort, one comparison open | Pauses lengthen before words that are surprising given her own earlier writing, with the current prompt excluded (D33): 0.051 per nat [0.036, 0.076], on 34 writers and 50,503 words. A matched donor's history had a larger point estimate (0.125), but its interval was invalid: one bootstrap draw had no donor support |
| Theory days | Three tests inconclusive or mixed: word scales, rater disagreement, and DISGUST with less talk of minds (TD4 to TD6); the source-weighing test void, 18 writers against a floor of 20 (TD7); the three Rutledge mood tests held at source (TD1 to TD3); mood drift and standing satiation held on licence (B1, B3); the never-trade test supports, descriptively (B2: Moral Machine refusals 14.5 points above gender and fitness, carried by species); chess effort times skill inconclusive (B4) |
| Week 4 backlog | Eight items remain (S2's complete replay and dependents; T4 uncertainty; WD1's corrected calibration; D7 follow-ups; CA1, the Community Alignment encoding; WB1 effects; P7 point scoring; the ScholaWrite fallback). Never started: six cards (WC2, FR1, TR5 and WC4, unblocked since R1 passed on 2 November; S3 and T2, consumers unbuilt). No record of three intakes (U1, S4.k, T2.r) |
| Queue | 0 of 4 slots active; 0 of 8 ready |

## 2. Programs

Each family names its route to the engine, a shared pipeline built once (amendment K), its cards, its branches and its texture grid. Every card's design note records, before outcomes:
- the primary and its direction;
- the practical bar and the three-way rule;
- the case and its check, with the floor and its fallback;
- the rival;
- the by-construction list: anything whose sign or size the design fixes, reported for scale only;
- the smaller route;
- the ceiling.

### 2.1 Family AT: attention marks for panel one (CoAuthor keystrokes)

**Route.** Panel one ("Current attention") marks words where the maker departed from her autopilot. The engine computes departures from the token loss of `Qwen2.5-0.5B` and `SmolLM2-360M`, without keystrokes. This family checks those marks against real pauses, and decides whose model of the writer the engine needs.

**Pipeline.**
- One scoring pass per language model over every writer-typed word in CoAuthor, in two contexts:
  - the final document's text up to the word, which is what the engine sees;
  - the document as it stood when she typed the word, reconstructed from the canonical timeline.
- The pass outputs word-level surprisal (summed over subword tokens) and the entropy of the next-token distribution at the word's first token.
- Models: P6's leave-writer-out 3-gram, plus the ten causal models pinned in section 0.5 (`distilroberta-base` is LA1's masked model and isn't scored here). The final-text context runs for all ten. The at-typing context runs for all ten on the frozen 20% of sessions, and on the rest only for AT2's best model and the engine's two departure models. Scoring reuses each prefix's cache, as P7's hybrid pilot validated, and the verify child recomputes a seeded 2% of forwards plus every downstream fit, as P7's batch pilot verified six fresh forwards. Run on CPU with at most 2 threads.
- The final-text context runs first, for every model. The at-typing context then runs on a frozen 20% of sessions (seed 20261107), then on the rest in idle slots.
- P7's GPT-2 medium scoring becomes this pipeline's first model; its point scoring is subsumed here.

**Family ceiling:** 750,000 CPU-seconds.

**AT1. Whose history predicts her pauses?** This resolves D33's donor question.
- **Design.** D33's joint writer-random-intercept model of log pause, its controls and its prompt exclusion, with three history terms in one fit:
  - population surprise;
  - own-history surprise;
  - donor-history surprise, centred on population.
- **Donors.**
  - The donor history is the pooled history of k = 5 donors, drawn without replacement from writers with supported histories in the same genre by D33's prompt-excluded matcher, and trimmed to her own history's session and token budget, as D33 did. Without the trim, five histories give the donor term more data and less noise than hers, which tilts the contrast toward "shared".
  - Support is judged per donor set, not per word. A resample whose donor set leaves the donor term without support redraws that writer's donor set, up to 20 times, and the redraw count is reported.
  - Each resample redraws the donors.
- **Primary:** own minus donor coefficient, per nat, with a 2,000-draw writer-cluster interval. Bar 0.01.
  - Supports a personal history if the whole interval exceeds +0.01.
  - "Shared, not personal" if the interval sits inside ±0.01 or below zero.
- **Case:** D33's supported cohort (34 writers). Floor 20 writers. Fallback: a pooled descriptive fit.
- **Rival:** topical reuse. The prompt is excluded, and genre-matched donors carry topic.
- **By construction:** none once budgets are equal. k = 1 in texture is the like-for-like check.
- **Branches.**
  - If personal: AT1.p, which part of her history carries it (her vocabulary cache against her phrasing bigrams).
  - If shared: AT1.s, a genre-adapted population model as the engine's default.
- **Texture:**
  - k ∈ {1, 3, 20};
  - donor match: genre, random, or same prompt;
  - pause measure: hesitancy posterior, log pause, or stop indicator;
  - genre split;
  - prompt included.
- **Ceiling:** 40,000 CPU-seconds.

**AT2. Which language model's surprise predicts her pauses?**
- **Design.** Add each model's surprisal to Week 4's within-writer timing controls, and score the fit on held-out writers (5-fold by writer).
- **Primary:** each model's held-out gain in log-likelihood of log pause per word, relative to the 3-gram, on the final-text context, with a 2,000-draw writer-cluster interval on each difference.
- **One primary:** the better of the engine's two departure models' gains. The other models' gains, the curve over model size, and the at-typing gains on the frozen 20% of sessions are secondary.
- **Readout:** the curve over model size. Is it rising, flat, or rising then falling? Larger transformers fit human reading times worse than smaller ones ([Oh & Schuler 2023](https://aclanthology.org/2023.tacl-1.20)); this asks the same of writing.
- **Practical bar:** 0.002 nats per word. A model "fits better" only past the bar.
- **Case:** all 61 writers' typed words. Floor 40 writers. Fallback: a pooled descriptive fit.
- **By construction:** none, but surprisal from related models is highly correlated, so report the pairwise correlations.
- **Branches.**
  - The best model by held-out fit on the final-text context becomes the model for AT3, AT4, GO1's language-model reader and LA1's surprise as soon as those fits land. The at-typing fits are reported beside it and don't change the choice. Until then those cards wait without a slot and don't count toward amendment A's buffer.
  - If the engine's departure models fall below the best by more than the bar: AT2.e, the engine's exact departure function at `certified-fit-1` (`5f3ad0a`) scored the same way.
- **Texture:**
  - context: final text or at-typing;
  - context length: 64, 256 or 1,024 tokens;
  - genre;
  - pause measure.
- **Ceiling:** 550,000 CPU-seconds, mostly in idle slots.

**AT3. Is it the open choice or the surprise?**
- **Design.** In one model, with AT2's best model:
  - the next-token entropy at the word's first token: how many continuations were open, the size of her decision;
  - the chosen word's surprisal: how unexpected it was.
- **Primary:** the entropy coefficient controlling surprisal, and the surprisal coefficient controlling entropy, each with a writer-cluster interval. Bar 0.01 per nat.
- **One primary:** the entropy coefficient. The rest are secondary.
- **By construction:** entropy is the expected surprisal, so the two correlate. Report the variance inflation, and run a texture cell with residualized entropy.
- **Route:** if entropy carries the pause, panel one should mark open choices, not only surprising words.
- **Texture:** each AT2 model; genre; word position (sentence start against inside).
- **Ceiling:** 30,000 CPU-seconds.

**AT4. Can the final text alone find her stops?**
- **Label:** a word is a stop if its preceding interval is hesitant (fluent posterior below 0.5; Week 4 defaults).
- **Design.** Predict stops from final-text features only, on held-out writers (5-fold by writer). Two models:
  - a baseline: word length, frequency, sentence and paragraph boundaries, position;
  - the full model: the baseline plus AT2's best surprisal and AT3's entropy.
- **Primary:** full minus baseline AUC, with a writer-cluster interval. Bar +0.02.
- **Secondary:** the AUC of the engine's own departure marks at `certified-fit-1`.
- **Route:** panel one gets a measured accuracy on real stops. If the engine's marks beat the baseline AUC by the bar, with its own writer-cluster interval, panel one's display is licensed at that AUC as a research preview.
- **Texture:** genre; threshold (fluent posterior 0.3 and 0.7); the engine's two departure models separately.
- **Ceiling:** 30,000 CPU-seconds.

### 2.2 Family CH: decision time and set points in chess (Lichess, Stockfish)

**Route.**
- Panel two marks planning moments, and the curator's 7 November answer reads long deliberation as a sign of the size of the decision tree. Chess is the one public record where the difficulty of each choice can be measured independently, by an engine. This family asks:
  - whether time follows difficulty;
  - whether expertise shrinks the tree;
  - whether a time reserve behaves like a set point read from restoring moves;
  - whether winning standing satiates.
- Ghost's K3 and K4 study the same questions in constructed worlds.

**Pipeline.**
- **CH0, intake and parse.**
  - Stream the four months in section 0.5 without full decompression to disk, and parse per-move clocks, ratings, time controls, results and timestamps. Hash usernames.
  - Two frozen samples, seed 20261107:
    - CH1's sample of players and their moves (below), for CH2, CH3 and CH5;
    - a player sample (2% of players, by hashed username), keeping every game those players played across the four months, for CH4 and CH6, which need long per-player histories.
  - Full months run only in idle slots, as texture, except two counting passes the samples need: each player's rated games per month (CH1's frame) and opening positions in the first 10 plies (CH3's book status).
  - Build per-player move-time sequences:
    - think time is the clock difference between a player's consecutive moves plus the increment;
    - drop each player's first two moves;
    - drop moves with zero measured think time from time models, counting them.
  - Strata: bullet, blitz, rapid, classical, by TimeControl.
- **CH1, positions and analysis.**
  - Sample players, then moves. Within each rating band (400 points) and time control, draw players at random among those with at least 20 rated games in the month, then analyse 40 of each player's moves, spread over at least 10 of her games. First 400,000 positions: 7,000 blitz players and 1,000 each in bullet, rapid and classical, half from the 2017 months and half from 2026-07, each player sampled once; then more players in idle slots, up to the family ceiling. No Stockfish rate has been measured on this host. At about a second per position plus its replay, the family ceiling holds roughly one million positions; CH1's in-slot pilot (amendment K) measures the rate.
  - Analyse each position with Stockfish 19 at MultiPV 5 and a fixed 1,000,000 nodes, single-threaded, with hash 64 MB. Each CH1 slot runs two single-threaded engines, so a Stockfish slot uses its two threads.
  - Send `ucinewgame` before each position, so the fresh-process replay reproduces every evaluation.
  - Don't use the Lichess evaluations file.
- **Measures per move:**
  - **k50:** the number of the five analysed moves within 50 centipawns of the best (policy closeness, 1 to 5);
  - **policy entropy:** a softmax over the top five evaluations, with its temperature fitted to human move choice by rating band on a held-out month;
  - **stakes:** the absolute evaluation before the move;
  - **complexity:** the number of legal moves;
  - **centipawn loss:** best minus played, with the played move evaluated separately if it's outside the top five.
- **Known answers:** single-legal-move positions return k50 = 1, and Lichess puzzles tagged mateIn1 whose solution is the only mating move return k50 = 1 (this is the puzzle file's use), plus a parser round-trip on 1,000 games.

**Family ceiling:** 2,500,000 CPU-seconds. Most of this is Stockfish, and Stockfish is what keeps idle slots busy.

**CH2. Do players think longer when the choice is close?**
- **Design.** A within-player regression of log think time on k50, by time control. Controls:
  - clock remaining (as a share of the initial clock) and increment;
  - move number, stakes and complexity;
  - material, and a player fixed effect.
- **Primary:** the k50 slope in blitz (the largest stratum), with a 2,000-draw player-cluster interval. Bar: 3% longer per additional close move.
- **Rival:** stakes and complexity, not closeness. Texture enters each alone.
- **His reading against the rival.** Secondary: split k50 into the gap between the two best moves (closeness) and the count of moves within 50 centipawns beyond the second (breadth). His tree-size reading predicts breadth carries think time beyond the gap; the conflict account ([Evans, Dillon & Rand 2015](https://doi.org/10.1037/xge0000107)) predicts the gap carries it.
- **Case:** at least 5,000 players with 20 or more analysed moves. Fallback: pooled across time controls.
- **Branches.**
  - If supported: CH2.m, whether the slope is steeper in critical positions (stakes near zero).
  - If against: CH2.s, policy entropy in place of k50.
- **Texture:**
  - each time control;
  - k100 and policy entropy as closeness measures;
  - months (2017 against 2026);
  - nodes (300,000; 3,000,000).
- **Ceiling:** 60,000 CPU-seconds, analysis aside.

**CH3. Does expertise shrink the tree?**
- **Design:**
  - CH2's model with a rating-band interaction on k50;
  - for the second primary, think time on book moves: in the first 10 plies, a move is "book" when the position before it occurred in at least 500 games of the same month and time control and the move played is that position's most played move there. Non-book moves are the other moves at equal move number. Book status is computed from the parsed months themselves, so no outside opening database is used.
- **Primaries:**
  - the interaction: does the time-closeness slope rise with rating?
  - the rating slope of log think time on book moves.
- **Bar:** a 2% change in slope per 400 rating points.
- **One primary:** the interaction. The rest are secondary.
- **Route:** expert time is spent where choices are close. If so, the engine's panel two marks long stops as planning only in proportion to the maker's expertise.
- **Texture:** time controls; rating band widths.
- **Ceiling:** 40,000 CPU-seconds.

**CH4. Is the time reserve a set point read from its restoring moves?** This is the curator's "a bunch of vectors that kind of help you zero in increasingly precisely on that set point".
- **Units:** players with at least 50 games in one time control (blitz first). (a) uses players with at least 115, so that 80 games fit in the first 70%.
- **Design.**
  - At every move from move 10 on, the reserve is the clock remaining as a share of the initial clock, minus the player's own median share at that move number in that time control.
  - For each player, fit a piecewise-linear response of think time to the reserve's deviation from a target. The target and its two slopes are estimated by profile likelihood on that player's first 70% of games, in time order.
  - Moves made with less than 15% of the initial clock remaining are dropped, so time pressure that forces fast moves doesn't count as restoring. The cut is on the clock itself, never on the reserve or its deviation, so the neighbourhood of the target stays in the data.
  - Games whose first clock reading is below the time control's initial clock (berserk) are dropped and counted.
- **Primaries.**
  - **(a) Zero in.** Fit the target on each player's first 10, 20, 40 and 80 games, and score each fit on the same held-out games as (b). Zeroing in predicts that the held-out gain over the no-target model rises with games used. The shrinking interval width is reported for scale only, since any estimate's interval narrows with more games.
  - **(b) Prediction.** On the player's held-out 30% of games, does the fitted target improve prediction of think time over a no-target model (move number, increment, clock)? This is the paired held-out log-likelihood gain, with a player-cluster interval. Bar 0.005 nats per move.
  - **(c) Overshoot, both ways.** After a deficit beyond 30% of the target, does the reserve recover past the target before settling? And after a surplus beyond 30%, does it fall below? The share of recoveries that overshoot in each direction, against a matched null simulated from each player's fitted target model, with her own residual autocorrelation and no overshoot term. Shuffled deviations can't serve: shuffling removes the autocorrelation, so the null crosses the target at almost every step. Projection bias runs both ways: plans made hungry overshoot, and plans made full undershoot ([Loewenstein, O'Donoghue & Rabin 2003](https://doi.org/10.1162/003355303322552784)). So the curator's "People will often overshoot" predicts the deficit side, and the mirror is the check.
  - **(d) Precision.** Do players whose games are concentrated in one time control (top quartile of concentration) have steeper restoring slopes? The difference in median slope, with an interval.
  - **(e) A point or a band?** Fit a two-threshold model beside the one-target model: no restoring response between a lower and an upper boundary, and restoring outside them. Compare held-out fit. One leading model holds that body fat is defended only at an upper and a lower boundary, with weak or no regulation in between ([Speakman et al. 2011](https://doi.org/10.1242/dmm.008698)). If the band model fits better, vectors locate the edges, not a middle (mine).
- **One primary:** (b). The rest are secondary.
- **Case:** at least 1,000 players. Planted-target recovery in 200 synthetic players must place the target within 5% of the clock.
- **By construction:** the forced speed-up near a flag is excluded by the clock floor; report what share of moves it removes. The interval width in (a) shrinks with games by sampling alone.
- **Route:** the engine's set-point reader. Ghost's K3 tells this card how many records a reader needs.
- **Texture:**
  - target at move 20 against move 10;
  - rapid;
  - concentration measured by games against by days;
  - overshoot threshold of 20% or 40%.
- **Ceiling:** 80,000 CPU-seconds.

**CH5. Does effort pay more for the skilled?** The curator's "effort times power is what gets the effect" (4 November), retesting B4, which was inconclusive.
- **Design.** Centipawn loss on think-time deviation × rating, within player, with CH2's controls. The deviation is log time minus her expected log time, from a regression of log time on a player effect and on time control, 400-point rating band, k50 and move-number decile, fitted without the move itself; with 40 analysed moves per player (CH1), per-player means by class would mostly rest on one move. Instrument the deviation, and its product with rating, by a prior clock of at most ten seconds and its product with rating, under B4's rules: OLS beside two-stage least squares, and both excluded-instrument partial F statistics above 10, otherwise OLS as descriptive only. Clock remaining stays in the controls as a smooth term, so identification rests on the ten-second threshold; say so in the result.
- **Primary:** the interaction. Multiplicative predicts that extra time cuts loss more at higher rating. Bar: 1 centipawn per doubling per 400 points.
- **Rival:** diminishing returns at the top, as in [Medvegy et al. 2022](https://doi.org/10.1002/acp.3958).
- **Texture:** time controls; loss capped at 300 or 1,000; positions with stakes under 200 only.
- **Ceiling:** 40,000 CPU-seconds.

**CH6. Does winning standing satiate?** This replaces the held B3. It uses human ratings in place of DomArchive.
- **Design.**
  - A session is consecutive rated games by one player with gaps under 30 minutes.
  - A discrete-time model of ending the session after each game. Predictors:
    - the session's net rating change so far;
    - the last result;
    - games played so far;
    - hour of day.
  - Player fixed effects.
- **Primary:** the odds ratio of stopping after a net-positive session against a net-negative one, at equal games played. Satiation predicts above 1. Bar: odds ratio 1.05. The curator's suggestion that social standing has no ceiling (C4, the claim B3 tested) predicts no satiation, so a supported satiation result counts against it.
- **Rival:** loss-chasing (people play on after losses), which also predicts above 1. So the secondary is the slope on the net change's size: satiation predicts stopping rises with the size of the gain.
- **Case:** at least 10,000 players with 5 or more sessions.
- **Texture:** gap thresholds of 15 or 60 minutes; blitz against rapid; streak terms; 2017 against 2026.
- **Ceiling:** 30,000 CPU-seconds.

### 2.3 Family IN: a channel's intensity and its trigger (Crowd-enVENT)

**Route.**
- The curator's 7 November answer: "I do wonder if the amount that they trigger is simply decided upon how well the scenario fits their trigger. How strong is the prediction of future harm? Because that is what determines how loud fear is, I guess." If this holds on people, the engine's panel three can grade a channel by trigger fit, not by topic words.
- The program's vocabulary stays Panksepp's. The corpus's prompted emotion words only select texts, and its appraisal ratings measure features of each event's trigger.

**Pipeline.**
- Intake the generation table (6,600 writer texts, each with the writer's intensity rating from 1 to 5 for the emotion she felt, and her 21 appraisal ratings) and the validation table (1,200 texts, each read by 5 readers).
- Map prompted emotions to channels, frozen before outcomes:
  - fear to FEAR; anger to RAGE; sadness to PANIC/GRIEF; disgust to DISGUST;
  - joy to PLAY, marked partial;
  - boredom to low SEEKING, marked partial;
  - guilt, shame, pride, relief, surprise, trust and no-emotion unmapped, reported only.
- Record the corpus's own column names for every appraisal in the design note.
- **Paragon profiles.** Each mapped channel's prototype trigger, written as the appraisals it should raise or lower, frozen before outcomes from the curator's statements:
  - **FEAR** ("there are now futures in which I die"): unpleasantness up; goal support down; the writer could anticipate the consequence (certainty of the harm) up; urgency up; own control down.
  - **RAGE** (something removed or blocked, and the urge to push the world back): another person responsible up; another person in control up; goal support down; urgency up; own control up (coping).
  - **PANIC/GRIEF** (a lost connection): unpleasantness up; goal support down; own control down; acceptance of the consequence down.
  - **DISGUST** (a read of harmful intent, then no further inquiry): violation of social norms or standards up; another person responsible up; the wish not to consider the event further up.
  - **PLAY** (partial): pleasantness up; goal support up; urgency down.
  - **SEEKING** (partial; boredom as its deficit): familiarity up; attention down; pleasantness down.
- The fit index is the mean of each profile's standardized items, signed. Unpleasantness and pleasantness are excluded from the index, since they're the rival.

**Family ceiling:** 60,000 CPU-seconds.

**IN1. Does intensity track the fit to the channel's prototype trigger?**
- **Design.** Within each mapped prompt, the writer's intensity on the fit index, controlling unpleasantness (or pleasantness, for PLAY), the writer's confidence, and her mean rating on the nine appraisals outside the four primary profiles (suddenness, familiarity, predict_event, goal_relevance, chance_responsblt, self_responsblt, chance_control, attention, effort). The last is a response-style control: the RAGE profile raises four items and lowers one, DISGUST raises all of its items and PANIC/GRIEF lowers all of its, so a writer who rates everything high would otherwise move the index and her intensity together.
- **Primary:** the pooled four-channel standardized slope of intensity on the fit index, with prompt intercepts and a 2,000-draw writer-cluster interval. Bar 0.10.
- **Secondary:** the same slope for FEAR, RAGE, PANIC/GRIEF and DISGUST separately, each with its own writer-cluster interval, at the same bar.
- **Readout:** the primary's verdict, then a count of channels whose secondary supports, is against, or is inconclusive.
- **Rival:** intensity is generic unpleasantness. It's in the model, so the index must add beyond it.
- **Case:** at least 300 texts per mapped prompt for a channel's secondary. A channel below that is reported descriptively; the pooled primary runs regardless.
- **Branches.**
  - Per channel supported: IN1.w, the profile's items one at a time (which part of the trigger carries intensity).
  - Per channel against: IN1.r, a reversed-sign profile as a check that the mapping, not the channel, failed.
- **Texture:**
  - equal weights against each profile's first-listed item doubled;
  - a 1-to-5 scale against binarized at 4;
  - excluding texts under 10 words;
  - each profile with its signs reversed, for every channel, as the response-style check.
- **Ceiling:** 15,000 CPU-seconds.

**IN2. Does certainty of the harm make FEAR louder?**
- **Design.** Within FEAR texts: intensity on unpleasantness, consequence anticipation and their interaction, controlling urgency and confidence.
- **Primary:** the interaction (harm anticipated with certainty is louder). Bar 0.10 standardized.
- **Rivals:**
  - Stress in the rating. Subjective stress, pupil size and skin conductance tracked irreducible uncertainty ([de Berker et al. 2016](https://doi.org/10.1038/ncomms10996)), a result the curator endorsed on 3 November. It fits his 7 November rule, "stress is caused by uncertainty", though in his gun example the uncertainty was about what to do, and in de Berker's task no action changed the shocks. If a writer's single intensity rating carries stress beside FEAR, that predicts the opposite sign. So a negative interaction can't separate louder FEAR under uncertainty from stress in the rating, and is reported that way (mine).
  - For vivid harms, the value people place on avoiding them, measured by choices and willingness to pay rather than by rated feeling, barely changes across middle probabilities ([Rottenstreich & Hsee 2001](https://doi.org/10.1111/1467-9280.00334)). If felt FEAR follows valuation, that predicts a flat interaction: possibility, not certainty, sets the volume (mine).
- **Ceiling:** 5,000 CPU-seconds.

**IN3. Does control quiet FEAR, and does it strengthen RAGE?**
- **Design.** Own-control slope on intensity, within FEAR texts (predicted negative) and within RAGE texts (predicted positive), controlling unpleasantness.
- **Primary:** the difference between the two slopes. Bar 0.15.
- **Route:** the curator's special forces agent, for whom "it clearly channels me into the set of actions I need to take", with RAGE as a possible substitute.
- **Expect the RAGE half to be weak.** In a test of anger's appraisals, no single appraisal was necessary or sufficient, control among them ([Kuppens et al. 2003](https://doi.org/10.1037/1528-3542.3.3.254)).
- **Ceiling:** 5,000 CPU-seconds.

**IN4. Where do readers miss the writer's trigger?** This is the engine's backward run.
- **Design.** For each appraisal, the agreement between each reader's rating and the writer's (absolute error), against the agreement among readers. Also by mapped channel, and by text length tercile.
- **Primary:** for each channel, the mean excess error (reader-to-writer error minus reader-to-reader error) on the channel's profile items, minus the same on the appraisals outside every profile, with a text-cluster interval. Bar 0.10 rating points. A positive value means readers miss the channel's trigger more than they miss the event's other features.
- **One primary:** the four channels pooled, with channel intercepts. Each channel's value is secondary.
- **By construction:** readers share the text and the task, so reader-to-reader error is the smaller on every item; the corpus authors found no appraisal on which writer-reader pairs agreed better ([Troiano, Oberländer & Klinger 2023](https://arxiv.org/abs/2206.05238), §5.3). The per-item excess is reported for scale only.
- **Route:** the engine's trigger reader is a reader. The items readers miss are where panel three must show low confidence.
- **Fallback:** none. Appraisal-enISEAR can't stand in: its appraisals were annotated by readers from the original author's perspective, not by the writers, and its page states no licence. If the validation table is malformed, IN4 is recorded "unsupported at source".
- **Ceiling:** 10,000 CPU-seconds.

### 2.4 Family SP: comfort set points that sharpen and move (ASHRAE Database II)

**Route.**
- The curator's 7 November answers:
  - set points sharpen with time spent near them ("I don't just want to be at 71 degrees I want to be at 71.1 degrees provided I've stayed at exactly 71"; "Rich people are soft");
  - a lasting deficit dulls them ("the resolution decreases. It's still there, but it just gets weaker").
- Thermal comfort is the one large public record with a felt response, a measured state, and how controlled each person's environment is.
- If the curator's precision dynamics show here, Ghost's K3 and the engine's set-point reader carry them.

**Pipeline.**
- Join measurements to building metadata: cooling type (air-conditioned, naturally ventilated, mixed); climate; the prevailing mean outdoor temperature.
- Exclude rows missing operative temperature or thermal sensation, counting them.
- Units: buildings, with at least 30 respondents each.

**Family ceiling:** 40,000 CPU-seconds.

**SP1. Does the comfort set point follow the weather?**
- **Design.** Per building, the neutral temperature: where mean thermal sensation crosses zero, by regression of sensation on operative temperature. Then regress neutral temperature on prevailing outdoor temperature, by cooling type. Where a building's slope is below 0.1 per °C, its neutral temperature uses Griffiths' fixed slope of 0.5 per °C (texture: all buildings by Griffiths).
- **Primary:** the slope difference, naturally ventilated minus air-conditioned, with a building-cluster interval. Bar 0.1 °C per °C.
- **Readout:** a replication of the adaptive comfort model ([de Dear & Brager 1998](https://escholarship.org/uc/item/4qq2p9c6)) on Database II. It reads the set point's location moving with experience.
- **Ceiling:** 10,000 CPU-seconds.

**SP2. Does steady climate control sharpen the set point?**
- **Design.** Per building:
  - sensitivity, the slope of sensation per °C (steeper is sharper);
  - the width of the temperature band in which at least 80% find conditions acceptable.
- **Primary:** the median sensitivity, air-conditioned minus naturally ventilated, with a building-cluster interval. Bar 0.05 sensation units per °C.
- **Rival:** an artefact of temperature range, in two directions. Measurement error in operative temperature flattens slopes fitted over narrow ranges, which biases air-conditioned buildings toward flatter slopes (against the prediction); the bounded seven-point sensation scale steepens slopes fitted near neutral and flattens them toward its ends (for it). Selecting buildings on range doesn't bias a linear slope by itself. Texture fits slopes on range-matched building pairs (matched on range and mean temperature), with an ordinal probit per building, and on buildings with at least a 4 °C range (48 of 116 air-conditioned and 53 of 74 naturally ventilated buildings with 30 or more respondents have one).
- **What a positive can't decide.** Cooling type stands for both thermal history and control over one's own conditions. In one building, with the same temperatures and clothing, occupants with different degrees of window control responded differently ([Brager, Paliaga & de Dear 2004](https://escholarship.org/uc/item/4x57v1pf)). So a positive SP2 can't tell time near the set point from perceived control. Say so in the result. Texture: the `window` and `fan` fields, where recorded, as controls for personal control.
- **Ceiling:** 10,000 CPU-seconds.

**SP3. Does a lasting deficit dull the set point, or move it?** This tests the curator's answer against its rival.
- **Design.** Naturally ventilated buildings, binned by how far the prevailing temperature sits from 22 °C, in 3 °C bins.
- **Two estimates per bin:**
  - sensitivity: dulling predicts it falls with distance;
  - neutral temperature: moving predicts it follows the prevailing temperature.
- **Primary:** the slope of sensitivity on distance, with a building-cluster interval, read beside SP1's location slope. Bar 0.01 per °C of distance. Both can hold.
- **Route:** Ghost's K3 asks the same question about records, using probes this data doesn't have.
- **Texture:** hot and cold sides separately; clothing and metabolic rate as controls; study as the cluster; range-matched bins with an ordinal probit, and air speed (`vel`) as a control.
- **Ceiling:** 10,000 CPU-seconds.

### 2.5 Family GO: stated goals and the revisions that serve them (PEPs, EIPs, Stack Exchange, IteraTeR)

**Route.**
- The top of the engine reads higher-order goals from text and its history, and has had no real ground truth.
- A PEP or EIP states its author's goal in a Motivation section and reasons in a Rationale section, and its history is a git log. Stack Exchange edits carry the editor's own reason.
- The family gives panel three a measured accuracy on stated goals. It also gives the engine's revision reader a measured accuracy on stated reasons. Both work on public pieces with visible history, the curator's planned reading targets.

**Pipeline (GO0).**
- Clone both repositories, and recover each document's history with renames followed.
- Parse header authors, status, type and, for EIPs, category.
- Extract the Motivation, Rationale, Abstract and Specification sections by their headings. A document without a Motivation section is excluded and counted.
- For Stack Exchange:
  - parse PostHistory edits (types 4 to 6 and 24), with the editor's comment, the before and after text, and whether the editor is the post's author;
  - map comments to reason categories by a frozen keyword dictionary (typo or spelling, grammar, formatting, clarity, added content, removed content, links, tags), with "other".
- For IteraTeR: intents per edit.

**Family ceiling:** 600,000 CPU-seconds.

**GO1. Can a reader find the author's stated goal from the rest of the document?**
- **Design.** For each document, hide its Motivation, then rank it against 49 distractor Motivations by its fit to the rest of the document. Distractors come from the same repository and type (PEPs: Standards Track, Informational or Process, since PEP headers carry no category; EIPs: type, and category for Standards Track). Where the stratum holds fewer than 50 documents with a Motivation section, the rest are drawn from the repository's other types, and the share is reported. Same-type distractors control genre, not topic; topic is what TF-IDF measures, and the claim is the gain over it. The scout's PEP clone (6 November) has 298 PEPs with a Motivation heading: 268 Standards Track, 20 Informational, 10 Process.
- **Readers:**
  - TF-IDF cosine;
  - the CA1 encoder's cosine, on 128-token chunks averaged, since the encoder reads at most 128 tokens;
  - a language model's conditional gain, log p(Motivation | rest) minus log p(Motivation), with AT2's best model that fits the context.
- **Primary:** each reader's top-1 accuracy minus 1/50, with an author-cluster interval. Separately, the language-model reader minus TF-IDF, and the encoder reader minus TF-IDF. Bar 0.05.
- **One primary:** the language-model reader minus TF-IDF. The rest are secondary.
- **By construction:** Motivations share vocabulary with their documents, and that is partly legitimate. TF-IDF is reported as the lexical floor, and the claim is the gain over it.
- **Branches.**
  - If a reader beats TF-IDF by the bar: GO1.r, Rationale in place of Motivation (reasons against goals).
  - If not: GO1.d, distractors from other types or categories (how much is topic).
- **Texture:** 9 distractors, or 99 where the stratum allows; PEPs and EIPs separately; Specification only as the rest; first draft against final draft.
- **Ceiling:** 150,000 CPU-seconds.

**GO2. After a goal is revised, does the text follow it?** This is the curator's account of global revision (1 November): "you need to go back and make changes to align those automatic outputs with the higher order functional hierarchy positions". And it is his 7 November check: "you kind of check each one one by one".
- **Design.** In each document's history, mark commits that change the Motivation by at least 20% of its tokens. For the three commits after it that touch other sections, take the added text's similarity to the new Motivation minus its similarity to the old one (the CA1 encoder, on 128-token chunks averaged). For the three commits before it that touch other sections, take the same contrast: that text can't follow a goal not yet written. Commits that touch more than five documents, or change only markup or whitespace, are excluded and counted.
- **Primary:** after minus before, with an author-cluster interval. Bar 0.02 cosine.
- **Rival:** the goal was rewritten to match text already written. That shows as a positive before-contrast, reported beside the primary.
- **By construction:** later text resembling the final text is guaranteed, so this card never uses the final text. A commit that left the Motivation unchanged has identical old and new Motivations, so its contrast is zero by definition and can't serve as a control.
- **Case:** at least 100 Motivation-changing commits with three earlier and three later commits that touch other sections. Fallback: one earlier and one later commit.
- **Ceiling:** 100,000 CPU-seconds.

**GO3. Do editors' stated reasons match what their edits do?**
- **Design.** Predict an edit's stated reason category from its diff alone: character and token changes, edit distance, punctuation, links, code spans, and an IteraTeR-trained intent classifier's output. Train on held-out users (5-fold by user).
- **Primary:** macro-F1 over the text-body reason categories (typo or spelling, grammar, clarity, added content, removed content), on body edits (types 5 and 24) only, minus the macro-F1 of a classifier that predicts from the class priors alone, with a user-cluster interval. Bar 0.05.
- **By construction:** a tag edit is its own PostHistory type (6), and link and formatting reasons are read off the same link and markup counts the classifier sees, so those categories are reported for scale only. A majority-class baseline scores near zero on macro-F1, so it can't be the comparison.
- **Secondary:** do a user's reasons recur as a personal habit? Identify a user's reason distribution from half of her edits against a gallery of 30, under Week 4's three-role rule.
- **Route:** the engine's revision reader gets a measured accuracy against writers' own reasons, on public histories.
- **Texture:** self-edits only; each site separately; IteraTeR classifier excluded.
- **Ceiling:** 250,000 CPU-seconds.

### 2.6 Family MD: mood levels, the uncertainty gate, security, and drift (Rutledge; Jangraw)

**Route.** The curator's lasting-deficit and trigger claims on people, from the two largest open mood records.

**MD1 to MD3** are TD1, TD2 and TD3 as designed (their committed notes in `docs/design/stage-15/theory-days/`). None has run yet. Each runs under Week 5, with its source switched to the Zenodo route in section 0.5 under the same pins, and its ceiling as recorded. The route change is recorded in a Week 5 intake note; `DATA_INTAKE.md` is not edited.
- **MD1** asks whether a mood level adds to momentum (TD1).
- **MD2** asks whether outcome uncertainty weakens the response (TD2).
- **MD3** asks whether security is defended from below and spent from above, or simply liked (TD3).
- **MD3's reading.** On 7 November the curator said security "is something you try to maximize... The problem is its value decreases as you get further and other needs get louder", and in the same answer, "I would expect that deviation from that setpoint, from Margin's setpoint specifically, has to be balanced against the other ones." TD3's committed outcomes stay as they are. A falling marginal value and a defended set point both predict that risk-taking falls the further behind she is, so a "supports" result fits both. MD3's Week 5 note, committed before outcomes, records this and reports one contrast beside the primary: the slope below zero minus the slope above it. A positive contrast, risk-taking falling faster with each point behind than it rises with each point ahead, favours a defended set point; a contrast near zero favours a falling value; a negative contrast is a rival's pattern: house money if both slopes are positive, break-even if the slope below zero is itself negative, which TD3's primary scores against C4.

**MD4** is B1 (mood drift by condition, OSF `km69z`), as designed. It runs only once the curator's message to Codex accepts the archive's notice. Until then it waits without a slot.

**Family ceiling:** 34,400 CPU-seconds: TD1 and TD2's shared 7,200, TD3's 3,600 and B1's 3,600 (theory-days packet section 3), plus 20,000.

### 2.7 Family LA: laughter as an inference marker (AMI, ICSI)

**Route.**
- The curator's new idea (7 November): "it's the inserting of that final piece followed by laughter that kind of highlights that you just did this. And other people will laugh to say they found the same thing." He says it's "worth checking".
- The engine's panel three would gain a structural cue if laughter marks the completion of a hidden structure, not mere surprise.

**Pipeline (LA0).**
- Parse AMI's timed word streams and its laugh vocal-sound events per speaker, and ICSI's laugh tags, timed from adjacent words.
- Dialogue acts are the units. A dialogue act is "laughed after" if any participant laughs during its last second or within 2 seconds of its end.
- Every vocal-sound, laugh, "while laughing" and "breath-laugh" mark is removed from the text fed to either model and from the length match. A laugh inside an act's own span is outcome, never input.
- Two cautions from the literature, which shape the design:
  - in 1,200 laughs, laughter followed statements, questions and material that did not seem humorous outside the conversation ([Provine 1993](https://doi.org/10.1111/j.1439-0310.1993.tb00478.x)), and in his 2000 *Psychology Today* write-up of the same data only 10 to 20% followed anything joke-like;
  - an annotation study rejected the assumption that laughter directly follows what it laughs at ([Mazzocconi, Tian & Ginzburg 2020](https://doi.org/10.1109/TAFFC.2020.2994533)).
  
  So texture widens the window, and LA1 reads its result as a share of laughter, not all of it.
- Participant metadata: AMI native language; ICSI country, region and native language.

**Family ceiling:** 450,000 CPU-seconds.

**LA1. Does laughter follow resolution, or surprise?**
- **Two measures per dialogue act:**
  - **surprise:** its surprisal given the preceding talk, from AT2's best model;
  - **resolution:** how much more predictable the preceding five dialogue acts become once it is added. This is the pseudo-log-likelihood of those five acts under `distilroberta-base` with the act appended, minus without it, per token.
- **Design.** Laughed-after acts against up to five matched acts from the same meeting and speaker, matched on length and dialogue-act type, never laughed after. A conditional logistic model with both measures.
- **Primary:** the resolution coefficient controlling surprise, with a meeting-cluster interval. Bar: odds ratio 1.10 per standard deviation.
- **Rivals:**
  - Incongruity: surprise alone. Its coefficient is the comparison.
  - Resolution without a joke gives insight without mirth. A caption that resolves a puzzling picture gave "aha" but not "ha ha"; only captions linking remote ideas added mirth ([Amir et al. 2015](https://doi.org/10.1093/cercor/bht343)). That predicts a null on resolution alone, so the card can come out against the curator's idea.
- **By construction:** none once laugh marks are stripped. The match removes speaker, length and act type.
- **Branches.**
  - If resolution carries laughter: LA1.s, whether the laugh comes from the speaker or from others.
  - If surprise carries it: LA1.i, surprise followed by a drop in surprise over the next act.
- **Texture:**
  - window of 1 or 3 seconds, and any laugh within 5 seconds either side;
  - 3 or 10 preceding acts;
  - AMI and ICSI separately;
  - laughs by others only.
- **Ceiling:** 300,000 CPU-seconds, mostly the masked model.

**LA2. Do people who share background laugh together?**
- **Design.** For each pair of participants in a meeting, the share of one's laughs that the other joins within 1 second. Compare same-background pairs with different-background pairs, by native language (AMI; ICSI) and region (ICSI), within meeting, controlling each person's base laugh rate.
- **Primary:** the same-minus-different difference in joined share, with a meeting-cluster interval. Bar 0.02.
- **Route:** shared inference shows in shared laughter, on the encryption account of humor ([Flamson & Barrett 2008](https://doi.org/10.1556/JEP.6.2008.4.2)), which predicts this already.
- **Ceiling:** 20,000 CPU-seconds.

### 2.8 Family ID: an identity mark on people (Moral Machine)

**Family ceiling:** 40,000 CPU-seconds.

**ID1. Are steady refusers also insensitive to quantity?**
- **Design.** In the admitted SharedResponses archive, take fingerprints whose species choices always saved humans in the first half of their species scenarios (steady refusers), under B2's exposure-matched rule. Species scenarios always have equal numbers on both sides (Awad et al. 2018, Supplementary Information), so outnumbered choices come only from Random scenarios: those with humans on one side and pets on the other, read from the character-count columns.
- **Primary:** in the second half, the logit-scale slope of saving the human side on the base-2 log ratio of pets to humans, steady refusers minus others with the same number of first-half species scenarios, with a fingerprint-cluster interval. Quantity insensitivity, a protected-value mark ([Baron & Spranca 1997](https://doi.org/10.1006/obhd.1997.2690)), predicts a flatter slope for steady refusers. Bar: 0.2 log-odds per doubling of the ratio.
- **Case:** at least 500 outnumbered scenarios among steady refusers, counted in Random scenarios. Fallback: descriptive counts.
- **By construction:** steady refusers prefer humans more, so their saving rate is higher in every scenario; the level difference is reported for scale only. A ceiling near 100% flattens slopes on the probability scale, so slopes are compared on the logit scale.
- **Ceiling:** 20,000 CPU-seconds.

### 2.9 Family BK: Week 4's held and never-started work

These cards run as Week 4 designed them, under amendments K to M and these ceilings, which lift their cost holds.

| Card | Ceiling (CPU-seconds) | Note |
|---|---:|---|
| S2 complete replay, then its dependents | 4,000 | The source sub-allocation is gone (amendment L(a)) |
| T4 uncertainty | 60,000 | Screening at 200 resamples, then 2,000 for the primary |
| WD1 corrected calibration | 120,000 | Use the validated slower solver while the fast one fails its parity check |
| D7 follow-ups | 20,000 | |
| PP3.p1 | 35,000 | |
| CA1 encoding, then V1's consumer | 180,000 | CPU encoder at `e8f8c211`. V2 waits: its VAL coding was paid, and no paid work is commissioned this week |
| WB1 effects | 260,000 | After a cost probe charged here |
| PP1 full run | 150,000 | Idle slots |
| S3, T2 | as designed | Consumers unbuilt in Week 4; build them |
| WC2, FR1, TR5, WC4 | as designed | Unblocked since R1 passed on 2 November |
| ScholaWrite fallback | as designed | |

**Family ceiling:** 1,000,000 CPU-seconds.

## 3. Dispatch and builders

**At handoff, the owner:**
1. writes the amendments;
2. opens Week 5's policy and calendar, with the `transition_only` reset (section 0.1);
3. adds the four leases;
4. runs every retrieval check in section 0.5;
5. starts the BK queue in the original four slots, as they free.

**Builders** (amendment J) start at handoff:
- **Builder 1:** family CH, in order CH0, CH1, then CH2 to CH6. Stockfish batches fill any idle slot from the moment CH1's fixture passes.
- **Builder 2:** family AT, in order AT2's pipeline, AT1, AT3, AT4; then family LA.
- **Builder 3:** MD1 to MD3's consumers; then the intakes for IN, SP and GO; then IN1 to IN4, SP1 to SP3, GO1 to GO3; then ID1.
- **The owner:** BK and MD4, and every review.

**Dispatch order for ready cards:**
1. MD1 to MD3 (as soon as the source lands);
2. AT1;
3. IN1;
4. SP1 and SP2;
5. CH2;
6. AT2;
7. GO1;
8. CH4;
9. LA1;
10. everything else in section order.

**Idle slots** take, in this order:
1. CH1's Stockfish batches;
2. AT2's remaining models;
3. LA1's masked-model scoring;
4. GO's encoder passes;
5. BK's full runs;
6. texture cells.

Filler batches (CH1's Stockfish, AT2's remaining models, LA1's masked scoring, GO's encoder passes) are sized to at most 30 minutes of wall time each, so a newly ready card or a builder's native fixture never waits longer than that for a slot.

**Re-reading earlier results.** The curator asked on 7 November: "we want to make sure that the relationships between them are checked and that we aren't forgetting about how to use the new information if we find it to zero in further on old information and recursively somehow."
- Each landed primary's record names, by ID, the earlier rows in the theory files and FINDINGS.md that bear on it, and says for each whether the new result could change its reading.
- Where it could, the owner queues a re-read card: the earlier analysis rerun with the new result as a covariate, a filter, or a prior where the earlier analysis already takes one, under the earlier card's frozen rule, capped at half the earlier card's original ceiling and charged to the family of the result that prompted it. It never reads a Tier 4 holdout, is reported beside the original and never overwrites it.
- Re-read cards join the backlog and take idle slots.
- A re-read that changes a reading is itself a landed result and gets the same pass, at most two levels deep this week.
- A changed reading is recorded as a result, with its ledger row. Theory rows change only through the curator's theory pass, so a re-read doesn't by itself trigger the theory-change interrupt this week.

**Utilization rule.** The daily digest reports slot-hours occupied and idle by cause. If more than 25% of a day's slot-hours sat idle, the next turn first fills idle slots from the idle-slot list, then builds texture cells for landed or running cards, then resumes building section 2's cards.

## 4. What each result changes

| Result | Route to the engine |
|---|---|
| AT1 shared | Panel one uses a genre-adapted population model; no writer history needed |
| AT1 personal | Panel one needs the maker's own corpus when available (public essays with history) |
| AT2 | The engine's departure model is the best held-out fit at acceptable cost, or the current pair is confirmed |
| AT3 entropy | Panel one marks open choices as well as surprising words |
| AT4 at or above the bar | Panel one's attention display is licensed as a research preview at its measured AUC |
| CH2 and CH3 positive | Panel two marks long stops as planning, weighted by the maker's expertise |
| CH4 positive | The engine's set-point reader reads targets from restoring moves, with a measured number of records |
| CH6 | A first human estimate on whether gains in standing satiate |
| IN1's pooled primary positive | Panel three grades a channel by trigger fit only where that channel's own secondary also supports; channels against or inconclusive keep topic-free "untested" labels |
| IN4 | Panel three's confidence per trigger feature |
| SP2 and SP3 | Precision dynamics for the set-point reader's priors |
| GO1 at or above the bar | Panel three gets a measured top-level accuracy on stated goals |
| GO3 at or above the bar | The engine's revision reader gets a measured accuracy on writers' own reasons |
| LA1 resolution | A structural cue for panel three (textual laughter markers) |
| Any card unsupported or "design cannot test" | Recorded with counts, and its fallback runs |

## 5. Cross-repository

| To | What | When |
|---|---|---|
| Ghost, `docs/exchange/sounding-line-week5-2026-11-07/` | CH4 and SP results (for K3); IN1 to IN3 (for K4); AT1 and AT3 (for K6); LA1 (for K7); GO2 (for K6) | As each lands |
| ToMpathy, `docs/` | A reviewed handoff for each of AT2, AT4, CH2, CH3, GO1 and GO3. A raw result file isn't a handoff: ToMpathy requires a reviewed handoff for conditional changes. Each handoff states the estimate with its interval, its scope, the engine change it licenses or doesn't, and the pinned versions | As each lands |

Handing over this packet approves aggregate-only copies into Ghost's `docs/exchange` and ToMpathy's `docs/` by EV4's procedure (copy, hash, record). Don't commit or push in the recipient repository. The WA0 receiving copy still waits for the curator's destination confirmation.

## 6. Theory filing

At handoff, apply `SOUNDING_LINE_THEORY_ERRATA_2026-11-07.md` (supplied with this packet) by the 6 November procedure: parse its Part D edits exactly, apply them, and write a receipt with before and after hashes.

## 7. Reporting

- **Daily digest** at 20:00 PST, in this order:
  1. utilization: slot-hours occupied and idle, by cause; ready cards against amendment A's buffer (2 per slot); each builder's assignment and state;
  2. corrections, with their class;
  3. landed results, with ledger ids, control status, three-way outcome and route;
  4. texture counts per family.
- **Final digest** by Sunday 15 November, 20:00 PST:
  1. positives first, each with its route;
  2. a one-page engine readiness table: panels one, two and three, what each now has measured support for, and what it doesn't;
  3. nulls with their sensitivity;
  4. "design cannot test" records and fallbacks;
  5. operations, including the week's utilization.
- **Drain addendum** by 23:00 PST.

## 8. Pre-mortem

- **Slots idle again.** *Guard:* amendments I to K, three builders from handoff, Stockfish batches as an always-available filler, and section 3's utilization rule. The digest reports idle slot-hours by cause every day.
- **Hugging Face, Zenodo, archive.org or GitHub refuse the agent's retrieval.**
  - AT2 runs on the cached models (section 0.5).
  - MD1 to MD3 take the curator's local copy.
  - GO3 runs on whichever sites arrived.
  - GO1 and GO2 need git clones, which the agent already makes for this repository.
- **Stockfish is slower than projected.** *Guard:* fixed nodes, single-threaded engines, and the CH2, CH3 and CH5 primaries on the first 400,000 positions (CH4 and CH6 use clocks and ratings, not the engine). More positions only tighten intervals.
- **Chess time measures time pressure, not deliberation.** *Guard:* clock and increment controls, CH4's clock floor, and the premove filter.
- **Crowd-enVENT's single intensity rating can't separate channels.** *Guard:* every IN test compares texts within a prompted emotion; IN1's pooled slope uses prompt intercepts. Mixed feelings are out of scope this week.
- **Comfort slopes are an artefact of temperature range.** *Guard:* SP2's range-matched texture.
- **PEP Motivations are recoverable from shared vocabulary alone.** *Guard:* TF-IDF as the floor, same-type distractors, and GO1.d.
- **GO2 drifts toward the final text by construction.** *Guard:* the old-against-new goal comparison never uses the final text.
- **Laughter tags are noisy or untimed (ICSI).** *Guard:* AMI's timed tags first; ICSI as replication, with times from adjacent words.
- **Usernames leak through aggregates.** *Guard:* hashing at intake, aggregate outputs only, and no per-person tables.
- **Multiple comparisons.** *Guard:* one primary per card, every result descriptive, texture never upgrades a claim.

## 9. Triggers (the only reasons to contact the curator)

1. A result reverses a delivered public claim.
2. Privacy: any identity or raw text would leave the repository.
3. An outage longer than 12 hours.
4. A source's licence turns out, after intake, to forbid research use. Stop its cards and report.

## Sources

- **Week 4 and theory-days records**, at `dcbcc26de`:
  - `results/phase_2_4_stage_15/DRIVE/WEEK4_DIGEST_20261106.md`
  - `results/phase_2_4_stage_15/DRIVE/WEEK4_D33_PROMPT_EXCLUDED_FULL_20261105.md`
  - `results/phase_2_4_stage_15/THEORY_DAYS/HEALTH_20261107_0101.md`
  - `runners/theory_days/intake.py`
  - `AGENTS.md`
- **Zenodo record 4421847**, hashed by the analyst on 7 November.
- **Licences** as read on each source's official page or inside its archive, 7 November.
- **Literature:**
  - [Oh & Schuler 2023](https://aclanthology.org/2023.tacl-1.20)
  - [Medvegy et al. 2022](https://doi.org/10.1002/acp.3958)
  - [de Berker et al. 2016](https://doi.org/10.1038/ncomms10996)
  - [de Dear & Brager 1998](https://escholarship.org/uc/item/4qq2p9c6)
  - [Flamson & Barrett 2008](https://doi.org/10.1556/JEP.6.2008.4.2)
  - [Speakman et al. 2011](https://doi.org/10.1242/dmm.008698)
  - [Loewenstein, O'Donoghue & Rabin 2003](https://doi.org/10.1162/003355303322552784)
  - [Rottenstreich & Hsee 2001](https://doi.org/10.1111/1467-9280.00334)
  - [Kuppens et al. 2003](https://doi.org/10.1037/1528-3542.3.3.254)
  - [Troiano, Oberländer & Klinger 2023](https://arxiv.org/abs/2206.05238)
  - [Brager, Paliaga & de Dear 2004](https://escholarship.org/uc/item/4x57v1pf)
  - [Mazzocconi, Tian & Ginzburg 2020](https://doi.org/10.1109/TAFFC.2020.2994533)
  - [Provine 1993](https://doi.org/10.1111/j.1439-0310.1993.tb00478.x)
  - [Provine 2000, "The Science of Laughter", *Psychology Today*](https://www.psychologytoday.com/us/articles/200011/the-science-of-laughter)
  - [Amir et al. 2015](https://doi.org/10.1093/cercor/bht343)
  - [Baron & Spranca 1997](https://doi.org/10.1006/obhd.1997.2690)
  - [Awad et al. 2018](https://doi.org/10.1038/s41586-018-0637-6), [Supplementary Information](https://media.springernature.com/original/springer-static/esm/art%3A10.1038%2Fs41586-018-0637-6/MediaObjects/41586_2018_637_MOESM1_ESM.pdf)
  - [Evans, Dillon & Rand 2015](https://doi.org/10.1037/xge0000107)
  - Földváry Ličina et al. 2018, the ASHRAE Global Thermal Comfort Database II paper
