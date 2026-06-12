"""
Neonaure - Controller module

This module acts as an intermediary between the model and the view:
- Handles user interactions (clicks, undo, reset, grid generation)
- Checks victory condition and unlocks next grid
- Manages navigation between game and startup menu
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from PyQt6.QtCore import QPoint

from .view import MainWindow, NumberSelector, VictoryDialog
from .model import Grid, Pattern, Cell
from .startup import unlock_next_grid

if TYPE_CHECKING:
    pass


# Classe principale du MVC : fait le pont entre le modèle (Grid) et la vue (MainWindow)
class Controller:

    # Initialise le modèle depuis un fichier JSON, crée la vue et l'historique des coups
    def __init__(self, file_path: str) -> None:
        self._file_path: str = file_path
        self.model: Grid = Grid.from_json(file_path)
        self.view: MainWindow = MainWindow(self)
        self._history: list[tuple[int, int, int]] = []
        self._return_to_menu: bool = False
        self.update_view()

    # Synchronise l'affichage de la vue avec l'état actuel du modèle
    def update_view(self) -> None:
        values: dict[tuple[int, int], int] = {}
        thick_borders: list[tuple[int, int, int, int]] = []
        immutable_cells: set[tuple[int, int]] = set()

        # Parcourt chaque pattern pour extraire valeurs et cellules immuables
        for pattern in self.model.patterns:
            for cell in pattern.cells:
                if cell.value > 0:
                    values[(cell.y, cell.x)] = cell.value
                if cell.immuable:
                    immutable_cells.add((cell.y, cell.x))

        cols, rows = self.model.get_dimensions()

        # Construit un dictionnaire pour savoir à quel pattern appartient chaque cellule
        pattern_membership: dict[tuple[int, int], str] = {}
        for pattern in self.model.patterns:
            for cell in pattern.cells:
                pattern_membership[(cell.y, cell.x)] = pattern.name

        # Détermine les bordures épaisses entre les différents patterns
        for r in range(rows):
            for c in range(cols):
                current_pattern: str | None = pattern_membership.get((r, c))

                if r == 0 or pattern_membership.get((r-1, c)) != current_pattern:
                    thick_borders.append((c, r, c+1, r))
                if r == rows - 1 or pattern_membership.get((r+1, c)) != current_pattern:
                    thick_borders.append((c, r+1, c+1, r+1))
                if c == 0 or pattern_membership.get((r, c-1)) != current_pattern:
                    thick_borders.append((c, r, c, r+1))
                if c == cols - 1 or pattern_membership.get((r, c+1)) != current_pattern:
                    thick_borders.append((c+1, r, c+1, r+1))

        self.view.grid_view.set_data(rows, cols, values, thick_borders, immutable_cells, pattern_membership)

    # Gère le clic sur une cellule : ouvre un popup de sélection et met à jour la valeur
    def handle_click(self, col: int, row: int) -> None:
        # Cherche la cellule et le pattern correspondant aux coordonnées cliquées
        target_pattern: Pattern | None = None
        target_cell: Cell | None = None

        for pattern in self.model.patterns:
            for cell in pattern.cells:
                if cell.x == col and cell.y == row:
                    target_pattern = pattern
                    target_cell = cell
                    break
            if target_pattern:
                break

        if not target_pattern or target_cell is None or target_cell.immuable:
            return

        # Calcule les numeros encore disponibles dans le motif
        # (tous les numeros de 1 a la taille du motif, moins ceux deja utilises par les immuables)
        pattern_size = len(target_pattern.cells)
        possible_numbers = set(range(1, pattern_size + 1))
        for c in target_pattern.cells:
            if c.value != 0 and c.immuable and c != target_cell:
                possible_numbers.discard(c.value)
        remaining_options = sorted(list(possible_numbers))

        if not remaining_options:
            return

        # Affiche le popup de sélection à la position de la cellule cliquée
        cell_size: int = self.view.grid_view.cell_size
        local_pos: QPoint = QPoint(
            col * cell_size + self.view.grid_view.offset_x,
            row * cell_size + self.view.grid_view.offset_y,
        )
        global_pos: QPoint = self.view.grid_view.mapToGlobal(local_pos)

        popup: NumberSelector = NumberSelector(self.view, remaining_options, global_pos, cell_size)

        # Si l'utilisateur a validé son choix, on enregistre l'ancienne valeur dans l'historique
        if popup.exec():
            new_number: int = popup.selected_number
            self._history.append((target_cell.x, target_cell.y, target_cell.value))
            # Si on clique sur le meme nombre, on l'enleve (toggle)
            if new_number == target_cell.value:
                target_cell.set_value(0)
            else:
                target_cell.set_value(new_number)
            self.update_view()

            # On verifie si la grille est complete et sans erreur
            if self.model.is_complete():
                # On debloque la grille suivante
                unlock_next_grid(self._file_path)

                dialog = VictoryDialog(self.view)
                if dialog.exec():
                    # Le joueur veut revenir au menu
                    self._return_to_menu = True
                    self.view.close()

    # Annule le dernier coup joué en restaurant l'ancienne valeur
    def undo(self) -> None:
        if not self._history:
            return
        x, y, old_value = self._history.pop()
        cell: Cell | None = self.model.get_cell(x, y)
        if cell is not None and not cell.immuable:
            cell.value = old_value
            self.update_view()

    # Remet toutes les cellules modifiables à 0 et vide l'historique
    def reset_grid(self) -> None:
        for pattern in self.model.patterns:
            for cell in pattern.cells:
                if not cell.immuable:
                    cell.set_value(0)
        self._history.clear()
        self.update_view()

    # Génère une nouvelle grille aléatoire aux dimensions données
    def generate_new_grid(self, width: int, height: int) -> None:
        """Génère une nouvelle grille aléatoire et met à jour la vue."""
        from generate_grid import generate_grid

        data: dict[str, list[list[int]]] = generate_grid(width, height)
        self.model = Grid.from_data(data)
        self._history.clear()
        self.update_view()
