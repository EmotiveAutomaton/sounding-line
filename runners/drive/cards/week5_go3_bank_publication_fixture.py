"""Original actual-bank fixture with only its expected producer identity changed."""
from pathlib import Path
from . import week5_go3_bank_analysis_fixture as original
from . import week5_go3_features_publication_fixture as feature
from . import week5_go3_publication as publication

MODULE = 'runners.drive.cards.week5_go3_bank_publication_fixture'
SOURCES = [Path(__file__), Path(original.__file__), Path(original.bank.__file__),
           Path(original.bank.original.__file__), Path(original.bank.core.__file__), *feature.SOURCES]


def execute(output, inputs, config):
    publication.require_complete_identity(inputs['feature_run'], module=feature.MODULE, sources=feature.SOURCES)
    with publication.alias(original, 'FEATURE_FIXTURE', feature.MODULE):
        return publication.invoke(original.execute, output, inputs, config,
                                  module=MODULE, sources=SOURCES, core=original.bank.core)


def verify(output, inputs, config):
    publication.require_complete_identity(inputs['feature_run'], module=feature.MODULE, sources=feature.SOURCES)
    with publication.alias(original, 'FEATURE_FIXTURE', feature.MODULE):
        return publication.invoke(original.verify, output, inputs, config,
                                  module=MODULE, sources=SOURCES, core=original.bank.core, verify=True)
