"""
Neonaure - Controller module

This module acts as an intermediary between the model and the view:
- Handles user interactions (clicks, undo, reset, grid generation)
- Checks victory condition and unlocks next grid
- Manages navigation between game and startup menu
"""

from PyQt6.QtCore import QPoint

from .view import MainWindow, NumberSelector, VictoryDialog
from .model import Grid, Pattern, Cell
from .startup import unlock_next_grid


# Classe principale du MVC : fait le pont entre le modele et la vue (MainWindow)
class Controller:

    # Initialise le modele depuis un fichier JSON, cree la vue et l'historique des coups
    def __init__(self, file_path: str) -> None:
        self._file_path = file_path
        self.model = Grid.from_json(file_path)
        self.view = MainWindow(self)
        self._history = []
        self._return_to_menu = False
        self.update_view()

    # Synchronise l'affichage de la vue avec l'etat actuel du modele
    def update_view(self) -> None:
        values = {}
        thick_borders = []
        immutable_cells = set()

        # Parcourt chaque pattern pour extraire valeurs et cellules immuables
        for pattern in self.model.patterns:
            for cell in pattern.cells:
                if cell.value > 0:
                    values[(cell.y, cell.x)] = cell.value
                if cell.immuable:
                    immutable_cells.add((cell.y, cell.x))

        cols, rows = self.model.get_dimensions()

        # Construit un dictionnaire pour savoir a quel pattern appartient chaque cellule
        pattern_membership = {}
        for pattern in self.model.patterns:
            for cell in pattern.cells:
                pattern_membership[(cell.y, cell.x)] = pattern.name

        # Determine les bordures epaisses entre les differents patterns
        for r in range(rows):
            for c in range(cols):
                current_pattern = pattern_membership.get((r, c))

                if r == 0 or pattern_membership.get((r-1, c)) != current_pattern:
                    thick_borders.append((c, r, c+1, r))
                if r == rows - 1 or pattern_membership.get((r+1, c)) != current_pattern:
                    thick_borders.append((c, r+1, c+1, r+1))
                if c == 0 or pattern_membership.get((r, c-1)) != current_pattern:
                    thick_borders.append((c, r, c, r+1))
                if c == cols - 1 or pattern_membership.get((r, c+1)) != current_pattern:
                    thick_borders.append((c+1, r, c+1, r+1))

        self.view.grid_view.set_data(rows, cols, values, thick_borders, immutable_cells, pattern_membership)

    # Gere le clic sur une cellule : ouvre un popup de selection et met a jour la valeur
    def handle_click(self, col: int, row: int) -> None:
        # Cherche la cellule et le pattern correspondant aux coordonnees cliquées
        target_pattern = None
        target_cell = None

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

        # construire la liste des options possibles
        options = []
        for n in range(1, len(target_pattern.cells) + 1):
            options.append(n)
        # enlever les valeurs deja prises par les cellules immuables
        for c in target_pattern.cells:
            if c.value != 0 and c.immuable and c != target_cell:
                if c.value in options:
                    options.remove(c.value)

        if not options:
            return

        # Affiche le popup de selection a la position de la cellule cliquée
        cell_size = self.view.grid_view.cell_size
        local_pos = QPoint(
            col * cell_size + self.view.grid_view.offset_x,
            row * cell_size + self.view.grid_view.offset_y,
        )
        global_pos = self.view.grid_view.mapToGlobal(local_pos)

        popup = NumberSelector(self.view, options, global_pos, cell_size)

        # Si l'utilisateur a valide son choix, on enregistre l'ancienne valeur dans l'historique
        if popup.exec():
            new_number = popup.selected_number
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

    # Annule le dernier coup joue en restaurant l'ancienne valeur
    def undo(self) -> None:
        if not self._history:
            return
        x, y, old_value = self._history.pop()
        cell = self.model.get_cell(x, y)
        if cell is not None and not cell.immuable:
            cell.value = old_value
            self.update_view()

    # Remet toutes les cellules modifiables a 0 et vide l'historique
    def reset_grid(self) -> None:
        for pattern in self.model.patterns:
            for cell in pattern.cells:
                if not cell.immuable:
                    cell.set_value(0)
        self._history.clear()
        self.update_view()

    # Genere une nouvelle grille aleatoire aux dimensions donnees
    def generate_new_grid(self, width: int, height: int) -> None:
        from generate_grid import generate_grid

        data = generate_grid(width, height)
        self.model = Grid.from_data(data)
        self._history.clear()
        self.update_view()
