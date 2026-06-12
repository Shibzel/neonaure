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
"""

import os
import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QWidget, QDialog, QPushButton, QGridLayout, QHBoxLayout, QVBoxLayout, QSizePolicy, QSpinBox, QFormLayout, QLabel
from PyQt6.QtGui import QPainter, QPen, QColor, QFont, QResizeEvent, QMouseEvent, QPaintEvent, QPixmap, QIcon
from PyQt6.QtCore import Qt, QRect, pyqtSignal, QPoint, QEvent, QSize

# Base paths for the project and assets folder
_BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_ASSETS_DIR = os.path.join(_BASE_DIR, "assets", "icons")

# Returns the absolute path of an icon in the assets folder
def _icon_path(name: str) -> str:
    return os.path.join(_ASSETS_DIR, name)


# Popup for selecting a number for a cell
class NumberSelector(QDialog):
    def __init__(self, parent: QWidget, options: list[int], cell_global_pos: QPoint, cell_size: int) -> None:
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowType.Popup | Qt.WindowType.FramelessWindowHint)
        self.selected_number = None

        layout = QGridLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(2)

        btn_size = max(25, int(cell_size * 0.7))
        font_size = max(8, int(cell_size * 0.3))

        row = 0
        col = 0
        for opt in options:
            btn = QPushButton(str(opt))
            btn.setFixedSize(btn_size, btn_size)
            btn.setFont(QFont("Arial", font_size))
            btn.numero = opt
            btn.clicked.connect(self._on_btn_clicked)
            layout.addWidget(btn, row, col)
            col += 1
            if col > 2:
                col = 0
                row += 1

        # Bouton croix pour fermer le popup
        close_btn = QPushButton()
        close_btn.setIcon(QIcon(_icon_path("cross.png")))
        close_btn.setIconSize(QSize(btn_size - 8, btn_size - 8))
        close_btn.setFixedSize(btn_size, btn_size)
        close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        close_btn.setToolTip("Fermer")
        close_btn.clicked.connect(lambda checked=False: self.reject())
        layout.addWidget(close_btn, row, col)

        self.adjustSize()
        self.move(cell_global_pos.x() + cell_size, cell_global_pos.y())

    def _on_btn_clicked(self):
        bouton = self.sender()
        self.selected_number = bouton.numero
        self.accept()

    # Saves the selected number and closes the popup
    def select_number(self, n):
        self.selected_number = n
        self.accept()


# Dialogue de victoire affiche quand la grille est terminee sans erreur
class VictoryDialog(QDialog):
    def __init__(self, parent: QWidget) -> None:
        super().__init__(parent)
        self.setWindowTitle("Victoire !")
        self.setFixedSize(300, 200)

        layout = QVBoxLayout(self)

        label = QLabel("Bravo, vous avez gagnÈ !")
        label.setFont(QFont("Arial", 16))
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(label)

        layout.addSpacing(20)

        menu_btn = QPushButton("Retour au menu")
        menu_btn.setFixedSize(180, 40)
        menu_btn.setFont(QFont("Arial", 12))
        menu_btn.clicked.connect(self.accept)
        layout.addWidget(menu_btn, alignment=Qt.AlignmentFlag.AlignCenter)


# Widget d'affichage et d'interaction avec la grille de jeu
class GridView(QWidget):
    cell_clicked = pyqtSignal(int, int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.rows = 0
        self.cols = 0
        self.cell_size = 50
        self.offset_x = 10
        self.offset_y = 10
        self.values = {}
        self.thick_borders = []
        self.immutable_cells = set()
        self.pattern_membership = {}

    # Calculates cell size so the grid fits in the widget
    def _compute_cell_size(self) -> int:
        if self.rows == 0 or self.cols == 0:
            return 50
        available_w = self.width() - 20
        available_h = self.height() - 20
        cell_w = available_w // self.cols if self.cols > 0 else 50
        cell_h = available_h // self.rows if self.rows > 0 else 50
        # Reduced minimum limit to 5 to adapt to highly rectangular grids
        return max(5, min(cell_w, cell_h))

    # Centers the grid in the widget
    def _compute_offset(self) -> None:
        grid_w = self.cols * self.cell_size
        grid_h = self.rows * self.cell_size
        self.offset_x = max(0, (self.width() - grid_w) // 2)
        self.offset_y = max(0, (self.height() - grid_h) // 2)

    # Detects conflicts: identical values among neighbors or within the same pattern
    def _compute_conflicts(self) -> list[tuple[int, int]]:
        conflicts = []

        for (r, c), value in self.values.items():
            for dr in (-1, 0, 1):
                for dc in (-1, 0, 1):
                    if dr == 0 and dc == 0:
                        continue
                    nr = r + dr
                    nc = c + dc
                    if self.values.get((nr, nc)) == value:
                        if (r, c) not in conflicts:
                            conflicts.append((r, c))

        if self.pattern_membership:
            pattern_cells = {}
            for pos, pname in self.pattern_membership.items():
                if pname not in pattern_cells:
                    pattern_cells[pname] = []
                pattern_cells[pname].append(pos)

            for cells in pattern_cells.values():
                for i in range(len(cells)):
                    r1, c1 = cells[i]
                    v1 = self.values.get((r1, c1))
                    if v1 is None:
                        continue
                    for j in range(i + 1, len(cells)):
                        r2, c2 = cells[j]
                        if self.values.get((r2, c2)) == v1:
                            if (r1, c1) not in conflicts:
                                conflicts.append((r1, c1))
                            if (r2, c2) not in conflicts:
                                conflicts.append((r2, c2))

        return conflicts

    # Recalculates cell size and centering on resize
    def resizeEvent(self, event: QResizeEvent) -> None:
        self.cell_size = self._compute_cell_size()
        self._compute_offset()
        super().resizeEvent(event)
        self.update()

    # Updates the data displayed by the grid
    def set_data(
        self,
        rows: int,
        cols: int,
        values: dict[tuple[int, int], int],
        thick_borders: list[tuple[int, int, int, int]],
        immutable_cells: set[tuple[int, int]],
        pattern_membership=None,
    ) -> None:
        self.rows = rows
        self.cols = cols
        self.values = values
        self.thick_borders = thick_borders
        self.immutable_cells = immutable_cells
        self.pattern_membership = pattern_membership or {}
        # Reduced margin to avoid window explosion on special formats
        self.setMinimumSize(self.cols * 5 + 20, self.rows * 5 + 20)
        self.cell_size = self._compute_cell_size()
        self._compute_offset()
        self.update()

    # Emits a signal when the user clicks on a modifiable cell
    def mousePressEvent(self, event: QMouseEvent) -> None:
        x_rel = event.pos().x() - self.offset_x
        y_rel = event.pos().y() - self.offset_y
        col = x_rel // self.cell_size
        row = y_rel // self.cell_size
        if 0 <= row < self.rows and 0 <= col < self.cols:
            local_x = x_rel % self.cell_size
            local_y = y_rel % self.cell_size
            margin = 4
            if (margin <= local_x <= self.cell_size - margin) and (margin <= local_y <= self.cell_size - margin):
                self.cell_clicked.emit(col, row)

    # Draws the grid: cells, values, thick borders, and conflicts
    def paintEvent(self, event: QPaintEvent) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        painter.fillRect(self.rect(), Qt.GlobalColor.white)

        ox = self.offset_x
        oy = self.offset_y
        cs = self.cell_size

        for i in range(self.rows):
            for j in range(self.cols):
                x = j * cs + ox
                y = i * cs + oy

                if (i, j) in self.immutable_cells:
                    painter.fillRect(x, y, cs, cs, QColor(200, 200, 200))

                thin_pen = QPen(QColor(200, 200, 200), 1)
                painter.setPen(thin_pen)
                painter.drawRect(x, y, cs, cs)

        painter.setPen(QPen(Qt.GlobalColor.black))
        font = QFont("Arial", max(8, int(cs * 0.35)))
        painter.setFont(font)

        conflicts = self._compute_conflicts()
        red_pen = QPen(QColor(220, 30, 30))

        for (i, j), value in self.values.items():
            x = j * cs + ox
            y = i * cs + oy
            rect = QRect(x, y, cs, cs)
            if (i, j) in conflicts:
                painter.setPen(red_pen)
            else:
                painter.setPen(QPen(Qt.GlobalColor.black))
            painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, str(value))

        thick_pen = QPen(Qt.GlobalColor.black, max(2, int(cs * 0.08)))
        painter.setPen(thick_pen)

        for border in self.thick_borders:
            x1 = border[0] * cs + ox
            y1 = border[1] * cs + oy
            x2 = border[2] * cs + ox
            y2 = border[3] * cs + oy
            painter.drawLine(x1, y1, x2, y2)


# Dialog to choose the size of a new grid
class GridSizeDialog(QDialog):
    """Popup to choose the X/Y dimensions of the new grid."""

    def __init__(self, parent: QWidget) -> None:
        super().__init__(parent)
        self.setWindowTitle("Nouvelle grille")
        self.setFixedSize(220, 150)

        layout = QFormLayout(self)

        self.spin_width = QSpinBox()
        self.spin_width.setRange(4, 12)
        self.spin_width.setValue(8)
        layout.addRow("Largeur :", self.spin_width)

        self.spin_height = QSpinBox()
        self.spin_height.setRange(4, 12)
        self.spin_height.setValue(8)
        layout.addRow("Hauteur :", self.spin_height)

        confirm_btn = QPushButton("GÈnÈrer")
        confirm_btn.clicked.connect(self.accept)
        layout.addRow(confirm_btn)


# Main game window with the grid and buttons
class MainWindow(QMainWindow):
    def __init__(self, controller) -> None:
        super().__init__()
        self.controller = controller
        self.setWindowTitle("Neonaure")
        self.grid_view = GridView()

        central = QWidget()
        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(self.grid_view, stretch=1)

        btn_panel = QVBoxLayout()
        btn_panel.setSpacing(8)

        self.undo_button = QPushButton()
        self.undo_button.setIcon(QIcon(_icon_path("undo.png")))
        self.undo_button.setIconSize(QSize(40, 40))
        self.undo_button.setFixedSize(56, 56)
        self.undo_button.setToolTip("Annuler le dernier coup")
        self.undo_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.undo_button.clicked.connect(self.controller.undo)
        btn_panel.addWidget(self.undo_button)

        self.reset_button = QPushButton()
        self.reset_button.setIcon(QIcon(_icon_path("trash.png")))
        self.reset_button.setIconSize(QSize(40, 40))
        self.reset_button.setFixedSize(56, 56)
        self.reset_button.setToolTip("RÈinitialiser la grille")
        self.reset_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.reset_button.clicked.connect(self.controller.reset_grid)
        btn_panel.addWidget(self.reset_button)

        self.map_button = QPushButton()
        self.map_button.setIcon(QIcon(_icon_path("map.png")))
        self.map_button.setIconSize(QSize(40, 40))
        self.map_button.setFixedSize(56, 56)
        self.map_button.setToolTip("Nouvelle carte alÈatoire")
        self.map_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.map_button.clicked.connect(self._on_map_clicked)
        btn_panel.addWidget(self.map_button)

        btn_panel.addStretch()
        main_layout.addLayout(btn_panel)

        self.setCentralWidget(central)
        self.grid_view.cell_clicked.connect(self.controller.handle_click)  # type: ignore[arg-type]
        self.resize(560, 500)

    # Opens the dialog to generate a new map
    def _on_map_clicked(self) -> None:
        """Opens the size dialog then asks the controller to generate."""
        dialog = GridSizeDialog(self)
        if dialog.exec():
            self.controller.generate_new_grid(
                dialog.spin_width.value(),
                dialog.spin_height.value(),
            )


# Test grid with 15 predefined patterns
test_data = {
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

# Transforms raw data into structures usable by GridView
def prepare_test_data(data):
    values = {}
    thick_borders = []
    immutable_cells = set()
    rows = 8
    cols = 8

    pattern_membership = {}
    for pattern_name, cells in data.items():
        for r, c, v in cells:
            pattern_membership[(r, c)] = pattern_name
            if v > 0:
                values[(r, c)] = v
                immutable_cells.add((r, c))

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

    return rows, cols, values, thick_borders, immutable_cells, pattern_membership


# Standalone test window to test the view without the controller
class TestWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Neonaure View Test")
        self.resize(560, 500)
        self.view = GridView()
        self.history = []

        central = QWidget()
        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(self.view, stretch=1)

        btn_panel = QVBoxLayout()
        btn_panel.setSpacing(8)

        self.undo_button = QPushButton()
        self.undo_button.setIcon(QIcon(_icon_path("undo.png")))
        self.undo_button.setIconSize(QSize(40, 40))
        self.undo_button.setFixedSize(56, 56)
        self.undo_button.setToolTip("Annuler le dernier coup")
        self.undo_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.undo_button.clicked.connect(self.undo)
        btn_panel.addWidget(self.undo_button)

        self.reset_button = QPushButton()
        self.reset_button.setIcon(QIcon(_icon_path("trash.png")))
        self.reset_button.setIconSize(QSize(40, 40))
        self.reset_button.setFixedSize(56, 56)
        self.reset_button.setToolTip("RÈinitialiser la grille")
        self.reset_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.reset_button.clicked.connect(self.reset_grid)
        btn_panel.addWidget(self.reset_button)

        btn_panel.addStretch()
        main_layout.addLayout(btn_panel)

        self.setCentralWidget(central)

        r, c, val, borders, immutables, p_membership = prepare_test_data(test_data)
        self.view.set_data(r, c, val, borders, immutables, p_membership)
        self.pattern_membership = p_membership
        self.immutable_cells = immutables
        self.values = val
        self.view.cell_clicked.connect(self.handle_test_click)  # type: ignore[arg-type]

    # Handles clicking on a cell in test mode
    def handle_test_click(self, col, row):
        if (row, col) in self.immutable_cells:
            return

        current_pattern = self.pattern_membership.get((row, col))
        if not current_pattern:
            return

        pattern_cells = []
        for (r, c), p in self.pattern_membership.items():
            if p == current_pattern:
                pattern_cells.append((r, c))
        pattern_size = len(pattern_cells)

        possible_numbers = []
        for n in range(1, pattern_size + 1):
            possible_numbers.append(n)
        for r, c in pattern_cells:
            if (r, c) in self.immutable_cells and (r, c) != (row, col):
                val = self.values.get((r, c))
                if val is not None:
                    if val in possible_numbers:
                        possible_numbers.remove(val)
        remaining_options = possible_numbers

        if not remaining_options:
            return

        cell_size = self.view.cell_size
        local_pos = QPoint(
            col * cell_size + self.view.offset_x,
            row * cell_size + self.view.offset_y,
        )
        global_pos = self.view.mapToGlobal(local_pos)

        popup = NumberSelector(self, remaining_options, global_pos, cell_size)
        if popup.exec():
            new_number = popup.selected_number
            old_value = self.values.get((row, col))
            if new_number == self.values.get((row, col)):
                del self.values[(row, col)]
                self.history.append(((row, col), old_value if old_value is not None else 0))
            else:
                self.values[(row, col)] = new_number
                self.history.append(((row, col), old_value if old_value is not None else 0))
            self.view.set_data(
                self.view.rows, self.view.cols, self.values,
                self.view.thick_borders, self.immutable_cells,
                self.pattern_membership,
            )

    # Undoes the last move played in test mode
    def undo(self):
        if not self.history:
            return
        pos, old_value = self.history.pop()
        if old_value == 0:
            self.values.pop(pos, None)
        else:
            self.values[pos] = old_value
        self.view.set_data(
            self.view.rows, self.view.cols, self.values,
            self.view.thick_borders, self.immutable_cells,
            self.pattern_membership,
        )

    # Resets the grid by removing non-immutable values
    def reset_grid(self):
        keys_to_remove = []
        for pos in self.values:
            if pos not in self.immutable_cells:
                keys_to_remove.append(pos)
        for key in keys_to_remove:
            del self.values[key]
        self.history.clear()
        self.view.set_data(
            self.view.rows, self.view.cols, self.values,
            self.view.thick_borders, self.immutable_cells,
            self.pattern_membership,
        )


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyleSheet("QWidget { background-color: white; color: black; }")
    window = TestWindow()
    window.show()
    sys.exit(app.exec())
