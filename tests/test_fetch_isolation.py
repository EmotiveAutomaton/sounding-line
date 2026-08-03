"""The fetch/analysis separation, tested rather than asserted.

SPEC §8's first non-negotiable:

    Split fetch from analysis into separate processes with separate privileges. Fetch writes to a
    content-addressed store and can reach the network. Analysis reads only from that store and
    has no network at all. They never share a process.

A separation that exists only in a docstring is a separation that will be violated by the next
convenient refactor. These tests make the violation fail loudly.
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
FETCHER = REPO / "fetch" / "fetcher.py"


def _imports(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names.update(a.name for a in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            names.add(node.module)
    return names


def test_fetcher_imports_nothing_from_the_analysis_package():
    """The process that touches the network must not know how to reach the probe.

    This is the load-bearing one. If the fetcher can import `soundingline`, a future edit can
    fetch a page and read it in the same process, and the whole of SPEC §8 becomes decorative.
    """
    bad = {n for n in _imports(FETCHER) if n.split(".")[0] == "soundingline"}
    assert not bad, (
        f"fetch/fetcher.py imports {sorted(bad)} from the analysis package. "
        f"SPEC §8: they never share a process."
    )


def test_analysis_package_never_imports_the_fetcher():
    """And the reverse: nothing under soundingline/ may reach the network side."""
    offenders = []
    for p in (REPO / "soundingline").rglob("*.py"):
        if any(n.split(".")[0] in {"fetch", "urllib", "requests", "httpx", "socket"}
               for n in _imports(p)):
            offenders.append(str(p.relative_to(REPO)))
    assert not offenders, f"analysis modules import network machinery: {offenders}"


def test_fetcher_refuses_hosts_outside_the_allowlist():
    import sys
    sys.path.insert(0, str(REPO / "fetch"))
    from fetcher import FetchRefused, Fetcher   # noqa: PLC0415

    f = Fetcher(allow_hosts={"example.com"}, store=REPO / "corpora" / "store")
    with pytest.raises(FetchRefused, match="allowlist"):
        f.fetch("https://evil.invalid/page")
    with pytest.raises(FetchRefused):
        f.fetch("file:///etc/passwd")
    with pytest.raises(FetchRefused):
        f.fetch("ftp://example.com/x")


def test_text_extraction_strips_executable_and_structural_noise():
    import sys
    sys.path.insert(0, str(REPO / "fetch"))
    from fetcher import _to_text   # noqa: PLC0415

    html = (b"<html><head><style>body{color:red}</style></head><body>"
            b"<script>alert('x')</script><nav>Home About</nav>"
            b"<p>The real content.</p><footer>copyright</footer></body></html>")
    out = _to_text(html, "text/html; charset=utf-8")
    assert "The real content." in out
    for gone in ("alert", "color:red", "Home About", "copyright"):
        assert gone not in out, f"{gone!r} survived extraction"


def test_store_is_not_committed():
    """SPEC §8: do not re-host the content. Hashes and offsets public, text private."""
    gitignore = (REPO / ".gitignore").read_text(encoding="utf-8")
    assert "corpora/store/" in gitignore
