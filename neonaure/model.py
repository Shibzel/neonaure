"""
Neonaure - Model module

This module contains the core data structures and business logic:
- Grid, Motif, and Cell classes to represent the game state.
- Methods to load/save grids.
- TODO
"""


# class Cell:
#     """Represents a cell inside a pattern or a grid."""
#     def __init__(self, x, y, value) -> None:
#         self.x = x
#         self.y = y
#         self.value = value


class Pattern:
    """Represents a pattern (region, motif) in the grid."""

    def __init__(self, cells: list) -> None:
        self.cells = cells


class Grid:
    """Represents the Neonaure game grid, including dimensions, cells, and patterns."""

    def __init__(
        self,
        height: int,
        width: int,
        patterns: list[Pattern],
    ) -> None:
        pass

    def neighbours(self, x: int, y: int) -> list:
        """Returns a list of the closest neighbours of a grid."""
        pass


class Solver:
    """Solves the Neonaure grid. TODO"""

    def __init__(self) -> None:
        pass
