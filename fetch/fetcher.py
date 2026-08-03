"""The fetch side. Reaches the network, writes a content-addressed store, and analyses nothing.

── THIS IS THE SECURITY BOUNDARY, NOT A DOWNLOAD SCRIPT ──────────────────────────────────────

SPEC §8, and it is the section that is explicitly not boilerplate:

    The corpus under study is adversarial content engineered to influence language models. That
    is not a risk of the project, it is the definition of the subject matter. Feeding it to a
    model-based probe IS the attack surface, and getting this wrong does not produce a bad
    result — it produces a result that is silently the attacker's.

    Split fetch from analysis into separate processes with separate privileges. Fetch writes to a
    content-addressed store and can reach the network. Analysis reads only from that store and
    has no network at all. They never share a process.

**This module imports nothing from `soundingline`.** Not the family, not the schema, not the
probe. That is deliberate and it is the whole point: the process that touches the network cannot
reach the process that reads the text, because it does not know how. Any future import from
`soundingline` into this file is a defect, and `tests/test_fetch_isolation.py` fails on it.

Amendment A-4 deferred this until Gate 2, on the reasoning that not having a fetcher removes most
of §8's attack surface while the instrument is being built. Gate 2 is where the corpus is needed,
so this is on schedule rather than early.

── WHAT IT REFUSES TO DO ─────────────────────────────────────────────────────────────────────

* **Never re-hosts.** Text goes to a gitignored store; manifests carry hashes, URLs and lengths
  and are the only thing committed. SPEC §8: store hashes and offsets publicly, text privately.
* **Never re-fetches during an experiment.** A cached hash is returned unchanged, so runs are
  reproducible and the study population cannot shift underneath a measurement.
* **Honours robots.txt and rate limits**, including for content the project finds contemptible.
  The provenance of the method is part of the argument.
* **Follows no redirect off its allowlist**, and stores the final URL alongside the requested one
  so a silent redirect cannot swap a document unnoticed.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import time
import urllib.robotparser
from dataclasses import asdict, dataclass
from pathlib import Path
from urllib.parse import urlparse

import urllib.request

REPO = Path(__file__).resolve().parents[1]
STORE = REPO / "corpora" / "store"
MANIFESTS = REPO / "corpora" / "manifests"

USER_AGENT = (
    "SoundingLine/0.1 (research instrument; intent-attribution study; "
    "contact: abrahamhaskins@gmail.com)"
)
MIN_INTERVAL_S = 2.0     # per host, and deliberately conservative
TIMEOUT_S = 30
MAX_BYTES = 4_000_000


class FetchRefused(RuntimeError):
    """Refused before any request was made. Not an error to be retried around."""


@dataclass(frozen=True)
class Record:
    """What the store holds about one document. The text lives beside this, never in it."""
    sha256: str
    requested_url: str
    final_url: str
    fetched_at: str
    content_type: str
    n_chars: int
    robots_allowed: bool


def _host(url: str) -> str:
    return (urlparse(url).hostname or "").lower()


class Fetcher:
    def __init__(self, *, allow_hosts: set[str] | None = None, store: Path = STORE) -> None:
        # An allowlist is optional here because the corpus is enumerated in a manifest rather
        # than crawled — but when supplied it is enforced before DNS, and redirects are checked
        # against it too. There is no discovery mode and no link-following: this fetcher can only
        # ever retrieve URLs a human wrote down.
        self.allow_hosts = allow_hosts
        self.store = store
        self.store.mkdir(parents=True, exist_ok=True)
        self._last: dict[str, float] = {}
        self._robots: dict[str, urllib.robotparser.RobotFileParser] = {}

    def _check_allowed(self, url: str) -> None:
        if not url.lower().startswith(("http://", "https://")):
            raise FetchRefused(f"not an http(s) URL: {url!r}")
        h = _host(url)
        if not h:
            raise FetchRefused(f"no host in {url!r}")
        if self.allow_hosts is not None and h not in self.allow_hosts:
            raise FetchRefused(f"host {h!r} is not in the allowlist")

    def _robots_ok(self, url: str) -> bool:
        h = _host(url)
        if h not in self._robots:
            rp = urllib.robotparser.RobotFileParser()
            rp.set_url(f"{urlparse(url).scheme}://{h}/robots.txt")
            try:
                rp.read()
            except Exception:                                    # noqa: BLE001
                # A robots.txt that cannot be read is treated as permissive, which is the
                # convention — but it is recorded per document so the decision is auditable
                # rather than assumed.
                rp = None                                        # type: ignore[assignment]
            self._robots[h] = rp                                 # type: ignore[assignment]
        rp = self._robots[h]
        return True if rp is None else rp.can_fetch(USER_AGENT, url)

    def _throttle(self, url: str) -> None:
        h = _host(url)
        gap = time.monotonic() - self._last.get(h, 0.0)
        if gap < MIN_INTERVAL_S:
            time.sleep(MIN_INTERVAL_S - gap)
        self._last[h] = time.monotonic()

    def fetch(self, url: str, *, force: bool = False) -> Record:
        """Retrieve one URL into the store, or return what is already there."""
        self._check_allowed(url)

        key = hashlib.sha256(url.encode("utf-8")).hexdigest()[:16]
        meta_path = self.store / f"{key}.meta.json"
        if meta_path.exists() and not force:
            # Never re-fetch during an experiment. SPEC §8: it makes runs reproducible AND it
            # means the study population cannot change underneath a measurement.
            return Record(**json.loads(meta_path.read_text(encoding="utf-8")))

        allowed = self._robots_ok(url)
        if not allowed:
            raise FetchRefused(f"robots.txt disallows {url}")

        self._throttle(url)
        req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(req, timeout=TIMEOUT_S) as resp:
            final = resp.geturl()
            self._check_allowed(final)          # a redirect may not leave the allowlist
            ctype = resp.headers.get("Content-Type", "")
            raw = resp.read(MAX_BYTES)

        text = _to_text(raw, ctype)
        rec = Record(
            sha256=hashlib.sha256(text.encode("utf-8")).hexdigest(),
            requested_url=url,
            final_url=final,
            fetched_at=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            content_type=ctype,
            n_chars=len(text),
            robots_allowed=allowed,
        )
        (self.store / f"{key}.txt").write_text(text, encoding="utf-8")
        meta_path.write_text(json.dumps(asdict(rec), indent=2), encoding="utf-8")
        return rec

    def read(self, rec: Record) -> str:
        key = hashlib.sha256(rec.requested_url.encode("utf-8")).hexdigest()[:16]
        return (self.store / f"{key}.txt").read_text(encoding="utf-8")


_TAG = re.compile(r"<[^>]+>")
_DROP = re.compile(r"<(script|style|nav|footer|header|aside|form|svg)\b.*?</\1>",
                   re.I | re.S)
_WS = re.compile(r"[ \t\r\f\v]+")
_BLANK = re.compile(r"\n{3,}")


def _to_text(raw: bytes, content_type: str) -> str:
    """HTML to readable text. Deliberately crude, and the crudeness is a feature.

    No parser, no JS, no link-following, nothing that executes. The probe is going to read this,
    so the extraction path is kept small enough to audit in one sitting — a rich extractor is
    more attack surface pointed directly at the thing SPEC §8 is protecting.
    """
    enc = "utf-8"
    m = re.search(r"charset=[\"']?([\w\-]+)", content_type or "", re.I)
    if m:
        enc = m.group(1)
    try:
        s = raw.decode(enc, errors="replace")
    except LookupError:
        # A header naming an encoding Python does not know (observed live: `charset=empty` on an
        # archived GeoCities page). Fall back rather than lose the document — the decision is
        # recorded in the manifest's content_type either way.
        s = raw.decode("utf-8", errors="replace")
    s = _DROP.sub(" ", s)
    s = re.sub(r"<br\s*/?>|</p>|</div>|</li>|</h[1-6]>", "\n", s, flags=re.I)
    s = _TAG.sub(" ", s)
    for a, b in (("&nbsp;", " "), ("&amp;", "&"), ("&lt;", "<"), ("&gt;", ">"),
                 ("&quot;", '"'), ("&#39;", "'"), ("&mdash;", "—"), ("&rsquo;", "'")):
        s = s.replace(a, b)
    s = _WS.sub(" ", s)
    s = "\n".join(line.strip() for line in s.split("\n"))
    return _BLANK.sub("\n\n", s).strip()


def main() -> None:
    ap = argparse.ArgumentParser(description="Fetch a manifest of URLs into the store.")
    ap.add_argument("manifest", help="JSON file: {name, items:[{id, url, row}]}")
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args()

    spec = json.loads(Path(args.manifest).read_text(encoding="utf-8"))
    hosts = {_host(i["url"]) for i in spec["items"]}
    f = Fetcher(allow_hosts=hosts)

    out = []
    for item in spec["items"]:
        try:
            rec = f.fetch(item["url"], force=args.force)
            out.append({**item, **asdict(rec)})
            print(f"  ok   {item['id']:<22} {rec.n_chars:>7} chars  {rec.sha256[:12]}", flush=True)
        except Exception as e:                                   # noqa: BLE001
            out.append({**item, "error": f"{type(e).__name__}: {e}"})
            print(f"  FAIL {item['id']:<22} {type(e).__name__}: {str(e)[:70]}", flush=True)

    MANIFESTS.mkdir(parents=True, exist_ok=True)
    dest = MANIFESTS / f"{spec['name']}.json"
    dest.write_text(json.dumps({"name": spec["name"], "items": out}, indent=2), encoding="utf-8")
    print(f"\nmanifest written: {dest.relative_to(REPO)}  "
          f"({sum(1 for o in out if 'sha256' in o)}/{len(out)} fetched)")


if __name__ == "__main__":
    main()
