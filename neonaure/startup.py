"""
Neonaure - Startup Screen Module

This module provides the startup screen with a dynamic carousel, 
grid preview rendering, and saved game loading functionality.
"""

from __future__ import annotations

import os
import json
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, 
    QScrollArea, QFileDialog, QSizePolicy, QGraphicsDropShadowEffect
)
from PyQt6.QtGui import QPainter, QPen, QColor, QFont, QPixmap, QBrush, QCursor
from PyQt6.QtCore import Qt, pyqtSignal, QPoint, QSize, QPropertyAnimation, QRect

"""Import the model to read grid data for preview rendering"""
from .model import Grid

"""Dynamic determination of the grids directory path"""
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GRIDS_DIR = os.path.join(BASE_DIR, "data", "grids")

"""Color palette for patterns in the preview"""
PATTERN_COLORS = [
    QColor(0, 255, 204, 60),   
    QColor(255, 0, 204, 60),   
    QColor(255, 204, 0, 60),   
    QColor(0, 102, 255, 60),   
    QColor(102, 255, 0, 60),   
    QColor(255, 51, 51, 60),   
    QColor(153, 51, 255, 60),  
    QColor(255, 153, 51, 60),  
]


class GridCard(QPushButton):
    """Custom button representing a grid card in the carousel."""

    clicked_with_path = pyqtSignal(str)

    def __init__(self, file_path: str, parent=None):
        super().__init__(parent)
        self.file_path = file_path
        self.grid_name = os.path.splitext(os.path.basename(file_path))[0].replace("_", " ").title()
        
        self.setFixedSize(200, 250)
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        
        """Card layout setup"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        """Label for the preview image"""
        self.preview_label = QLabel()
        self.preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview_label.setFixedSize(180, 180)
        layout.addWidget(self.preview_label)

        """Label for the grid name"""
        self.name_label = QLabel(self.grid_name)
        self.name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.name_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        self.name_label.setStyleSheet("color: #E0E0E0; border: none;")
        layout.addWidget(self.name_label)

        """Trigger the preview rendering"""
        self._render_preview()

        """Base style and effects"""
        self.setStyleSheet("""
            GridCard {
                background-color: #2B2B2B;
                border: 2px solid #444;
                border-radius: 15px;
            }
            GridCard:hover {
                background-color: #3A3A3A;
                border: 2px solid #00FFCC;
            }
        """)

        """Glow effect on hover"""
        self.shadow = QGraphicsDropShadowEffect(self)
        self.shadow.setBlurRadius(20)
        self.shadow.setColor(QColor(0, 255, 204, 0)) 
        self.shadow.setOffset(0, 0)
        self.setGraphicsEffect(self.shadow)

        self.clicked.connect(lambda: self.clicked_with_path.emit(self.file_path))

    def _render_preview(self):
        """Generates a QPixmap of the grid for the preview."""
        try:
            grid = Grid.from_json(self.file_path)
            width, height = grid.get_dimensions()
            if width == 0 or height == 0:
                return

            pixmap = QPixmap(180, 180)
            pixmap.fill(Qt.GlobalColor.transparent)
            
            p = QPainter(pixmap)
            p.setRenderHint(QPainter.RenderHint.Antialiasing)

            margin = 10
            available_size = 180 - 2 * margin
            cell_size = min(available_size / width, available_size / height)
            
            ox = (180 - width * cell_size) / 2
            oy = (180 - height * cell_size) / 2

            """Assign colors to patterns"""
            pattern_colors = {}
            for i, pattern in enumerate(grid.patterns):
                pattern_colors[pattern.name] = PATTERN_COLORS[i % len(PATTERN_COLORS)]

            """Draw filled cells"""
            for pattern in grid.patterns:
                color = pattern_colors[pattern.name]
                p.setBrush(QBrush(color))
                p.setPen(Qt.PenStyle.NoPen)
                for cell in pattern.cells:
                    x = int(ox + cell.x * cell_size)
                    y = int(oy + cell.y * cell_size)
                    cs = int(cell_size)
                    p.drawRect(QRect(x, y, cs, cs))

            """Draw thick borders (similar logic to the controller)"""
            thick_pen = QPen(QColor("#E0E0E0"), max(2, int(cell_size * 0.1)))
            p.setPen(thick_pen)

            for r in range(height):
                for c in range(width):
                    current_pattern_name = None
                    cell = grid.get_cell(c, r)
                    if cell:
                        pat = grid.get_pattern_of(c, r)
                        if pat: 
                            current_pattern_name = pat.name

                    """Top border"""
                    if r == 0 or grid.get_pattern_of(c, r-1) is None or grid.get_pattern_of(c, r-1).name != current_pattern_name:
                        p.drawLine(QPoint(int(ox + c*cell_size), int(oy + r*cell_size)), QPoint(int(ox + (c+1)*cell_size), int(oy + r*cell_size)))
                    
                    """Bottom border"""
                    if r == height - 1 or grid.get_pattern_of(c, r+1) is None or grid.get_pattern_of(c, r+1).name != current_pattern_name:
                        p.drawLine(QPoint(int(ox + c*cell_size), int(oy + (r+1)*cell_size)), QPoint(int(ox + (c+1)*cell_size), int(oy + (r+1)*cell_size)))
                    
                    """Left border"""
                    if c == 0 or grid.get_pattern_of(c-1, r) is None or grid.get_pattern_of(c-1, r).name != current_pattern_name:
                        p.drawLine(QPoint(int(ox + c*cell_size), int(oy + r*cell_size)), QPoint(int(ox + c*cell_size), int(oy + (r+1)*cell_size)))
                    
                    """Right border"""
                    if c == width - 1 or grid.get_pattern_of(c+1, r) is None or grid.get_pattern_of(c+1, r).name != current_pattern_name:
                        p.drawLine(QPoint(int(ox + (c+1)*cell_size), int(oy + r*cell_size)), QPoint(int(ox + (c+1)*cell_size), int(oy + (r+1)*cell_size)))

            """Draw pre-filled values"""
            font = QFont("Arial", max(6, int(cell_size * 0.4)))
            p.setFont(font)
            p.setPen(QColor("#FFFFFF"))
            for pattern in grid.patterns:
                for cell in pattern.cells:
                    if cell.value != 0:
                        x = int(ox + cell.x * cell_size)
                        y = int(oy + cell.y * cell_size)
                        cs = int(cell_size)
                        p.drawText(QRect(x, y, cs, cs), Qt.AlignmentFlag.AlignCenter, str(cell.value))
            
            p.end()
            self.preview_label.setPixmap(pixmap)

        except Exception as e:
            print(f"Error while rendering {self.file_path}: {e}")

    def enterEvent(self, event):
        """Neon glow animation on hover enter"""
        self.anim = QPropertyAnimation(self.shadow, b"color")
        self.anim.setDuration(200)
        self.anim.setStartValue(QColor(0, 255, 204, 0))
        self.anim.setEndValue(QColor(0, 255, 204, 150))
        self.anim.start()
        super().enterEvent(event)

    def leaveEvent(self, event):
        """Neon glow animation on hover leave"""
        self.anim = QPropertyAnimation(self.shadow, b"color")
        self.anim.setDuration(200)
        self.anim.setStartValue(QColor(0, 255, 204, 150))
        self.anim.setEndValue(QColor(0, 255, 204, 0))
        self.anim.start()
        super().leaveEvent(event)


class StartupWindow(QMainWindow):
    """Startup window containing the grid selection carousel."""
    
    start_game_signal = pyqtSignal(str) 

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Neonaure - Startup")
        self.setFixedSize(900, 600)
        self.setStyleSheet("background-color: #1E1E1E; color: white;")

        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(40, 30, 40, 30)
        main_layout.setSpacing(30)

        """Title"""
        title = QLabel("NEONAURE")
        title.setFont(QFont("Arial", 48, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("color: #00FFCC; border: none;")
        main_layout.addWidget(title)

        subtitle = QLabel("Select a grid to start")
        subtitle.setFont(QFont("Arial", 14))
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setStyleSheet("color: #AAAAAA; border: none; margin-bottom: 10px;")
        main_layout.addWidget(subtitle)

        """Carousel Area"""
        carousel_container = QWidget()
        carousel_layout = QHBoxLayout(carousel_container)
        carousel_layout.setContentsMargins(0, 0, 0, 0)
        carousel_layout.setSpacing(10)

        """Left arrow"""
        left_arrow = QPushButton("◀")
        left_arrow.setFixedSize(40, 40)
        left_arrow.setStyleSheet(self._arrow_style())
        left_arrow.clicked.connect(lambda: self._scroll_carousel(-300))

        """Scrollable area"""
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll_area.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        
        self.carousel_content = QWidget()
        self.carousel_layout = QHBoxLayout(self.carousel_content)
        self.carousel_layout.setSpacing(20)
        self.carousel_layout.setContentsMargins(20, 0, 20, 0)
        self.carousel_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)

        self.scroll_area.setWidget(self.carousel_content)

        """Right arrow"""
        right_arrow = QPushButton("▶")
        right_arrow.setFixedSize(40, 40)
        right_arrow.setStyleSheet(self._arrow_style())
        right_arrow.clicked.connect(lambda: self._scroll_carousel(300))

        carousel_layout.addWidget(left_arrow)
        carousel_layout.addWidget(self.scroll_area, stretch=1)
        carousel_layout.addWidget(right_arrow)

        main_layout.addWidget(carousel_container, stretch=1)

        """Load saved game button"""
        self.load_btn = QPushButton("📂 Load a saved game")
        self.load_btn.setFixedHeight(50)
        self.load_btn.setFont(QFont("Arial", 12))
        self.load_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.load_btn.setStyleSheet("""
            QPushButton {
                background-color: #333333;
                color: #FFFFFF;
                border: 2px solid #555555;
                border-radius: 10px;
            }
            QPushButton:hover {
                background-color: #444444;
                border: 2px solid #FF00CC;
                color: #FF00CC;
            }
        """)
        self.load_btn.clicked.connect(self._load_saved_game)
        main_layout.addWidget(self.load_btn, alignment=Qt.AlignmentFlag.AlignCenter)

        """Dynamically load grids"""
        self._populate_carousel()

    def _arrow_style(self):
        """Returns the stylesheet for the carousel arrows."""
        return """
            QPushButton {
                background-color: #333333;
                color: white;
                border: none;
                border-radius: 20px;
                font-size: 18px;
            }
            QPushButton:hover {
                background-color: #00FFCC;
                color: #1E1E1E;
            }
        """

    def _populate_carousel(self):
        """Scans the data/grids folder and generates the cards."""
        if not os.path.exists(GRIDS_DIR):
            os.makedirs(GRIDS_DIR)
            return

        grid_files = [f for f in os.listdir(GRIDS_DIR) if f.endswith('.json')]
        
        """Sort to ensure consistent display order"""
        grid_files.sort()

        for grid_file in grid_files:
            file_path = os.path.join(GRIDS_DIR, grid_file)
            card = GridCard(file_path)
            card.clicked_with_path.connect(self._on_grid_selected)
            self.carousel_layout.addWidget(card)

    def _scroll_carousel(self, delta_x: int):
        """Scrolls the carousel smoothly."""
        scroll_bar = self.scroll_area.horizontalScrollBar()
        anim = QPropertyAnimation(scroll_bar, b"value")
        anim.setDuration(300)
        anim.setStartValue(scroll_bar.value())
        anim.setEndValue(scroll_bar.value() + delta_x)
        anim.start()

    def _on_grid_selected(self, file_path: str):
        """Called when the user clicks on a grid card."""
        self.start_game_signal.emit(file_path)
        self.close()

    def _load_saved_game(self):
        """Opens a file dialog to load a saved game file."""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Load save", "", "JSON Files (*.json)"
        )
        if file_path:
            self.start_game_signal.emit(file_path)
            self.close()