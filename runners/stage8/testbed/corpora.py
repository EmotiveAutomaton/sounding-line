"""T02: the human-input corpora fetched AS MANIFESTS under the fetch discipline
(fetch/fetcher.py: an allowlist, robots and rate limits honored, a content-addressed store
that is gitignored, hashes and URLs and lengths in the manifest, no re-hosting, never
re-fetched during an experiment). What is fetched is each corpus's landing page, README,
license text, and any small index or sample file the discipline admits (text, at most four
megabytes); bulk data stays where it is and the catalog card says so.

DESIGN CHECK (2026-09-04)
lessons read: LESSONS §2 (a loader over someone else's data is validated on a fixture
  before a count is quoted), §5 (network only in the fetch side; time-boxed).
gates: T02: NULL of an undisciplined manifest is any item without a hash, URL, length, and
  license field, or a fetch off the allowlist (fails DOWN: that item MANIFEST_FAILED);
  ALTERNATIVE: every item carries the four fields. bands: exhaustive.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO))

from fetch.fetcher import Fetcher, FetchRefused                                    # noqa: E402
from soundingline.stage8 import now_iso, update_registry                          # noqa: E402

MANIFEST = REPO / "corpora" / "manifests" / "stage8_testbed.json"
ALLOW = {"github.com", "raw.githubusercontent.com", "huggingface.co", "arxiv.org", "www.cs.cornell.edu",
         "www.woolfonline.com", "woolfonline.com", "shelleygodwinarchive.org", "www.shelleygodwinarchive.org", "aclanthology.org"}

CORPORA = {
    "argrewrite_v2": {"in_hand": True, "path": "corpora/public/argrewrite", "human_input": "readers' inferred revision purposes (the reader-guess corpus)",
                      "card": "the reader-guess corpus", "urls": []},
    "newsedits_2": {"human_input": "professional editors' intention labels; a prospective update task with published baselines",
                    "card": "the real-record ceiling",
                    "urls": ["https://raw.githubusercontent.com/isi-nlp/newsedits/master/README.md", "https://raw.githubusercontent.com/isi-nlp/newsedits/master/LICENSE"]},
    "arxivedits": {"human_input": "annotator intention labels on real revisions", "card": "small, clean intention truth",
                   "urls": ["https://arxiv.org/abs/2210.15067", "https://raw.githubusercontent.com/chaojiang06/arXivEdits/main/README.md"]},
    "iterater": {"human_input": "annotator intention labels on real revisions", "card": "small, clean intention truth",
                 "urls": ["https://raw.githubusercontent.com/vipulraheja/iterater/main/README.md", "https://raw.githubusercontent.com/vipulraheja/iterater/main/LICENSE",
                          "https://huggingface.co/datasets/wanghaoxu/IteraTeR_full_sent"]},
    "genius_expertise": {"human_input": "crowd inferences and, where obtainable, the maker's own statements on the same lines", "card": "the human bridge without recruitment; licensing is the catch",
                         "urls": ["https://www.cs.cornell.edu/~arb/data/genius-expertise/"]},
    "woolf_online": {"human_input": "drafts with scholarly commentary", "card": "one maker across drafts",
                     "urls": ["http://www.woolfonline.com/"]},
    "shelley_godwin": {"human_input": "manuscript drafts with editorial transcription (a second genetic edition)", "card": "one maker across drafts",
                       "urls": ["https://shelleygodwinarchive.org/"]},
    "commitbench": {"human_input": "makers' stated intentions per change (commit messages) in code; a domain caveat", "card": "stated proximal goals at scale, in code",
                    "urls": ["https://huggingface.co/datasets/Maxscha/commitbench"]},
    "coauthor": {"in_hand": True, "path": "corpora/coauthor", "human_input": "the writer's suggestion decisions (accept, edit, dismiss, ignore)", "card": "already measured (Stage 7 P13)", "urls": []},
    "scholawrite": {"in_hand": True, "path": "", "human_input": "the writer's own labels on keystroke-level revision", "card": "already measured (Stage 7 P14)", "urls": []},
}


def fetch_all() -> dict:
    f = Fetcher(allow_hosts=ALLOW)
    items = {}
    for name, spec in CORPORA.items():
        recs = []
        for url in spec.get("urls") or []:
            try:
                r = f.fetch(url)
                text = f.read(r)
                lic = "see page"
                low = text.lower()
                for tag in ("mit license", "apache license", "cc by-nc-sa", "cc by-nc", "cc by-sa", "cc by 4.0", "cc-by", "creative commons", "bsd", "gpl", "all rights reserved"):
                    if tag in low:
                        lic = tag
                        break
                recs.append({"url": url, "final_url": r.final_url, "sha256": r.sha256, "n_chars": r.n_chars, "content_type": r.content_type,
                             "robots_allowed": r.robots_allowed, "license_hint": lic, "fetched_at": r.fetched_at})
            except FetchRefused as e:
                recs.append({"url": url, "refused": str(e)[:200]})
            except Exception as e:                                                # noqa: BLE001
                recs.append({"url": url, "error": repr(e)[:200]})
        n_local = None
        if spec.get("in_hand") and spec.get("path"):
            p = REPO / spec["path"]
            n_local = sum(1 for x in p.rglob("*") if x.is_file()) if p.exists() else 0
        items[name] = {**{k: v for k, v in spec.items() if k != "urls"}, "fetched": recs, "n_local_files": n_local,
                       "status": ("IN_HAND" if spec.get("in_hand") else ("MANIFESTED" if recs and all("sha256" in r for r in recs) else ("MANIFEST_PARTIAL" if any("sha256" in r for r in recs) else "MANIFEST_FAILED")))}
    out = {"name": "stage8_testbed", "written_at": now_iso(), "policy": "manifests only: hashes, URLs, lengths, license hints; text in the gitignored store; bulk data never re-hosted", "items": items}
    MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    MANIFEST.write_text(json.dumps(out, indent=1), encoding="utf-8", newline="\n")
    update_registry("CORPUS_MANIFESTS", lambda c: {**c, "manifest": str(MANIFEST), "items": {k: v["status"] for k, v in items.items()}, "written_at": now_iso()})
    return out
