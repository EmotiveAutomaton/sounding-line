# Jester text input for the commissioned CPU pass

The complete 150-joke text input is prepared and independently verified. P7 has
not scored it; D36's ratings parser and scientific adapter remain unbuilt.

METHOD. Retain the official Berkeley repository's Dataset 3 source page and
archives at commit `4449c6e7f4a8d3644308f5c5edc7e11404ea808b`, verify exact transfer
sizes and SHA-256 hashes, and check every ZIP member's CRC. Extract spreadsheet
cells A1:A150 without changing their strings or row-based identities. A fresh
process reconstructs all strings directly from workbook XML and matches the
prepared JSON exactly, independently of the initial openpyxl reader. The 841
trailing workbook rows contain formatting only and are not additional jokes.

The [official release page](https://github.com/BerkeleyAutomation/Jester-Frontend/blob/4449c6e7f4a8d3644308f5c5edc7e11404ea808b/dataset/index.html)
identifies Dataset 3 as the update of Dataset 2 and permits research use with
acknowledgement of Goldberg, Roeder, Gupta and Perkins, *Eigentaste: A Constant
Time Collaborative Filtering Algorithm*, Information Retrieval 4(2), 133–151
(2001). Its conflicting user-count headings are not a verified rating census.
The ratings archive is retained and integrity-checked; worksheet validation and
rating summaries have not run. Dataset 4 is outside this intake.

[Aggregate manifest and verification](JESTER_TEXT_INTAKE.json) retain source URLs,
hashes and exact scope. All source bytes, extracted strings and private parser
receipts remain in the ignored local corpus cache. No scientific result,
statistical state, family counter, P7 admission or successor dispatch follows
from intake. Next: authenticate completed P6 and model inputs, validate P7's
checkpoint/resume behavior, and run its bounded execution pilot.
