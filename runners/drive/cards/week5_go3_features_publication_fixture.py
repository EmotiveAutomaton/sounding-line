"""Same original-model/full-row fixture, with UUID publication and identity."""
from pathlib import Path
from . import week5_go3_features_collected_fixture as original
from . import week5_go3_publication as publication

MODULE = 'runners.drive.cards.week5_go3_features_publication_fixture'
SOURCES = [Path(__file__), Path(original.__file__), Path(original.features.__file__),
           Path(original.features.analysis.__file__), Path(original.features.core.__file__)]


def execute(output, inputs, config):
    return publication.invoke(original.execute, output, inputs, config,
                              module=MODULE, sources=SOURCES, core=original.features.core)


def verify(output, inputs, config):
    return publication.invoke(original.verify, output, inputs, config,
                              module=MODULE, sources=SOURCES, core=original.features.core, verify=True)
