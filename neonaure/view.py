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

import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QWidget, QDialog, QPushButton, QGridLayout
from PyQt6.QtGui import QPainter, QPen, QColor, QFont
from PyQt6.QtCore import Qt, QRect, pyqtSignal, QPoint

# NumberSelector is a popup dialog that appears when the user clicks on an empty cell, allowing them to select a number from the valid options for that cell's pattern.
class NumberSelector(QDialog):
    def __init__(self, parent, options, cell_global_pos, cell_size):
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
            btn.clicked.connect(lambda checked, n=opt: self.select_number(n))
            layout.addWidget(btn, row, col)
            col += 1
            if col > 2:
                col = 0
                row += 1

        self.adjustSize()

        popup_width = self.width()
        popup_height = self.height()
        
        x = cell_global_pos.x() + cell_size
        y = cell_global_pos.y() - (popup_height // 2) + (cell_size // 2)

        screen_geom = parent.screen().availableGeometry()
        if x + popup_width > screen_geom.right():
            x = cell_global_pos.x() - popup_width
        if y < screen_geom.top():
            y = screen_geom.top()
        if y + popup_height > screen_geom.bottom():
            y = screen_geom.bottom() - popup_height

        self.move(x, y)

    def select_number(self, n):
        self.selected_number = n
        self.accept()

"""
The GridView class is responsible for rendering the game grid, including cells, numbers, and borders. 
It also handles mouse events to detect clicks on cells and hover effects.
"""
class GridView(QWidget):
    cell_clicked: pyqtSignal = pyqtSignal(int, int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.rows: int = 0
        self.cols: int = 0
        self.cell_size: int = 50
        self._offset_x: int = 10
        self._offset_y: int = 10
        self.values: dict = {}
        self.thick_borders: list = []
        self.immutable_cells: set = set()
        self.setMouseTracking(True)
        self.hovered_row: int = -1
        self.hovered_col: int = -1

    def _compute_cell_size(self) -> int:
        if self.rows == 0 or self.cols == 0:
            return 50
        available_w = self.width() - 20
        available_h = self.height() - 20
        cell_w = available_w // self.cols
        cell_h = available_h // self.rows
        return max(20, min(cell_w, cell_h))

    def _compute_offset(self):
        grid_w = self.cols * self.cell_size
        grid_h = self.rows * self.cell_size
        self._offset_x = max(0, (self.width() - grid_w) // 2)
        self._offset_y = max(0, (self.height() - grid_h) // 2)

    def resizeEvent(self, event):
        self.cell_size = self._compute_cell_size()
        self._compute_offset()
        super().resizeEvent(event)
        self.update()

    def set_data(self, rows, cols, values, thick_borders, immutable_cells):
        self.rows: int = rows
        self.cols: int = cols
        self.values: dict = values
        self.thick_borders: list = thick_borders
        self.immutable_cells: set = immutable_cells
        self.setMinimumSize(self.cols * 20 + 20, self.rows * 20 + 20)
        self.cell_size = self._compute_cell_size()
        self._compute_offset()
        self.update()

    """
    Mouse event handlers to detect clicks and hover effects on cells
    """
    def mouseMoveEvent(self, event):
        x_rel = event.pos().x() - self._offset_x
        y_rel = event.pos().y() - self._offset_y
        col = x_rel // self.cell_size
        row = y_rel // self.cell_size
        
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

    """
    When the mouse leaves the grid area, reset hover state
    """
    def leaveEvent(self, event):
        self.hovered_row = -1
        self.hovered_col = -1
        self.update()

    """
    When a cell is clicked, emit the cell_clicked signal with the column and row indices
    """
    def mousePressEvent(self, event):
        x_rel = event.pos().x() - self._offset_x
        y_rel = event.pos().y() - self._offset_y
        col = x_rel // self.cell_size
        row = y_rel // self.cell_size
        if 0 <= row < self.rows and 0 <= col < self.cols:
            local_x = x_rel % self.cell_size
            local_y = y_rel % self.cell_size
            margin = 4
            if (margin <= local_x <= self.cell_size - margin) and (margin <= local_y <= self.cell_size - margin):
                self.cell_clicked.emit(col, row)

    """
    The paintEvent method is responsible for drawing the grid, including cells, numbers, and borders. 
    It uses QPainter to render the visual elements based on the current state of the grid.
    """
    def paintEvent(self, event):
        painter: QPainter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        painter.fillRect(self.rect(), Qt.GlobalColor.white)

        ox, oy = self._offset_x, self._offset_y
        cs = self.cell_size

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

        for (i, j), value in self.values.items():
            x: int = j * cs + ox
            y: int = i * cs + oy
            rect: QRect = QRect(x, y, cs, cs)
            painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, str(value))

        thick_pen: QPen = QPen(Qt.GlobalColor.black, max(2, int(cs * 0.08)))
        painter.setPen(thick_pen)

        for border in self.thick_borders:
            x1: int = border[0] * cs + ox
            y1: int = border[1] * cs + oy
            x2: int = border[2] * cs + ox
            y2: int = border[3] * cs + oy
            painter.drawLine(x1, y1, x2, y2)


"""
The MainWindow class is the main application window that contains the GridView. 
It initializes the GUI and connects the cell_clicked signal from the GridView to 
the controller's handle_click method, allowing user interactions to be processed by the controller.
"""
class MainWindow(QMainWindow):
    def __init__(self, controller):
        super().__init__()
        self.controller: Controller = controller
        self.setWindowTitle("Neonaure")
        self.grid_view = GridView(self)
        self.setCentralWidget(self.grid_view)
        self.grid_view.cell_clicked.connect(self.controller.handle_click)
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
    "motif15": [[5,5,0]]
}

"""
prepare_test_data is a helper function that processes the test data to extract values, 
thick borders, immutable cells, and pattern membership information.
"""
def prepare_test_data(data):
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

""" 
The TestWindow class is a simple test application that initializes the GridView 
with prepared test data and allows the user to interact with the grid. 
It demonstrates how the view can be used independently for testing purposes. 
"""
class TestWindow(QMainWindow):
    def __init__(self):
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
        self.view.set_data(r, c, val, borders, immutables)
        self.pattern_membership: dict[tuple[int, int], str] = p_membership
        self.immutable_cells: set[tuple[int, int]] = immutables
        self.values: dict[tuple[int, int], int] = val
        self.view.cell_clicked.connect(self.handle_test_click)

    def handle_test_click(self, col: int, row: int):
        if (row, col) in self.immutable_cells:
            return

        current_pattern: str = self.pattern_membership.get((row, col))
        if not current_pattern:
            return
            
        pattern_cells: list[tuple[int, int]] = [(r, c) for (r, c), p in self.pattern_membership.items() if p == current_pattern]
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
            col * cell_size + self.view._offset_x,
            row * cell_size + self.view._offset_y,
        )
        global_pos: QPoint = self.view.mapToGlobal(local_pos)

        popup: NumberSelector = NumberSelector(self, remaining_options, global_pos, cell_size)
        if popup.exec():
            new_number: int = popup.selected_number
            if new_number == self.values.get((row, col)):
                del self.values[(row, col)]
            else:
                self.values[(row, col)] = new_number
            self.view.set_data(self.view.rows, self.view.cols, self.values, self.view.thick_borders, self.immutable_cells)

if __name__ == "__main__":
    app: QApplication = QApplication(sys.argv)
    app.setStyleSheet("QWidget { background-color: white; color: black; }")
    window: TestWindow = TestWindow()
    window.show()
    sys.exit(app.exec())