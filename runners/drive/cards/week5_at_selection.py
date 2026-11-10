"""Selected-reader numerical provenance; complete AT2 selection only."""
from pathlib import Path
from .week5_at_source import authenticate
from .week5_at_scoring import digest
from .week5_at_scoring_v4 import NUMERICAL_SPEC
from .timing_census import read


def selected_reader(selection_root,manifest):
    root=authenticate(selection_root);result=read(root/'output/RESULT.json');binding=read(root/'output/READER_BINDING.json')
    if result.get('card')!='AT2' or result.get('screening_only') or not result.get('selection_admissible'):
        raise ValueError('Completed primary AT2 reader selection required')
    if (binding.get('numerical_spec')!=NUMERICAL_SPEC or binding.get('model')!=result.get('selected_model') or
        binding.get('model')!=manifest.get('model') or binding.get('revision')!=manifest.get('revision') or
        binding.get('manifest_sha256')!=digest(manifest)):
        raise ValueError('Selected reader numerical/revision/manifest binding differs')
    return binding
