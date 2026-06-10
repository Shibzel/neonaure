"""
Neonaure - Model module

Author(s):
    - Jean-François L. (contact@shibzel.me)

This module contains the core data structures and business logic:
- Grid, Motif, and Cell classes to represent the game state.
- Methods to load/save grids.
- Solver class using Graph Coloring and Backtracking.
"""

from __future__ import annotations

import json

PATTERN_KEY_STARTS_WITH: str = "motif"


class PatternAlreadyLoaded(RuntimeError):
    pass


class CellIsImmuable(Exception):
    pass


class InvalidGrid(Exception):
    pass


def load_json(file_path: str) -> dict | list:
    with open(file_path, "r") as file:
        return json.load(file)


def save_json(file_path: str, data: dict | list) -> None:
    with open(file_path, "w+") as file:
        json.dump(data, file, indent=None)


class Cell:
    __slots__ = ("x", "y", "value", "immuable")

    def __init__(self, x: int, y: int, value: int = 0, immuable: bool = False) -> None:
        self.x: int = x
        self.y: int = y
        self.value: int = value
        self.immuable: bool = immuable

    def __str__(self) -> str:
        return f"({self.x}, {self.y}) with value {self.value}"

    def __repr__(self) -> str:
        return f"Cell(x={self.x}, y={self.y}, value={self.value}, immuable={self.immuable})"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Cell):
            return False
        if self.value == 0 and other.value == 0:
            return False
        return self.value == other.value

<<<<<<< Updated upstream
    def to_list(self) -> list:
        """Returns the cell data as a list [x, y, value, immuable]."""
=======
    def __hash__(self) -> int:
        return hash((self.x, self.y))

    def to_list(self) -> list[int | bool]:
>>>>>>> Stashed changes
        return [self.x, self.y, self.value, self.immuable]

    def is_empty(self) -> bool:
        return self.value == 0

    def set_value(self, value: int) -> None:
        """Sets the cell value. Raises CellIsImmuable if the cell cannot be modified."""
        if self.immuable:
            raise CellIsImmuable(f"Cell `{self}` is immuable cannot be edited.")
        self.value = value


class Pattern:
    """Represents a pattern (region, motif) in the grid."""

    def __init__(self, name: str, cells: list[Cell] | None = None) -> None:
        self.name: str = name
        self.cells: list[Cell] = cells or []

<<<<<<< Updated upstream
    def to_list(self) -> list:
        """Returns the pattern data as a list of cell lists."""
=======
    def __repr__(self) -> str:
        return f"Pattern(name={self.name!r}, cells={len(self.cells)} cells)"

    def to_list(self) -> list[list[int | bool]]:
>>>>>>> Stashed changes
        return [cell.to_list() for cell in self.cells]

    def size(self) -> int:
        return len(self.cells)

    def values(self) -> list[int]:
        return [c.value for c in self.cells if c.value != 0]

    def missing_values(self) -> list[int]:
        used: set[int] = set(self.values())
        return [v for v in range(1, self.size() + 1) if v not in used]

    def contains_value(self, v: int) -> bool:
        return any(c.value == v for c in self.cells)

    def get_cell(self, x: int, y: int) -> Cell | None:
        for c in self.cells:
            if c.x == x and c.y == y:
                return c
        return None

    def set_cell(self, x: int, y: int, value: int, immuable: bool = False) -> None:
        """Updates the value of an existing cell, or adds a new cell if absent."""
        for cell in self.cells:
            if cell.x == x and cell.y == y:
                cell.set_value(value)
                break
        else:
            self.cells.append(Cell(x, y, value, immuable))

    @classmethod
<<<<<<< Updated upstream
    def from_raw_cells(cls, name: str, raw_cells: list) -> "Pattern":
        """Creates a Pattern instance from a raw list of cell data."""
        instance = cls(name)
=======
    def from_raw_cells(cls, name: str, raw_cells: list[list[int]]) -> Pattern:
        instance: Pattern = cls(name)
>>>>>>> Stashed changes
        for cell in raw_cells:
            # Logique d'immuabilité :
            # Si la cellule a 4 éléments, cela veut dire qu'elle provient d'une save,
            #   donc on vérifie la 4ème valeur pour sa valeur d'immuabilité (True = non mutable)
            # Si il n'y a que 3 éléments, alors la cellule est immuable car chargée
            #   depuis un json externe (nouvelle partie)
            immuable: bool = False
            if (len(cell) == 3) and (cell[2] != 0):
                immuable = True
            elif len(cell) > 3:
                immuable = cell[3]
            instance.set_cell(cell[0], cell[1], cell[2], immuable)
        return instance


class Grid:
    """Represents the Neonaure game grid, including dimensions, cells, and patterns."""

    def __init__(self, patterns: list[Pattern]) -> None:
        self.patterns: list[Pattern] = []
        for pattern in patterns:
            self._add_pattern(pattern)
        self.height: int = 0
        self.width: int = 0
        self._compute_dimensions()
        self.matrix: list[list[Cell | None]] = [[None for _ in range(self.width)] for _ in range(self.height)]
        self._fill_matrix()

<<<<<<< Updated upstream
    def to_dict(self) -> dict:
        """Returns the grid data as a dictionary keyed by pattern names.
        The result should should be able te be converted into JSON objects."""
=======
    def to_dict(self) -> dict[str, list[list[int | bool]]]:
>>>>>>> Stashed changes
        return {pattern.name: pattern.to_list() for pattern in self.patterns}

    def _fill_matrix(self) -> None:
        """Populates the 2D matrix with cell references based on their coordinates."""
        for pattern in self.patterns:
            for cell in pattern.cells:
                self.matrix[cell.y][cell.x] = cell

    def _add_pattern(self, pattern: Pattern) -> None:
        """Adds a pattern to the grid. Raises PatternAlreadyLoaded if the name exists."""
        for p in self.patterns:
            if p.name == pattern.name:
                raise PatternAlreadyLoaded(
                    f"Pattern with name '{pattern.name}' is already loaded."
                )
        self.patterns.append(pattern)

    def _compute_dimensions(self) -> None:
        self.height = 0
        self.width = 0
        for pattern in self.patterns:
            for cell in pattern.cells:
                if cell.x >= self.width:
                    self.width = cell.x + 1
                if cell.y >= self.height:
                    self.height = cell.y + 1

    def get_dimensions(self) -> tuple[int, int]:
<<<<<<< Updated upstream
        """Calculates and returns the grid dimensions (width, height)."""
        if (self.height is None) or (self.width is None):
            self.height = self.width = 0
            for pattern in self.patterns:
                for cell in pattern.cells:
                    if cell.x > self.width:
                        self.width = cell.x + 1
                    if cell.y > self.height:
                        self.height = cell.y + 1
=======
>>>>>>> Stashed changes
        return self.width, self.height

    def get_cell(self, x: int, y: int) -> Cell | None:
        if 0 <= y < self.height and 0 <= x < self.width:
            return self.matrix[y][x]
        return None

    def get_pattern_of(self, x: int, y: int) -> Pattern | None:
        for pattern in self.patterns:
            for cell in pattern.cells:
                if cell.x == x and cell.y == y:
                    return pattern
        return None

    def is_valid_placement(self, x: int, y: int, value: int) -> bool:
        pattern: Pattern | None = self.get_pattern_of(x, y)
        if pattern is None:
            return False
        if value < 1 or value > pattern.size():
            return False
        if pattern.contains_value(value):
            return False
        for nb in self.neighbours(x, y):
            if nb.value == value:
                return False
        return True

    def is_complete(self) -> bool:
        return all(c.value != 0 for p in self.patterns for c in p.cells)

    def is_solved(self) -> bool:
        if not self.is_complete():
            return False
        for pattern in self.patterns:
            for cell in pattern.cells:
                if self._has_neighbour_conflict(cell):
                    return False
        return True

    def _has_neighbour_conflict(self, cell: Cell) -> bool:
        for nb in self.neighbours(cell.x, cell.y):
            if nb.value == cell.value and cell.value != 0:
                return True
        return False

    def set_cell_value(self, x: int, y: int, value: int) -> bool:
        cell: Cell | None = self.get_cell(x, y)
        if cell is None or cell.immuable:
            return False
        cell.set_value(value)
        return True

    def neighbours(self, x: int, y: int) -> list[Cell]:
        """Returns a list of the closest neighbours of a cell."""
        offsets: list[tuple[int, int]] = [
            (-1, 0), (1, 0), (0, -1), (0, 1),
            (-1, -1), (-1, 1), (1, -1), (1, 1)
        ]
        result: list[Cell] = []
        for dx, dy in offsets:
            nx: int = x + dx
            ny: int = y + dy
            if (0 <= nx < self.width) and (0 <= ny < self.height):
                cell: Cell | None = self.matrix[ny][nx]
                if cell is not None:
                    result.append(cell)
        return result

    @classmethod
<<<<<<< Updated upstream
    def from_data(cls, data: dict) -> "Grid":
        """Creates a Grid instance from a dictionary of pattern data."""
        patterns: list = []
=======
    def from_data(cls, data: dict[str, list[list[int]]]) -> Grid:
        patterns: list[Pattern] = []
>>>>>>> Stashed changes
        for key, val in data.items():
            if key.startswith(PATTERN_KEY_STARTS_WITH):
                patterns.append(Pattern.from_raw_cells(key, val))
        return cls(patterns)

    @classmethod
<<<<<<< Updated upstream
    def from_json(cls, file_path: str):
        """Creates a Grid instance from a JSON file path."""
        data: dict = load_json(file_path)
=======
    def from_json(cls, file_path: str) -> Grid:
        data: dict[str, list[list[int]]] = load_json(file_path)  # type: ignore[assignment]
>>>>>>> Stashed changes
        return cls.from_data(data)

    def save_grid_to_json(self, file_path: str) -> None:
        """Saves the current grid state to a JSON file."""
        save_json(file_path, self.to_dict())


class Solver:
    """Solves the Neonaure grid using Graph Coloring theory and Backtracking."""

    def __init__(self, grid: Grid) -> None:
        self.grid: Grid = grid
        self._solution_count: int = 0
        self._max_count: int = 2

    def _has_conflict(self, cell: Cell) -> bool:
        """Returns True if a cell shares its value with any of its neighbours."""
        return any(
            neighbour == cell
            for neighbour in self.grid.neighbours(cell.x, cell.y)
        )

    def is_solved(self) -> bool:
        """Returns True if all cells have a non-zero value and no cell shares its value with a neighbour."""
        return all(
            cell.value != 0 and not self._has_conflict(cell)
            for pattern in self.grid.patterns
            for cell in pattern.cells
        )

    def _get_pattern_for_cell(self, cell: Cell) -> Pattern:
        """Retrieves the Pattern object containing the given cell."""
        for pattern in self.grid.patterns:
            for p_cell in pattern.cells:
                if p_cell.x == cell.x and p_cell.y == cell.y:
                    return pattern
        raise ValueError(f"Cell at ({cell.x}, {cell.y}) does not belong to any pattern.")

    def _get_possible_values(self, cell: Cell) -> list[int]:
        """
        Calculates the domain (possible values) for a cell based on Graph Coloring constraints.
        A value is possible if it is not used by adjacent nodes (neighbours)
        or nodes within the same clique (pattern).
        """
        pattern: Pattern = self._get_pattern_for_cell(cell)
        n: int = len(pattern.cells)
        possible_values: set[int] = set(range(1, n + 1))

        for neighbour in self.grid.neighbours(cell.x, cell.y):
            if neighbour.value != 0:
                possible_values.discard(neighbour.value)

        for p_cell in pattern.cells:
            if p_cell.value != 0 and p_cell is not cell:
                possible_values.discard(p_cell.value)

        return list(possible_values)

    def solve_grid(self) -> bool:
<<<<<<< Updated upstream
        """Fills the grid using backtracking. Returns True if solved."""
        # Gather all empty cells (nodes with no color yet)
        empty_cells: list = [
=======
        """
        Uses a "backtracking" algorithm etc etc TODO
        Things to consider :
            - This method fills the grid that has been initialized
            - TODO
        """
        for pattern in self.grid.patterns:
            for cell in pattern.cells:
                if cell.value != 0 and self._has_conflict(cell):
                    return False
                if cell.value != 0:
                    for p_cell in pattern.cells:
                        if p_cell is not cell and p_cell.value == cell.value:
                            return False

        empty_cells: list[Cell] = [
>>>>>>> Stashed changes
            cell for pattern in self.grid.patterns
            for cell in pattern.cells if cell.value == 0
        ]

        return self._backtrack(empty_cells)

    def solve(self) -> bool:
        return self.solve_grid()

    def _backtrack(self, empty_cells: list[Cell]) -> bool:
        """Recursive backtracking algorithm to color the graph."""
        if not empty_cells:
            return True

        best_cell: Cell | None = None
        best_options: list[int] = []
        min_options: int = len(self.grid.patterns[0].cells) + 1 if self.grid.patterns else 0
        best_index: int = -1

        for i, cell in enumerate(empty_cells):
            options: list[int] = self._get_possible_values(cell)

            if len(options) == 0:
                return False

            if len(options) < min_options:
                min_options = len(options)
                best_cell = cell
                best_options = options
                best_index = i
                if min_options == 1:
                    break

        empty_cells.pop(best_index)

        for value in best_options:
            best_cell.set_value(value)

            if self._backtrack(empty_cells):
                return True

            best_cell.set_value(0)

        empty_cells.insert(best_index, best_cell)
        return False

    def hint(self) -> tuple[int, int, int] | None:
        empty_cells: list[Cell] = [
            cell for pattern in self.grid.patterns
            for cell in pattern.cells if cell.value == 0
        ]
        if not empty_cells:
            return None

        best_cell: Cell | None = None
        best_options: list[int] = []
        min_options: int = len(self.grid.patterns[0].cells) + 1 if self.grid.patterns else 0

        for cell in empty_cells:
            options: list[int] = self._get_possible_values(cell)
            if len(options) == 0:
                continue
            if len(options) < min_options:
                min_options = len(options)
                best_cell = cell
                best_options = options
                if min_options == 1:
                    break

        if best_cell is None or not best_options:
            return None

        return (best_cell.x, best_cell.y, best_options[0])

    def count_solutions(self, max_count: int = 2) -> int:
        empty_cells: list[Cell] = [
            cell for pattern in self.grid.patterns
            for cell in pattern.cells if cell.value == 0
        ]
        self._solution_count: int = 0
        self._max_count: int = max_count
        self._count_backtrack(empty_cells)
        return self._solution_count

    def _count_backtrack(self, empty_cells: list[Cell]) -> None:
        if self._solution_count >= self._max_count:
            return
        if not empty_cells:
            self._solution_count += 1
            return

        best_cell: Cell | None = None
        best_options: list[int] = []
        min_options: int = len(self.grid.patterns[0].cells) + 1 if self.grid.patterns else 0
        best_index: int = -1

        for i, cell in enumerate(empty_cells):
            options: list[int] = self._get_possible_values(cell)
            if len(options) == 0:
                return
            if len(options) < min_options:
                min_options = len(options)
                best_cell = cell
                best_options = options
                best_index = i
                if min_options == 1:
                    break

        empty_cells.pop(best_index)

        for value in best_options:
            if self._solution_count >= self._max_count:
                break
            best_cell.set_value(value)
            self._count_backtrack(empty_cells)
            best_cell.set_value(0)

        empty_cells.insert(best_index, best_cell)


if __name__ == "__main__":
    data: dict[str, list[list[int]]] = load_json("./data/grids/default.json")  # type: ignore[assignment]
    print(data)
    grid: Grid = Grid.from_data(data)
    print(f"h: {grid.height},  w: {grid.width}\n", grid.to_dict())
    for row in grid.matrix:
        for cell in row:
            print(cell.value if cell is not None else ".", end="")
        print("")
    print("")
    for nb in grid.neighbours(0, 5):
        print(nb.value, end="")
    print("")

    solver: Solver = Solver(grid)
    is_solved: bool = solver.solve_grid()
    print("solved ? ", is_solved)
    print("is solved ? ", solver.is_solved())
    for row in grid.matrix:
        for cell in row:
            print(cell.value if cell is not None else ".", end="")
        print("")
