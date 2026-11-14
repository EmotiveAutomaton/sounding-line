# CH10 fixture denominator annotation

Prepared November 13, 2026 before native tests. Original v1 preparation remains.
The v2 fixture reports equivalent binary-trial counts for every model branch,
including unsupported targets; it no longer mixes compressed-cell units into
those branches. All production history/model bytes and declared truths are
unchanged. The explicit expansion check now includes both 10/100 loss and14/100
win cells, so it checks a nonzero cross-product as well as denominators.

## DESIGN CHECK

The primary fixture's unsupported eight-lag branch still represents all48 cells
for300 people, each containing100000 binary trials. Its row count must say so.
There was no native failure or source run; this is a static annotation repair.
Complete planted-primary and decay controls plus independent replay remain
required, with no change to the approved two-plus-win-bonus specification.
