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

import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QWidget
from PyQt6.QtGui import QPainter, QPen, QColor, QFont
from PyQt6.QtCore import Qt, QRect, pyqtSignal

#The GridView class renders the game grid, handles user clicks, and displays cell values and borders.
class GridView(QWidget):
    cell_clicked = pyqtSignal(int, int)

    # Initializes the grid view with default settings (0 rows, 0 cols, empty values, no borders).
    def __init__(self, parent=None):
        super().__init__(parent)
        self.rows = 0
        self.cols = 0
        self.cell_size = 50
        self.values = {}
        self.thick_borders = []

    # Sets the grid data (rows, cols, cell values, and thick borders) and updates the display.
    def set_data(self, rows, cols, values, thick_borders):
        self.rows = rows
        self.cols = cols
        self.values = values
        self.thick_borders = thick_borders
        self.setMinimumSize(self.cols * self.cell_size + 20, self.rows * self.cell_size + 20)
        self.update()

    # Handles mouse click events to determine which cell was clicked and emits a signal with the cell coordinates.
    def mousePressEvent(self, event):
        x_rel = event.pos().x() - 10
        y_rel = event.pos().y() - 10
        col = x_rel // self.cell_size
        row = y_rel // self.cell_size
        if 0 <= row < self.rows and 0 <= col < self.cols:
            local_x = x_rel % self.cell_size
            local_y = y_rel % self.cell_size
            margin = 4
            if (margin <= local_x <= self.cell_size - margin) and (margin <= local_y <= self.cell_size - margin):
                self.cell_clicked.emit(col, row)

    # Paints the grid, cell values, and thick borders based on the current data. Uses anti-aliasing for smoother visuals.
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        painter.fillRect(self.rect(), Qt.GlobalColor.white)

        thin_pen = QPen(QColor(200, 200, 200), 1)
        painter.setPen(thin_pen)

        for i in range(self.rows):
            for j in range(self.cols):
                x = j * self.cell_size + 10
                y = i * self.cell_size + 10
                painter.drawRect(x, y, self.cell_size, self.cell_size)

        painter.setPen(QPen(Qt.GlobalColor.black))
        font = QFont("Arial", 16)
        painter.setFont(font)

        for (i, j), value in self.values.items():
            x = j * self.cell_size + 10
            y = i * self.cell_size + 10
            rect = QRect(x, y, self.cell_size, self.cell_size)
            painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, str(value))

        thick_pen = QPen(Qt.GlobalColor.black, 4)
        painter.setPen(thick_pen)

        for border in self.thick_borders:
            x1 = border[0] * self.cell_size + 10
            y1 = border[1] * self.cell_size + 10
            x2 = border[2] * self.cell_size + 10
            y2 = border[3] * self.cell_size + 10
            painter.drawLine(x1, y1, x2, y2)


# The MainWindow class sets up the main application window, integrates the GridView, and connects user interactions to the controller.
class MainWindow(QMainWindow):
    def __init__(self, controller):
        super().__init__()
        self.controller = controller
        self.setWindowTitle("Neonaure")
        self.grid_view = GridView(self)
        self.setCentralWidget(self.grid_view)
        self.grid_view.cell_clicked.connect(self.controller.handle_click)

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
    "motif15": [[5,5,0]]
}

# Prepares test data for the grid view by organizing cell values and determining where thick borders should be drawn.
def prepare_test_data(data):
    values = {}
    thick_borders = []
    rows = 8
    cols = 8
    
    pattern_membership = {}
    for pattern_name, cells in data.items():
        for r, c, v in cells:
            pattern_membership[(r, c)] = pattern_name
            if v > 0:
                values[(r, c)] = v
                
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
                
    return rows, cols, values, thick_borders


# TestWindow is a simple window for testing the GridView component with predefined data. It prints cell clicks to the console.
class TestWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Neonaure View Test")
        self.view = GridView(self)
        self.setCentralWidget(self.view)
        
        r, c, val, borders = prepare_test_data(test_data)
        self.view.set_data(r, c, val, borders)
        self.view.cell_clicked.connect(self.handle_test_click)

    def handle_test_click(self, col, row):
        print(f"Test click detected: col {col}, row {row}")

# The main block initializes the application, sets a basic style, creates the test window, and starts the event loop.
if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyleSheet("QWidget { background-color: white; color: black; }")
    window = TestWindow()
    window.show()
    sys.exit(app.exec())