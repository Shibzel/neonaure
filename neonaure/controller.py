"""
Neonaure - Controller module

This module acts as an intermediary between the model and the view:
- TODO
"""
from typing import Dict, Tuple, List, Set, Optional

from PyQt6.QtCore import QPoint
from .view import MainWindow, NumberSelector
from .model import Grid

# The Controller class is responsible for managing the game state and handling user interactions. It initializes the model and view, updates the view based on the model's state, and processes user clicks on the grid to update the model accordingly.
class Controller:
    def __init__(self, file_path: str) -> None:
        self.model: Grid = Grid.from_json(file_path)
        self.view: MainWindow = MainWindow(self)
        self.update_view()

    def update_view(self) -> None:
        values: Dict[Tuple[int, int], int] = {}
        thick_borders: List[Tuple[int, int, int, int]] = []

        for pattern in self.model.patterns:
            for cell in pattern.cells:
                if cell.value > 0:
                    values[(cell.y, cell.x)] = cell.value

        rows: int
        cols: int
        rows, cols = self.model.get_dimensions()

        pattern_membership: Dict[Tuple[int, int], str] = {}
        for pattern in self.model.patterns:
            for cell in pattern.cells:
                pattern_membership[(cell.y, cell.x)] = pattern.name

        for r in range(rows):
            for c in range(cols):
                current_pattern: Optional[str] = pattern_membership.get((r, c))

                if r == 0 or pattern_membership.get((r-1, c)) != current_pattern:
                    thick_borders.append((c, r, c+1, r))
                if r == rows - 1 or pattern_membership.get((r+1, c)) != current_pattern:
                    thick_borders.append((c, r+1, c+1, r+1))
                if c == 0 or pattern_membership.get((r, c-1)) != current_pattern:
                    thick_borders.append((c, r, c, r+1))
                if c == cols - 1 or pattern_membership.get((r, c+1)) != current_pattern:
                    thick_borders.append((c+1, r, c+1, r+1))

        self.view.grid_view.set_data(rows, cols, values, thick_borders)
    # The handle_click method processes user clicks on the grid.
    def handle_click(self, row: int, col: int) -> None:
        target_pattern: Optional[object] = None
        target_cell: Optional[object] = None

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
        possible_numbers: Set[int] = set(range(1, pattern_size + 1))
        used_numbers: Set[int] = {
            c.value
            for c in target_pattern.cells
            if c.value != 0
            and c.immuable
            and c != target_cell
        }
        remaining_options: List[int] = sorted(list(possible_numbers - used_numbers))

        if not remaining_options:
            return

        cell_size: int = self.view.grid_view.cell_size
        local_pos: QPoint = QPoint(col * cell_size, row * cell_size)
        global_pos: QPoint = self.view.grid_view.mapToGlobal(local_pos)

        popup: NumberSelector = NumberSelector(self.view, remaining_options, global_pos, cell_size)

        if popup.exec():
            new_number: int = popup.selected_number
            target_cell.set_value(new_number)
            self.update_view()