"""
Neonaure - View Module

This module handles the graphical user interface (GUI) components, including:
- The main window and menu bar.
- The grid display component (interactive cells, visual feedback).
- User input handling (e.g., number selection, menu actions).
- Error/notification messages (e.g., invalid moves, victory).

The view observes the model and updates the display accordingly but does NOT
contain any game logic or data manipulation. All user interactions are
forwarded to the controller.
- TODO
"""

from __future__ import annotations

import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QWidget, QDialog, QPushButton, QGridLayout
from PyQt6.QtGui import QPainter, QPen, QColor, QFont, QResizeEvent, QMouseEvent, QPaintEvent
from PyQt6.QtCore import Qt, QRect, pyqtSignal, QPoint, QEvent
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .controller import Controller


class NumberSelector(QDialog):
    def __init__(self, parent: QWidget, options: list[int], cell_global_pos: QPoint, cell_size: int) -> None:
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowType.Popup | Qt.WindowType.FramelessWindowHint)
        self.selected_number: int | None = None

        layout: QGridLayout = QGridLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(2)

        btn_size: int = max(25, int(cell_size * 0.7))
        font_size: int = max(8, int(cell_size * 0.3))

        row: int = 0
        col: int = 0
        for opt in options:
            btn: QPushButton = QPushButton(str(opt))
            btn.setFixedSize(btn_size, btn_size)
            btn.setFont(QFont("Arial", font_size))
            btn.clicked.connect(lambda checked, n=opt: self.select_number(n))
            layout.addWidget(btn, row, col)
            col += 1
            if col > 2:
                col = 0
                row += 1

        self.adjustSize()

        popup_width: int = self.width()
        popup_height: int = self.height()

        x: int = cell_global_pos.x() + cell_size
        y: int = cell_global_pos.y() - (popup_height // 2) + (cell_size // 2)

        screen_geom = parent.screen().availableGeometry()
        if x + popup_width > screen_geom.right():
            x = cell_global_pos.x() - popup_width
        if y < screen_geom.top():
            y = screen_geom.top()
        if y + popup_height > screen_geom.bottom():
            y = screen_geom.bottom() - popup_height

        self.move(x, y)

    def select_number(self, n: int) -> None:
        self.selected_number = n
        self.accept()


class GridView(QWidget):
    cell_clicked: pyqtSignal = pyqtSignal(int, int)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.rows: int = 0
        self.cols: int = 0
        self.cell_size: int = 50
        self.offset_x: int = 10
        self.offset_y: int = 10
        self.values: dict[tuple[int, int], int] = {}
        self.thick_borders: list[tuple[int, int, int, int]] = []
        self.immutable_cells: set[tuple[int, int]] = set()
        self.pattern_membership: dict[tuple[int, int], str] = {}
        self.setMouseTracking(True)
        self.hovered_row: int = -1
        self.hovered_col: int = -1

    def _compute_cell_size(self) -> int:
        if self.rows == 0 or self.cols == 0:
            return 50
        available_w: int = self.width() - 20
        available_h: int = self.height() - 20
        cell_w: int = available_w // self.cols
        cell_h: int = available_h // self.rows
        return max(20, min(cell_w, cell_h))

    def _compute_offset(self) -> None:
        grid_w: int = self.cols * self.cell_size
        grid_h: int = self.rows * self.cell_size
        self.offset_x = max(0, (self.width() - grid_w) // 2)
        self.offset_y = max(0, (self.height() - grid_h) // 2)

    def _compute_conflicts(self) -> set[tuple[int, int]]:
        conflicts: set[tuple[int, int]] = set()
        for (r, c), value in self.values.items():
            for dr in (-1, 0, 1):
                for dc in (-1, 0, 1):
                    if dr == 0 and dc == 0:
                        continue
                    nr: int = r + dr
                    nc: int = c + dc
                    if self.values.get((nr, nc)) == value:
                        conflicts.add((r, c))

        if self.pattern_membership:
            pattern_cells: dict[str, list[tuple[int, int]]] = {}
            for pos, pname in self.pattern_membership.items():
                pattern_cells.setdefault(pname, []).append(pos)

            for cells in pattern_cells.values():
                for i, (r1, c1) in enumerate(cells):
                    v1: int | None = self.values.get((r1, c1))
                    if v1 is None:
                        continue
                    for r2, c2 in cells[i + 1:]:
                        if self.values.get((r2, c2)) == v1:
                            conflicts.add((r1, c1))
                            conflicts.add((r2, c2))

        return conflicts

    def resizeEvent(self, event: QResizeEvent) -> None:  # type: ignore[override]
        self.cell_size = self._compute_cell_size()
        self._compute_offset()
        super().resizeEvent(event)
        self.update()

    def set_data(
        self,
        rows: int,
        cols: int,
        values: dict[tuple[int, int], int],
        thick_borders: list[tuple[int, int, int, int]],
        immutable_cells: set[tuple[int, int]],
        pattern_membership: dict[tuple[int, int], str] | None = None,
    ) -> None:
        self.rows = rows
        self.cols = cols
        self.values = values
        self.thick_borders = thick_borders
        self.immutable_cells = immutable_cells
        self.pattern_membership = pattern_membership or {}
        self.setMinimumSize(self.cols * 20 + 20, self.rows * 20 + 20)
        self.cell_size = self._compute_cell_size()
        self._compute_offset()
        self.update()

    def mouseMoveEvent(self, event: QMouseEvent) -> None:  # type: ignore[override]
        x_rel: int = event.pos().x() - self.offset_x
        y_rel: int = event.pos().y() - self.offset_y
        col: int = x_rel // self.cell_size
        row: int = y_rel // self.cell_size

        if 0 <= row < self.rows and 0 <= col < self.cols:
            if self.hovered_row != row or self.hovered_col != col:
                self.hovered_row = row
                self.hovered_col = col
                self.update()
        else:
            if self.hovered_row != -1 or self.hovered_col != -1:
                self.hovered_row = -1
                self.hovered_col = -1
                self.update()

    def leaveEvent(self, event: QEvent) -> None:  # type: ignore[override]
        self.hovered_row = -1
        self.hovered_col = -1
        self.update()

    def mousePressEvent(self, event: QMouseEvent) -> None:  # type: ignore[override]
        x_rel: int = event.pos().x() - self.offset_x
        y_rel: int = event.pos().y() - self.offset_y
        col: int = x_rel // self.cell_size
        row: int = y_rel // self.cell_size
        if 0 <= row < self.rows and 0 <= col < self.cols:
            local_x: int = x_rel % self.cell_size
            local_y: int = y_rel % self.cell_size
            margin: int = 4
            if (margin <= local_x <= self.cell_size - margin) and (margin <= local_y <= self.cell_size - margin):
                self.cell_clicked.emit(col, row)

    def paintEvent(self, event: QPaintEvent) -> None:  # type: ignore[override]
        painter: QPainter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        painter.fillRect(self.rect(), Qt.GlobalColor.white)

        ox: int = self.offset_x
        oy: int = self.offset_y
        cs: int = self.cell_size

        for i in range(self.rows):
            for j in range(self.cols):
                x: int = j * cs + ox
                y: int = i * cs + oy

                if (i, j) in self.immutable_cells:
                    painter.fillRect(x, y, cs, cs, QColor(200, 200, 200))
                elif i == self.hovered_row and j == self.hovered_col:
                    painter.fillRect(x, y, cs, cs, QColor(240, 240, 240))

                thin_pen: QPen = QPen(QColor(200, 200, 200), 1)
                painter.setPen(thin_pen)
                painter.drawRect(x, y, cs, cs)

        painter.setPen(QPen(Qt.GlobalColor.black))
        font: QFont = QFont("Arial", max(8, int(cs * 0.35)))
        painter.setFont(font)

        conflicts: set[tuple[int, int]] = self._compute_conflicts()
        red_pen: QPen = QPen(QColor(220, 30, 30))

        for (i, j), value in self.values.items():
            x = j * cs + ox
            y = i * cs + oy
            rect: QRect = QRect(x, y, cs, cs)
            if (i, j) in conflicts:
                painter.setPen(red_pen)
            else:
                painter.setPen(QPen(Qt.GlobalColor.black))
            painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, str(value))

        thick_pen: QPen = QPen(Qt.GlobalColor.black, max(2, int(cs * 0.08)))
        painter.setPen(thick_pen)

        for border in self.thick_borders:
            x1: int = border[0] * cs + ox
            y1: int = border[1] * cs + oy
            x2: int = border[2] * cs + ox
            y2: int = border[3] * cs + oy
            painter.drawLine(x1, y1, x2, y2)


class MainWindow(QMainWindow):
    def __init__(self, controller: Controller) -> None:
        super().__init__()
        self.controller: Controller = controller
        self.setWindowTitle("Neonaure")
        self.grid_view: GridView = GridView(self)
        self.setCentralWidget(self.grid_view)
        self.grid_view.cell_clicked.connect(self.controller.handle_click)  # type: ignore[arg-type]
        self.resize(500, 500)


test_data: dict[str, list[list[int]]] = {
    "motif1": [[0,0,0], [1,0,0], [0,1,0], [1,1,3], [2,1,0]],
    "motif2": [[2,0,5], [3,0,0], [4,0,0], [4,1,0], [5,0,0]],
    "motif3": [[6,0,0], [5,1,0], [6,1,4], [6,2,0], [7,0,0]],
    "motif4": [[0,2,5], [1,2,0], [0,3,0], [1,3,0], [0,4,0]],
    "motif5": [[2,2,0], [2,3,0], [3,1,0], [3,2,0], [4,2,0]],
    "motif6": [[5,2,0], [4,3,0], [5,3,5], [4,4,0], [5,4,0]],
    "motif7": [[7,3,0], [6,4,0], [7,4,2], [7,5,0], [7,6,0]],
    "motif8": [[0,5,0], [0,6,0], [1,5,3], [1,4,0], [2,4,0]],
    "motif9": [[2,5,0], [3,5,0], [4,5,0], [3,4,0], [3,3,0]],
    "motif10": [[0,7,3], [1,6,0], [1,7,0], [2,6,5], [2,7,0]],
    "motif11": [[7,1,0], [7,2,0]],
    "motif12": [[3,6,0], [4,6,0],[3,7,0], [4,7,0], [5,7,2]],
    "motif13": [[5,6,0], [6,5,0], [6,6,0], [6,7,0], [7,7,0]],
    "motif14": [[6,3,0]],
    "motif15": [[5,5,0]],
}


def prepare_test_data(
    data: dict[str, list[list[int]]],
) -> tuple[int, int, dict[tuple[int, int], int], list[tuple[int, int, int, int]], set[tuple[int, int]], dict[tuple[int, int], str]]:
    values: dict[tuple[int, int], int] = {}
    thick_borders: list[tuple[int, int, int, int]] = []
    immutable_cells: set[tuple[int, int]] = set()
    rows: int = 8
    cols: int = 8

    pattern_membership: dict[tuple[int, int], str] = {}
    for pattern_name, cells in data.items():
        for r, c, v in cells:
            pattern_membership[(r, c)] = pattern_name
            if v > 0:
                values[(r, c)] = v
                immutable_cells.add((r, c))

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

    return rows, cols, values, thick_borders, immutable_cells, pattern_membership


class TestWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Neonaure View Test")
        self.resize(500, 500)
        self.view: GridView = GridView(self)
        self.setCentralWidget(self.view)

        r: int
        c: int
        val: dict[tuple[int, int], int]
        borders: list[tuple[int, int, int, int]]
        immutables: set[tuple[int, int]]
        p_membership: dict[tuple[int, int], str]
        r, c, val, borders, immutables, p_membership = prepare_test_data(test_data)
        self.view.set_data(r, c, val, borders, immutables, p_membership)
        self.pattern_membership: dict[tuple[int, int], str] = p_membership
        self.immutable_cells: set[tuple[int, int]] = immutables
        self.values: dict[tuple[int, int], int] = val
        self.view.cell_clicked.connect(self.handle_test_click)  # type: ignore[arg-type]

    def handle_test_click(self, col: int, row: int) -> None:
        if (row, col) in self.immutable_cells:
            return

        current_pattern: str | None = self.pattern_membership.get((row, col))
        if not current_pattern:
            return

        pattern_cells: list[tuple[int, int]] = [
            (r, c) for (r, c), p in self.pattern_membership.items() if p == current_pattern
        ]
        pattern_size: int = len(pattern_cells)

        possible_numbers: set[int] = set(range(1, pattern_size + 1))
        used_numbers: set[int] = {
            self.values.get((r, c))
            for r, c in pattern_cells
            if self.values.get((r, c)) is not None
            and (r, c) in self.immutable_cells
            and (r, c) != (row, col)
        }
        remaining_options: list[int] = sorted(list(possible_numbers - used_numbers))

        if not remaining_options:
            return

        cell_size: int = self.view.cell_size
        local_pos: QPoint = QPoint(
            col * cell_size + self.view.offset_x,
            row * cell_size + self.view.offset_y,
        )
        global_pos: QPoint = self.view.mapToGlobal(local_pos)

        popup: NumberSelector = NumberSelector(self, remaining_options, global_pos, cell_size)
        if popup.exec():
            new_number: int = popup.selected_number
            if new_number == self.values.get((row, col)):
                del self.values[(row, col)]
            else:
                self.values[(row, col)] = new_number
            self.view.set_data(
                self.view.rows, self.view.cols, self.values,
                self.view.thick_borders, self.immutable_cells,
                self.pattern_membership,
            )


if __name__ == "__main__":
    app: QApplication = QApplication(sys.argv)
    app.setStyleSheet("QWidget { background-color: white; color: black; }")
    window: TestWindow = TestWindow()
    window.show()
    sys.exit(app.exec())
