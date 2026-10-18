import json
import os
from pathlib import Path
import subprocess
import sys

import pytest

from runners.drive.cards import timing_schola_intake as card
from runners.drive.cards.timing_census import write, read, filehash


def fixture_inputs(root):
    root = Path(root).resolve()
    schema = root / "schema.json"
    write(schema, dict(features={k: {} for k in card.EXPECTED_FIELDS}, splits=dict(all_sorted=dict(num_examples=5))))
    raw = root / "held-source.bin"
    raw.write_bytes(b"synthetic source bytes; no participant data")
    identity = root / "identity.json"
    write(identity, dict(source_files=dict(files={p.relative_to(root).as_posix():filehash(p) for p in [schema, raw]})))
    review, summary = root / "review.json", root / "summary.json"
    write(review, dict(author_ids="project scoped, not established global people"))
    write(summary, dict(source_rows=5, projects=2, project_scoped_author_ids=4))
    return dict(repo_root=str(root), source_schema=str(schema), source_identity=str(identity), source_review=str(review), prepared_summary=str(summary))


def test_serialized_intake_and_fresh_source_verification(tmp_path):
    inputs = fixture_inputs(tmp_path / "source")
    output = tmp_path / "output"
    write(output / "YIELD_REQUEST.json", {})
    assert card.execute(output, inputs, card.CONFIG)["status"] == "yielded"
    (output / "YIELD_REQUEST.json").unlink()
    result = card.execute(output, inputs, card.CONFIG)
    assert result["dependency_state"] == "held"
    assert not result["scientific_result"]
    assert len(result["missing_dependencies"]) == 4
    manifest = tmp_path / "verify.json"
    write(manifest, dict(inputs=inputs, output=str(output), config=card.CONFIG))
    code = "import json,sys; from pathlib import Path; from runners.drive.cards.timing_schola_intake import verify; x=json.load(open(sys.argv[1])); print(json.dumps(verify(Path(x['output']),x['inputs'],x['config'])))"
    child = subprocess.run([sys.executable, "-c", code, str(manifest)], text=True, capture_output=True, timeout=30,
                           env=dict(os.environ, PYTHONHASHSEED="431"), creationflags=subprocess.BELOW_NORMAL_PRIORITY_CLASS if os.name == "nt" else 0)
    assert child.returncode == 0, child.stderr
    assert json.loads(child.stdout)["primary"] == result
    raw = Path(inputs["repo_root"]) / "held-source.bin"
    raw.write_bytes(b"changed")
    with pytest.raises(ValueError, match="source changed"):
        card.verify(output, inputs, card.CONFIG)


def test_invented_global_identity_and_changed_schema_refuse(tmp_path):
    inputs = fixture_inputs(tmp_path)
    review = Path(inputs["source_review"])
    review.write_text(json.dumps(dict(author_ids="numeric IDs identify global people")), encoding="utf-8")
    with pytest.raises(ValueError, match="identity contract"):
        card.inspect(inputs, card.CONFIG)
    with pytest.raises(ValueError, match="configuration"):
        card.inspect(inputs, dict(card.CONFIG, version=True))
