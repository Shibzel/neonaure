"""
Neonaure - Controller module

This module acts as an intermediary between the model and the view:
- TODO
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from PyQt6.QtCore import QPoint

from .view import MainWindow, NumberSelector
from .model import Grid, Pattern, Cell

if TYPE_CHECKING:
    pass


class Controller:
    def __init__(self, file_path: str) -> None:
        self.model: Grid = Grid.from_json(file_path)
        self.view: MainWindow = MainWindow(self)
        self._history: list[tuple[int, int, int]] = []
        self.update_view()

    def update_view(self) -> None:
        values: dict[tuple[int, int], int] = {}
        thick_borders: list[tuple[int, int, int, int]] = []

        for pattern in self.model.patterns:
            for cell in pattern.cells:
                if cell.value > 0:
                    values[(cell.y, cell.x)] = cell.value

        rows: int
        cols: int
        rows, cols = self.model.get_dimensions()

        pattern_membership: dict[tuple[int, int], str] = {}
        for pattern in self.model.patterns:
            for cell in pattern.cells:
                pattern_membership[(cell.y, cell.x)] = pattern.name

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

        immutable_cells: set[tuple[int, int]] = set()
        self.view.grid_view.set_data(rows, cols, values, thick_borders, immutable_cells, pattern_membership)

    def handle_click(self, row: int, col: int) -> None:
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

        pattern_size: int = len(target_pattern.cells)
        possible_numbers: set[int] = set(range(1, pattern_size + 1))
        used_numbers: set[int] = {
            c.value
            for c in target_pattern.cells
            if c.value != 0
            and c.immuable
            and c != target_cell
        }
        remaining_options: list[int] = sorted(list(possible_numbers - used_numbers))

        if not remaining_options:
            return

        cell_size: int = self.view.grid_view.cell_size
        local_pos: QPoint = QPoint(col * cell_size, row * cell_size)
        global_pos: QPoint = self.view.grid_view.mapToGlobal(local_pos)

        popup: NumberSelector = NumberSelector(self.view, remaining_options, global_pos, cell_size)

        if popup.exec():
            new_number: int = popup.selected_number
            self._history.append((target_cell.x, target_cell.y, target_cell.value))
            target_cell.set_value(new_number)
            self.update_view()

    def undo(self) -> None:
        if not self._history:
            return
        x, y, old_value = self._history.pop()
        cell: Cell | None = self.model.get_cell(x, y)
        if cell is not None and not cell.immuable:
            cell.value = old_value
            self.update_view()

    def reset_grid(self) -> None:
        for pattern in self.model.patterns:
            for cell in pattern.cells:
                if not cell.immuable:
                    cell.set_value(0)
        self._history.clear()
        self.update_view()

    def generate_new_grid(self, width: int, height: int) -> None:
        """Génère une nouvelle grille aléatoire et met à jour la vue."""
        from generate_grid import generate_grid

        data: dict[str, list[list[int]]] = generate_grid(width, height)
        self.model = Grid.from_data(data)
        self._history.clear()
        self.update_view()
