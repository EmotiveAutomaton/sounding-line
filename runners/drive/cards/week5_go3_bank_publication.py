"""Unchanged full-bank statistics accepting the exact UUID feature producer."""
from pathlib import Path
from . import week5_go3_bank_analysis as original
from . import week5_go3_features_publication as feature
from . import week5_go3_publication as publication

MODULE = 'runners.drive.cards.week5_go3_bank_publication'
SOURCES = [Path(__file__), Path(original.__file__), Path(original.original.__file__),
           Path(original.core.__file__), *feature.SOURCES]


def execute(output, inputs, config):
    publication.require_complete_identity(inputs['feature_run'], module=feature.MODULE, sources=feature.SOURCES)
    return publication.invoke(lambda out, ins, cfg: original.run(out, ins, cfg, feature.MODULE),
                              output, inputs, config, module=MODULE, sources=SOURCES, core=original.core)


def verify(output, inputs, config):
    publication.require_complete_identity(inputs['feature_run'], module=feature.MODULE, sources=feature.SOURCES)
    return publication.invoke(lambda out, ins, cfg: original.verify_run(out, ins, cfg, feature.MODULE),
                              output, inputs, config, module=MODULE, sources=SOURCES, core=original.core, verify=True)
