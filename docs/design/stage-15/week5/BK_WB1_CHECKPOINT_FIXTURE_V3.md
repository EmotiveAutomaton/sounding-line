# WB1 checkpoint fixture variable correction

Source review found an unexecuted fixture defect in
`week5_bk_wb1_fixture_v2`: `pilot` first holds the coverage-pilot directory and
is later reused for the encoding pilot-bank JSON path. The subsequent
coverage-prefix assertion then treats that JSON file as a directory. No
numerical assertion is implicated, and no attempted fixture failure or spent
healing attempt is claimed: this was detected before execution.

`week5_bk_wb1_fixture_v3` changes only the four references to the first local
variable, naming it `coverage_probe`. Every original full coverage-pilot,
collection, raw-handler, numerical and continuation assertion is retained.
`week5_bk_wb1_checkpoint_fixture_v2` changes only its import to this corrected
full fixture; the original exact pinned small-model proof is unchanged.
The earlier v2 file and prepared manifest remain immutable and are locally
superseded for admission by this explicitly named successor.

## DESIGN CHECK

The case and check are the original complete WB1 checkpoint validation. The
separate directory and bank-file variables must reach their intended unchanged
assertions. Source comparison must show only those four identifier changes
and the outer import change. Native execute and fresh verification still need
to run; syntax or a textual diff does not qualify the handler.

The smaller route and proposed counted envelope remain unchanged: constructed
full raw/statistical plus pinned small-model checkpoint proof, 600 CPU seconds,
900 wall seconds, 3 GiB projected peak, two numerical threads, backlog family
on an original bank slot. This successor has not been run or admitted. Owner
review and a committed design precede launch. All old charges and artifacts
remain; the correction changes no model, scientific estimator or sample.
