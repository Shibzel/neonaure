"""
Neonaure - Model module

This module contains the core data structures and business logic:
- Grid, Motif, and Cell classes to represent the game state.
- Methods to load/save grids.
- TODO
"""

import json

PATTERN_KEY_STARTS_WITH = "motif"


class PatternAlreadyLoaded(RuntimeError):
    pass


class CellIsImmuable(Exception):
    pass


def load_json(file_path: str) -> dict | list:
    """Loads the contents of a json file. Either returns a dict or a list."""
    with open(file_path, "r") as file:
        return json.load(file)


def save_json(file_path: str, data: dict | list) -> None:
    """Saves a dict or an array like struct into a json file."""
    with open(file_path, "w+") as file:
        json.dump(data, file, indent=None)


class Cell:
    def __init__(self, x, y, value: int = 0, immuable: bool = False) -> None:
        self.x = x
        self.y = y
        self.value = value
        self.immuable = immuable

    def __str__(self) -> str:
        return f"({self.x}, {self.y}) with value {self.value}"

    def to_list(self) -> list:
        return [self.x, self.y, self.value, self.immuable]

    def set_value(self, value: int) -> None:
        if self.immuable:
            raise CellIsImmuable(f"Cell `{self}` is immuable cannot be edited.")
        self.value = value


class Pattern:
    """Represents a pattern (region, motif) in the grid."""

    def __init__(self, name: str, cells: list[Cell] | None = None) -> None:
        self.name = name
        self.cells = cells or []

    def to_list(self) -> list:
        return [cell.to_list() for cell in self.cells]

    def set_cell(self, x: int, y: int, value: int, immuable: bool = False) -> None:
        for cell in self.cells:
            if cell.x == x and cell.y == y:
                cell.set_value(value)
                break
        else:  # Cellule absente du motif
            self.cells.append(Cell(x, y, value, immuable))

    @classmethod
    def from_raw_cells(cls, name: str, raw_cells: list) -> "Pattern":
        instance = cls(name)
        for cell in raw_cells:
            # Logique d'immuabilité :
            # Si la cellule a 4 éléments, cela veut dire qu'elle provient d'une save,
            #   donc on vérifie la 4ème valeur pour sa valeur d'immuabilité (True = non mutable)
            # Si il n'y a que 3 éléments, alors la cellule est immuable car chargée
            #   depuis un json externe (nouvelle partie)
            immuable = False
            if (len(cell) == 3) and (cell[2] != 0):
                immuable = True
            elif len(cell) > 3:
                immuable = cell[3]
            instance.set_cell(cell[0], cell[1], cell[2], immuable)
        return instance


class Grid:
    """Represents the Neonaure game grid, including dimensions, cells, and patterns."""

    def __init__(self, patterns: list[Pattern]) -> None:
        self.patterns = []
        for pattern in patterns:
            self._add_pattern(pattern)
        self.height = self.width = None
        x, y = self.get_dimensions()
        self.matrix = [[None for _ in range(x)] for _ in range(y)]
        self._fill_matrix()

    def to_dict(self) -> dict:
        return {pattern.name: pattern.to_list() for pattern in self.patterns}

    def _fill_matrix(self) -> None:
        for pattern in self.patterns:
            for cell in pattern.cells:
                self.matrix[cell.y][cell.x] = cell

    def _add_pattern(self, pattern: Pattern) -> None:
        for p in self.patterns:
            if p.name == pattern.name:
                raise PatternAlreadyLoaded(
                    f"Pattern with name '{pattern.name}' is already loaded."
                )
        self.patterns.append(pattern)

    def get_dimensions(self) -> tuple[int, int]:
        if (self.height is None) or (self.width is None):
            self.height = self.width = 0
            for pattern in self.patterns:
                for cell in pattern.cells:
                    if cell.x > self.width:
                        self.width = cell.x + 1
                    if cell.y > self.height:
                        self.height = cell.y + 1
        return self.width, self.height

    def neighbours(self, x: int, y: int) -> list:
        """Returns a list of the closest neighbours of a grid."""
        raise NotImplementedError

    @classmethod
    def from_data(cls, data: dict) -> "Grid":
        patterns = []
        for key, val in data.items():
            # La clé se doit de commencer par "motif"
            if key.startswith(PATTERN_KEY_STARTS_WITH):
                patterns.append(Pattern.from_raw_cells(key, val))
        instance = cls(patterns)
        return instance

    @classmethod
    def from_json(cls, file_path: str):
        data: dict = load_json(file_path)
        return cls.from_data(data)

    def save_grid_to_json(self, file_path: str) -> None:
        save_json(file_path, self.to_dict())


class Solver:
    """Solves the Neonaure grid. TODO"""

    def __init__(self, grid: Grid) -> None:
        self.grid = grid


if __name__ == "__main__":
    data = load_json("./data/grids/default.json")
    print(data)
    grid = Grid.from_data(data)
    print(f"h: {grid.height},  w: {grid.width}\n", grid.to_dict())
    for x in grid.matrix:
        for y in x:
            print(y.value, end="")
        print("")
