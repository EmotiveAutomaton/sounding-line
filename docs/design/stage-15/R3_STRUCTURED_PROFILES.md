# R3 structured-profile repair

The October 15 curator instruction advances execution now under the existing
next-round commission and shared campaign ceiling. This does not add a tranche.
The original failed Stage 14 profile pilot remains unchanged. Stage 15 owns this
new attempt and any later feature evaluation; it does not reopen Stage 14.

Use the same discarded three-writer pilot and own/donor past-only histories,
with six requests. The separately held main has 31 writers and 62 requests.
Sonnet 5.5 returns structured JSON with at most twelve statements, each under
25 words, supported by indices into the supplied history. Maximum output is
1,500 tokens. The exact schema is visible in the message and constrained decoder.
Targets and their outcomes do not reach profile generation. Duplicate keys,
invalid indices, empty or repeated statements, truncation and missing requests
fail admission. No response is silently clipped or retried.

All six pilot profiles must pass literal validation and full write-through before
main submission. Index validity does not establish semantic faithfulness. Profiles
remain candidate features: usefulness requires the commissioned backbone controls,
frozen evaluation and applicable engine/twin gates. They never become judges.

The new versioned adapter calls the unchanged campaign reservation API, which
executes `runners/gear3.py`'s canonical locked ledger functions. This retains the
existing campaign and node ceilings, duplicate-attempt refusal and uncertain-cost
reservation. It leaves historical dispatcher and source bytes unchanged; there
is no bare provider dispatch without that guard. Pilot uses the original pilot
node; main uses the original API node. Reserve funds remain unavailable.

Current [official pricing](https://platform.claude.com/docs/en/about-claude/pricing)
supports batch rates of $1 input and $5 output per million tokens. Count each
actual request, add 30% input allowance and maximum output, round up, then add
two cents. Reserve before the sole submission. Credential access and exact model
identity must pass first. No tools, caching, redirects, retries or substitutions.
An ambiguous submission retains its reservation and wakes the owner.

The exact native supervisor registers completion/failure/disappearance before
dispatch and retrieves read-only every two minutes for at most one day. This
service polling does not add model wakes or change the six-hour health clock.
Ended ownership plus complete token accounting is required for reconciliation.
No automatic main follows. Raw human evidence, provider identities and credentials
remain local; public records contain aggregate counts and hashes.

Implementation: `runners/next_round/profiles.py` and `profile_supervisor.py`.
Eleven targeted checks cover parser failures, real evidence separation, full
fake-provider submission/retrieval/replay, duplicate refusal and uncertain POST.
These checks establish software behavior, not live model or scientific admission.
