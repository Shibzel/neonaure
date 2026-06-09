"""
Neonaure Game

Authors :
    - Shibzel (contact@shibzel.me)
    - Adrien R.
    - Florian S.

Description :
    TODO
    See README.md for information about the project itself.
"""

__version__ = "O.1"


# from .controller import *
# from .view import *
from .model import Grid, Pattern, Solver

DEFAULT_GRID = "./data/grid/default.json"


def run(file: str = DEFAULT_GRID) -> None:
    pass
