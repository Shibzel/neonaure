"""
Neonaure

Authors :
    - Jean-François L. (contact@shibzel.me)
    - Adrien R.
    - Florian S.

Description :
    Module package for every function and objects that allows the game to run.
    Also contains a generic `run()` function that runs the game.
    See README.md for information about the project itself.
"""

__version__ = "O.1"


from .controller import *  # TODO: Spécifier les fonctions et classes à importer
from .model import Grid, Pattern, Solver, Cell, PatternAlreadyLoaded, CellIsImmuable
from .view import *  # Pareil ici

DEFAULT_GRID = "./data/grid/default.json"


def run(file: str = DEFAULT_GRID) -> None:
    raise NotImplementedError
