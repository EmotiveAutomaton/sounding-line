"""Publication-only successor to the frozen complete GO3 feature producer."""
from pathlib import Path
from . import week5_go3_features_collected as original
from . import week5_go3_publication as publication

MODULE = 'runners.drive.cards.week5_go3_features_publication'
SOURCES = [Path(__file__), Path(original.__file__), Path(original.analysis.__file__), Path(original.core.__file__)]


def execute(output, inputs, config):
    return publication.invoke(original.execute, output, inputs, config,
                              module=MODULE, sources=SOURCES, core=original.core)


def verify(output, inputs, config):
    return publication.invoke(original.verify, output, inputs, config,
                              module=MODULE, sources=SOURCES, core=original.core, verify=True)
