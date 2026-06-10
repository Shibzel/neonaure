"""
Neonaure - Model module

Author(s):
    - Jean-François L. (contact@shibzel.mes)

This module contains the core data structures and business logic:
- Grid, Motif, and Cell classes to represent the game state.
- Methods to load/save grids.
- Solver class using Graph Coloring and Backtracking.
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

    def __eq__(self, other: object) -> bool:
        if not hasattr(other, "value"):
            return False
        return self.value == other.value

    def to_list(self) -> list:
        """Returns the cell data as a list [x, y, value, immuable]."""
        return [self.x, self.y, self.value, self.immuable]

    def set_value(self, value: int) -> None:
        """Sets the cell value. Raises CellIsImmuable if the cell cannot be modified."""
        if self.immuable:
            raise CellIsImmuable(f"Cell `{self}` is immuable cannot be edited.")
        self.value = value


class Pattern:
    """Represents a pattern (region, motif) in the grid."""

    def __init__(self, name: str, cells: list[Cell] | None = None) -> None:
        self.name = name
        self.cells = cells or []

    def to_list(self) -> list:
        """Returns the pattern data as a list of cell lists."""
        return [cell.to_list() for cell in self.cells]

    def set_cell(self, x: int, y: int, value: int, immuable: bool = False) -> None:
        """Updates the value of an existing cell, or adds a new cell if absent."""
        for cell in self.cells:
            if cell.x == x and cell.y == y:
                cell.set_value(value)
                break
        else:  # Cellule absente du motif
            self.cells.append(Cell(x, y, value, immuable))

    @classmethod
    def from_raw_cells(cls, name: str, raw_cells: list) -> "Pattern":
        """Creates a Pattern instance from a raw list of cell data."""
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
        self.patterns: list[Pattern] = []
        for pattern in patterns:
            self._add_pattern(pattern)
        self.height: int | None = None
        self.width: int | None = None
        x, y = self.get_dimensions()
        self.matrix = [[None for _ in range(x)] for _ in range(y)]
        self._fill_matrix()

    def to_dict(self) -> dict:
        """Returns the grid data as a dictionary keyed by pattern names.
        The result should should be able te be converted into JSON objects."""
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

    def get_dimensions(self) -> tuple[int, int]:
        """Calculates and returns the grid dimensions (width, height)."""
        if (self.height is None) or (self.width is None):
            self.height = self.width = 0
            for pattern in self.patterns:
                for cell in pattern.cells:
                    if cell.x > self.width:
                        self.width = cell.x + 1
                    if cell.y > self.height:
                        self.height = cell.y + 1
        return self.width, self.height

    def neighbours(self, x: int, y: int) -> list[Cell]:
        """Returns a list of the closest neighbours of a cell."""
        offsets = [
            (-1, 0), (1, 0), (0, -1), (0, 1),  # 4 directions cardinales
            (-1, -1), (-1, 1), (1, -1), (1, 1) # diagonales
        ]
        result: list = []
        for dx, dy in offsets:
            nx, ny = x + dx, y + dy
            if (0 <= nx < self.width) and (0 <= ny < self.height):
                cell = self.matrix[ny][nx]
                if cell is not None:
                    result.append(cell)
        return result

    @classmethod
    def from_data(cls, data: dict) -> "Grid":
        """Creates a Grid instance from a dictionary of pattern data."""
        patterns: list = []
        for key, val in data.items():
            # La clé se doit de commencer par "motif"
            if key.startswith(PATTERN_KEY_STARTS_WITH):
                patterns.append(Pattern.from_raw_cells(key, val))
        instance = cls(patterns)
        return instance

    @classmethod
    def from_json(cls, file_path: str):
        """Creates a Grid instance from a JSON file path."""
        data: dict = load_json(file_path)
        return cls.from_data(data)

    def save_grid_to_json(self, file_path: str) -> None:
        """Saves the current grid state to a JSON file."""
        save_json(file_path, self.to_dict())


class Solver:
    """Solves the Neonaure grid using Graph Coloring theory and Backtracking."""

    def __init__(self, grid: Grid) -> None:
        self.grid = grid

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
        possible_values: set = set(range(1, n + 1))

        # Contrainte 1: Retirer les valeurs des nodes adjacentes
        for neighbour in self.grid.neighbours(cell.x, cell.y):
            if neighbour.value != 0:
                possible_values.discard(neighbour.value)

        # Contrainte 2: Retirer les valeurs du même motif
        for p_cell in pattern.cells:
            if p_cell.value != 0 and p_cell is not cell:
                possible_values.discard(p_cell.value)

        return list(possible_values)

    def solve_grid(self) -> bool:
        """Fills the grid using backtracking. Returns True if solved."""
        # Gather all empty cells (nodes with no color yet)
        empty_cells: list = [
            cell for pattern in self.grid.patterns
            for cell in pattern.cells if cell.value == 0
        ]

        return self._backtrack(empty_cells)

    def _backtrack(self, empty_cells: list[Cell]) -> bool:
        """Recursive backtracking algorithm to color the graph."""
        if not empty_cells:
            return True

        # On cherche la cellule égale à 0 qui a le plus petit nombre possibilités
        best_cell: Cell | None = None
        best_options: list = []
        min_options: float = float('inf')
        best_index: int = -1

        for i, cell in enumerate(empty_cells):
            options = self._get_possible_values(cell)

            # Si une case n'a plus d'options alors on fait face à un cul de sac
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

        # Try each possible value for the chosen cell
        for value in best_options:
            best_cell.set_value(value)  # Coloration

            # Si on est sur une solution, on renvoie True
            if self._backtrack(empty_cells):
                return True

            # Fail, on "backtrack"
            best_cell.set_value(0)

        # Si aucune valeur ne fonctionne, on met ma cellule dans la liste et on signale l'échec
        empty_cells.insert(best_index, best_cell)
        return False


if __name__ == "__main__":
    # Sh*tty lines of code to test everything, do not pay attention
    data = load_json("./data/grids/default.json")
    print(data)
    grid = Grid.from_data(data)
    print(f"h: {grid.height},  w: {grid.width}\n", grid.to_dict())
    for x in grid.matrix:
        for y in x:
            print(y.value, end="")
        print("")
    print("")
    for x in grid.neighbours(0, 5):
        print(x.value, end="")
    print("")

    solver = Solver(grid)
    is_solved = solver.solve_grid()
    print("solved ? ", is_solved)
    print("is solved ? ", solver.is_solved())
    for x in grid.matrix:
        for y in x:
            print(y.value, end="")
        print("")
