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


# Exception levée quand un pattern est déjà chargé dans la grille
class PatternAlreadyLoaded(RuntimeError):
    pass


# Exception levée quand on tente de modifier une cellule immuable
class CellIsImmuable(Exception):
    pass


# Charge un fichier JSON et retourne son contenu sous forme de dict ou liste
def load_json(file_path: str) -> dict | list:
    with open(file_path, "r") as file:
        return json.load(file)


# Représente une cellule de la grille avec coordonnées, valeur et immuabilité
class Cell:

    # Initialise une cellule avec sa position, sa valeur et son statut d'immuabilité
    def __init__(self, x: int, y: int, value: int = 0, immuable: bool = False) -> None:
        self.x: int = x
        self.y: int = y
        self.value: int = value
        self.immuable: bool = immuable

    # Affichage lisible de la cellule
    def __str__(self) -> str:
        return f"({self.x}, {self.y}) with value {self.value}"

    # Représentation de debug
    def __repr__(self) -> str:
        return f"Cell(x={self.x}, y={self.y}, value={self.value}, immuable={self.immuable})"

    # Deux cellules sont "egales" si elles sont a la meme position (x, y)
    # Cela permet de comparer des cellules de maniere logique
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Cell):
            return False
        return self.x == other.x and self.y == other.y

    # Le hash est base sur les coordonnees, ce qui est coherent avec __eq__
    # (deux objets egaux doivent avoir le meme hash)
    # Cela permet d'utiliser des Cell dans des set() ou comme cles de dict
    def __hash__(self) -> int:
        return hash((self.x, self.y))

    # Sérialise la cellule en liste [x, y, valeur, immuable]
    def to_list(self) -> list[int | bool]:
        """Returns the cell data as a list [x, y, value, immuable]."""
        return [self.x, self.y, self.value, self.immuable]

    # Modifie la valeur d'une cellule, lève une exception si immuable
    def set_value(self, value: int) -> None:
        """Sets the cell value. Raises CellIsImmuable if the cell cannot be modified."""
        if self.immuable:
            raise CellIsImmuable(f"Cell `{self}` is immuable cannot be edited.")
        self.value = value


# Représente un motif (région) de la grille, contenant plusieurs cellules
class Pattern:
    """Represents a pattern (region, motif) in the grid."""

    # Initialise un motif avec un nom et une liste de cellules
    def __init__(self, name: str, cells: list[Cell] | None = None) -> None:
        self.name: str = name
        self.cells: list[Cell] = cells or []

    def __repr__(self) -> str:
        return f"Pattern(name={self.name!r}, cells={len(self.cells)} cells)"

    # Sérialise le motif en liste de listes
    def to_list(self) -> list[list[int | bool]]:
        """Returns the pattern data as a list of cell lists."""
        return [cell.to_list() for cell in self.cells]

    # Nombre de cellules dans le motif
    def size(self) -> int:
        return len(self.cells)

    # Liste des valeurs déjà présentes dans le motif (sans les zéros)
    def values(self) -> list[int]:
        return [c.value for c in self.cells if c.value != 0]

    # Vérifie si une valeur est déjà présente dans le motif
    def contains_value(self, v: int) -> bool:
        return any(c.value == v for c in self.cells)

    # Met à jour une cellule existante ou en ajoute une nouvelle au motif
    def set_cell(self, x: int, y: int, value: int, immuable: bool = False) -> None:
        """Updates the value of an existing cell, or adds a new cell if absent."""
        for cell in self.cells:
            if cell.x == x and cell.y == y:
                cell.set_value(value)
                break
        else:
            self.cells.append(Cell(x, y, value, immuable))

    # Crée un Pattern à partir de données brutes (listes de coordonnées/valeurs)
    @classmethod
    def from_raw_cells(cls, name: str, raw_cells: list[list[int]]) -> Pattern:
        """Creates a Pattern instance from a raw list of cell data."""
        instance: Pattern = cls(name)
        for cell in raw_cells:
            # Logique d'immuabilité :
            # Si la cellule a 4 éléments, elle provient d'une save,
            #   on vérifie le 4ème élément pour l'immuabilité
            # Si il n'y a que 3 éléments et valeur != 0, la cellule est immuable
            #   car chargée depuis un json externe (nouvelle partie)
            immuable: bool = False
            if (len(cell) == 3) and (cell[2] != 0):
                immuable = True
            elif len(cell) > 3:
                immuable = cell[3]
            instance.set_cell(cell[0], cell[1], cell[2], immuable)
        return instance


# Représente la grille de jeu complète avec ses patterns et sa matrice 2D
class Grid:
    """Represents the Neonaure game grid, including dimensions, cells, and patterns."""

    # Construit la grille à partir d'une liste de patterns
    def __init__(self, patterns: list[Pattern]) -> None:
        self.patterns: list[Pattern] = []
        for pattern in patterns:
            self._add_pattern(pattern)
        self.height: int = 0
        self.width: int = 0
        self._compute_dimensions()
        self.matrix: list[list[Cell | None]] = [[None for _ in range(self.width)] for _ in range(self.height)]
        self._fill_matrix()

    # Sérialise la grille en dictionnaire {nom_du_pattern: données}
    def to_dict(self) -> dict[str, list[list[int | bool]]]:
        """Returns the grid data as a dictionary keyed by pattern names."""
        return {pattern.name: pattern.to_list() for pattern in self.patterns}

    # Remplit la matrice 2D avec les références des cellules
    def _fill_matrix(self) -> None:
        """Populates the 2D matrix with cell references based on their coordinates."""
        for pattern in self.patterns:
            for cell in pattern.cells:
                self.matrix[cell.y][cell.x] = cell

    # Ajoute un pattern, lève une erreur si le nom existe déjà
    def _add_pattern(self, pattern: Pattern) -> None:
        """Adds a pattern to the grid. Raises PatternAlreadyLoaded if the name exists."""
        for p in self.patterns:
            if p.name == pattern.name:
                raise PatternAlreadyLoaded(
                    f"Pattern with name '{pattern.name}' is already loaded."
                )
        self.patterns.append(pattern)

    # Calcule la largeur et la hauteur de la grille à partir des coordonnées max
    def _compute_dimensions(self) -> None:
        self.height = 0
        self.width = 0
        for pattern in self.patterns:
            for cell in pattern.cells:
                if cell.x >= self.width:
                    self.width = cell.x + 1
                if cell.y >= self.height:
                    self.height = cell.y + 1

    # Retourne (largeur, hauteur) de la grille
    def get_dimensions(self) -> tuple[int, int]:
        return self.width, self.height

    # Verifie si la grille est remplie et sans erreur
    # Toutes les cellules doivent avoir une valeur non-nulle,
    # et il ne doit pas y avoir de conflit (voisins identiques ou doublon dans un motif)
    def is_complete(self) -> bool:
        # On verifie que toutes les cellules sont remplies
        for pattern in self.patterns:
            for cell in pattern.cells:
                if cell.value == 0:
                    return False

        # On verifie qu'il n'y a pas de conflit entre voisins
        solver = Solver(self)
        for pattern in self.patterns:
            for cell in pattern.cells:
                if solver._has_conflict(cell):
                    return False

        # On verifie qu'il n'y a pas de doublon dans chaque motif
        for pattern in self.patterns:
            values_seen = []
            for cell in pattern.cells:
                if cell.value in values_seen:
                    return False
                values_seen.append(cell.value)

        return True

    # Retourne la cellule aux coordonnées données, ou None
    def get_cell(self, x: int, y: int) -> Cell | None:
        if 0 <= y < self.height and 0 <= x < self.width:
            return self.matrix[y][x]
        return None

    # Retourne le pattern qui contient la cellule aux coordonnées données
    def get_pattern_of(self, x: int, y: int) -> Pattern | None:
        for pattern in self.patterns:
            for cell in pattern.cells:
                if cell.x == x and cell.y == y:
                    return pattern
        return None

    # Retourne la liste des 8 voisins directs d'une cellule
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

    # Crée une grille à partir d'un dictionnaire de données de patterns
    @classmethod
    def from_data(cls, data: dict[str, list[list[int]]]) -> Grid:
        """Creates a Grid instance from a dictionary of pattern data."""
        patterns: list[Pattern] = []
        for key, val in data.items():
            if key.startswith(PATTERN_KEY_STARTS_WITH):
                patterns.append(Pattern.from_raw_cells(key, val))
        return cls(patterns)

    # Crée une grille à partir d'un chemin de fichier JSON
    @classmethod
    def from_json(cls, file_path: str) -> Grid:
        """Creates a Grid instance from a JSON file path."""
        data: dict[str, list[list[int]]] = load_json(file_path)  # type: ignore[assignment]
        return cls.from_data(data)



# Solveur de grille basé sur la coloration de graphe et le backtracking
class Solver:
    """Solves the Neonaure grid using Graph Coloring theory and Backtracking."""

    # Initialise le solveur avec la grille à résoudre
    def __init__(self, grid: Grid) -> None:
        self.grid: Grid = grid

    # Verifie si une cellule partage sa valeur avec un voisin
    # On parcourt les 8 voisins et on regarde si l'un d'eux a la meme valeur
    def _has_conflict(self, cell: Cell) -> bool:
        neighbours = self.grid.neighbours(cell.x, cell.y)
        for neighbour in neighbours:
            if neighbour.value != 0 and neighbour.value == cell.value:
                return True
        return False

    # Retourne le pattern qui contient la cellule donnée
    def _get_pattern_for_cell(self, cell: Cell) -> Pattern:
        """Retrieves the Pattern object containing the given cell."""
        for pattern in self.grid.patterns:
            for p_cell in pattern.cells:
                if p_cell.x == cell.x and p_cell.y == cell.y:
                    return pattern
        raise ValueError(f"Cell at ({cell.x}, {cell.y}) does not belong to any pattern.")

    # Calcule les valeurs possibles pour une cellule
    # On commence avec toutes les valeurs de 1 a la taille du motif
    # puis on enleve celles qui sont deja prises par les voisins ou dans le motif
    def _get_possible_values(self, cell: Cell) -> list[int]:
        pattern = self._get_pattern_for_cell(cell)
        n = len(pattern.cells)

        # Au debut, toutes les valeurs de 1 a n sont possibles
        possible_values = []
        for v in range(1, n + 1):
            possible_values.append(v)

        # On enleve les valeurs des voisins (contrainte de voisinage)
        for neighbour in self.grid.neighbours(cell.x, cell.y):
            if neighbour.value != 0 and neighbour.value in possible_values:
                possible_values.remove(neighbour.value)

        # On enleve les valeurs deja presentes dans le motif (contrainte de motif)
        for p_cell in pattern.cells:
            if p_cell.value != 0 and p_cell is not cell:
                if p_cell.value in possible_values:
                    possible_values.remove(p_cell.value)

        return possible_values

    # Resout la grille par backtracking
    # D'abord on verifie qu'il n'y a pas de conflit dans l'etat initial
    # puis on lance le backtracking sur les cases vides
    def solve_grid(self) -> bool:
        # Verification initiale : pas de conflit entre valeurs deja posees
        for pattern in self.grid.patterns:
            for cell in pattern.cells:
                if cell.value != 0 and self._has_conflict(cell):
                    return False

        # On verifie aussi qu'il n'y a pas de doublon dans chaque motif
        for pattern in self.grid.patterns:
            for cell in pattern.cells:
                if cell.value != 0:
                    for p_cell in pattern.cells:
                        if p_cell is not cell and p_cell.value == cell.value:
                            return False

        # On recupere toutes les cellules vides (valeur == 0)
        empty_cells = []
        for pattern in self.grid.patterns:
            for cell in pattern.cells:
                if cell.value == 0:
                    empty_cells.append(cell)

        return self._backtrack(empty_cells)

    # Alias pour solve_grid
    def solve(self) -> bool:
        return self.solve_grid()

    # Algorithme de backtracking recursif avec selection MRV
    # MRV = Minimum Remaining Values : on choisit en priorite la case
    # qui a le moins de valeurs possibles (elle est la plus contrainte)
    def _backtrack(self, empty_cells: list[Cell]) -> bool:
        # S'il n'y a plus de cases vides, la grille est resolue
        if len(empty_cells) == 0:
            return True

        # On cherche la case avec le moins de valeurs possibles (heuristique MRV)
        best_cell = None
        best_options = []
        min_options = 999  # nombre tres grand pour commencer
        best_index = -1

        for i in range(len(empty_cells)):
            cell = empty_cells[i]
            options = self._get_possible_values(cell)

            # Si aucune valeur possible, on est dans une impasse
            if len(options) == 0:
                return False

            # Si cette case a moins d'options que la meilleure trouvee,
            # on la garde
            if len(options) < min_options:
                min_options = len(options)
                best_cell = cell
                best_options = options
                best_index = i

                # Si on a trouve une case avec 1 seule option, pas besoin
                # de chercher plus loin, c'est forcement la meilleure
                if min_options == 1:
                    break

        # On retire la case choisie de la liste des cases vides
        empty_cells.pop(best_index)

        # On essaie chaque valeur possible pour cette case
        for value in best_options:
            best_cell.set_value(value)

            # On relance le backtracking sur les cases restantes
            if self._backtrack(empty_cells):
                return True

            # Si ca n'a pas marche, on remet la valeur a 0 et on essaie
            # la valeur suivante (c'est le "retour sur trace")
            best_cell.set_value(0)

        # Aucune valeur ne fonctionne, on remet la case dans la liste
        # et on retourne False pour dire au parent de backtracker aussi
        empty_cells.insert(best_index, best_cell)
        return False



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

    solver = Solver(grid)
    is_solved = solver.solve_grid()
    print("solved ? ", is_solved)
    for row in grid.matrix:
        for cell in row:
            print(cell.value if cell is not None else ".", end="")
        print("")
