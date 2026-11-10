"""Original complete sixteen-world mathematical proof with UUID publication."""
from pathlib import Path
from . import week5_go3_bank_math_fixture as original
from . import week5_go3_publication as publication

MODULE = 'runners.drive.cards.week5_go3_math_publication_fixture'
SOURCES = [Path(__file__), Path(original.__file__), Path(original.fixture.__file__),
           Path(original.bank.__file__), Path(original.bank.original.__file__), Path(original.bank.core.__file__)]


def execute(output, inputs, config):
    return publication.invoke(original.execute, output, inputs, config,
                              module=MODULE, sources=SOURCES, core=original.bank.core)


def verify(output, inputs, config):
    return publication.invoke(original.verify, output, inputs, config,
                              module=MODULE, sources=SOURCES, core=original.bank.core, verify=True)
