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

from __future__ import annotations

__version__: str = "0.1"

from .controller import Controller
from .model import Cell, CellIsImmuable, Grid, Pattern, PatternAlreadyLoaded, Solver
from .view import GridView, MainWindow, NumberSelector

DEFAULT_GRID: str = "./data/grids/default.json"


def run(file: str = DEFAULT_GRID) -> None:
    raise NotImplementedError
