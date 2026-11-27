"""ADP1 Week 8 first-play entry."""
from . import week8_game as game


def design(unit):
    return game.design('ADP1',unit)


fixture = game.fixture


def run(unit,d,mode):
    game.run('ADP1',d,mode)


def check(unit,d):
    return game.check(d)
