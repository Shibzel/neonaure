"""
Neonaure - Startup Module

Handles the game's startup screen, campaign grid detection,
clean preview (without text), visual locking, and progression.
"""

import os
import json
import re
from glob import glob
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QLabel, QGridLayout, 
                             QScrollArea, QFrame)
from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtGui import QPainter, QColor, QPen, QFont

from .model import Grid
from .view import GridView

try:
    from generate_grid import generate_grid
except ImportError:
    import sys
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from generate_grid import generate_grid

# Dynamic calculation of absolute paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROGRESS_FILE = os.path.join(BASE_DIR, "data", "progress.json")
GRIDS_DIR = os.path.join(BASE_DIR, "data", "grids")


def load_progress() -> list[str]:
    """Loads the list of unlocked grids from the save file."""
    if os.path.exists(PROGRESS_FILE):
        try:
            with open(PROGRESS_FILE, "r") as f:
                return json.load(f).get("unlocked", ["default.json"])
        except Exception:
            pass
    return ["default.json"]


def save_progress(unlocked: list[str]) -> None:
    """Saves the list of unlocked grids to the progress file."""
    os.makedirs(os.path.dirname(PROGRESS_FILE), exist_ok=True)
    with open(PROGRESS_FILE, "w") as f:
        json.dump({"unlocked": unlocked}, f)


def natural_sort_key(s: str) -> list:
    """Sort key to rank 'grid2' before 'grid10'."""
    return [int(text) if text.isdigit() else text.lower()
            for text in re.split('([0-9]+)', s)]


def unlock_next_grid(current_file_path: str) -> None:
    """Unlocks the next campaign grid in order."""
    unlocked = load_progress()
    current_name = os.path.basename(current_file_path)
    
    if not os.path.exists(GRIDS_DIR):
        return

    # Retrieve grids, excluding generated ones
    files = [os.path.basename(f) for f in glob(os.path.join(GRIDS_DIR, "*.json"))]
    files = [f for f in files if not f.startswith("grid_gen_")]
    files.sort(key=natural_sort_key)
    
    if "default.json" in files:
        files.remove("default.json")
        files.insert(0, "default.json")
        
    try:
        idx = files.index(current_name)
        if idx + 1 < len(files):
            next_grid = files[idx + 1]
            if next_grid not in unlocked:
                unlocked.append(next_grid)
                save_progress(unlocked)
    except ValueError:
        pass


class PreviewGridView(GridView):
    """Adaptive preview component. Draws the grid structure without text."""
    
    def __init__(self, is_unlocked: bool, parent=None):
        super().__init__(parent)
        self.is_unlocked = is_unlocked

    def paintEvent(self, event) -> None:
        """Total override of drawing to force centering, size, and remove text."""
        painter: QPainter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Drawing area background
        bg_color = Qt.GlobalColor.white if self.is_unlocked else QColor(245, 245, 245)
        painter.fillRect(self.rect(), bg_color)

        if self.rows == 0 or self.cols == 0:
            return

        # 1. Increased margin to prevent drawing from touching or overflowing the card
        margin = 16
        avail_w = self.width() - (margin * 2)
        avail_h = self.height() - (margin * 2)

        # Cell size (take the smallest so everything fits)
        cs = max(1, min(avail_w // self.cols, avail_h // self.rows))
        
        # Total size of the drawn grid
        grid_w = cs * self.cols
        grid_h = cs * self.rows

        # 2. Perfect centering (local offsets, ignores parent class ones)
        ox = (self.width() - grid_w) // 2
        oy = (self.height() - grid_h) // 2

        # 3. Color choice (Playable Mode vs Locked Mode)
        grid_line_color = QColor(200, 200, 200) if self.is_unlocked else QColor(220, 220, 220)
        thick_line_color = Qt.GlobalColor.black if self.is_unlocked else QColor(160, 160, 160)
        immuable_bg_color = QColor(210, 210, 210) if self.is_unlocked else QColor(235, 235, 235)

        # 4. Drawing background cells and thin borders
        thin_pen = QPen(grid_line_color, 1)
        for i in range(self.rows):
            for j in range(self.cols):
                x: int = j * cs + ox
                y: int = i * cs + oy

                if (i, j) in self.immutable_cells:
                    painter.fillRect(x, y, cs, cs, immuable_bg_color)

                painter.setPen(thin_pen)
                painter.drawRect(x, y, cs, cs)

        # 5. Drawing thick pattern borders
        thick_pen = QPen(thick_line_color, max(2, int(cs * 0.1)))
        thick_pen.setCapStyle(Qt.PenCapStyle.SquareCap) # Cleaner joints
        painter.setPen(thick_pen)

        for border in self.thick_borders:
            x1: int = border[0] * cs + ox
            y1: int = border[1] * cs + oy
            x2: int = border[2] * cs + ox
            y2: int = border[3] * cs + oy
            painter.drawLine(x1, y1, x2, y2)


class LevelCard(QFrame):
    """Clickable card displaying a dynamic grid preview."""
    clicked = pyqtSignal(str)

    def __init__(self, file_path: str, is_unlocked: bool, parent=None):
        super().__init__(parent)
        self.file_path = file_path
        self.is_unlocked = is_unlocked
        
        self.setFixedSize(160, 210) 
        
        if is_unlocked:
            self.setStyleSheet("QFrame { border: 1px solid #ccc; border-radius: 8px; background-color: #fff; }")
            self.setCursor(Qt.CursorShape.PointingHandCursor)
        else:
            self.setStyleSheet("QFrame { border: 1px solid #eee; border-radius: 8px; background-color: #fbfbfb; }")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(4)
        
        self.preview = PreviewGridView(is_unlocked, self)
        self._setup_preview()
        layout.addWidget(self.preview)
        
        name = os.path.basename(file_path).replace(".json", "")
        lbl = QLabel(name)
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl.setFixedHeight(20) 
        if is_unlocked:
            lbl.setStyleSheet("border: none; font-weight: bold; color: black; font-size: 12px;")
        else:
            lbl.setStyleSheet("border: none; font-weight: bold; color: #bbb; font-size: 12px;")
        layout.addWidget(lbl)
            
    def _setup_preview(self) -> None:
        """Extracts and configures model data for thumbnail display."""
        try:
            grid = Grid.from_json(self.file_path)
            values = {}
            thick_borders = []
            immutable_cells = set()
            pattern_membership = {}
            
            # This is where the Width/Height inversion caused reading bugs!
            cols, rows = grid.get_dimensions()
            
            for pattern in grid.patterns:
                for cell in pattern.cells:
                    pattern_membership[(cell.y, cell.x)] = pattern.name
                    if cell.value > 0:
                        values[(cell.y, cell.x)] = cell.value
                        immutable_cells.add((cell.y, cell.x))

            for r in range(rows):
                for c in range(cols):
                    cur_pat = pattern_membership.get((r, c))
                    if r == 0 or pattern_membership.get((r-1, c)) != cur_pat:
                        thick_borders.append((c, r, c+1, r))
                    if r == rows - 1 or pattern_membership.get((r+1, c)) != cur_pat:
                        thick_borders.append((c, r+1, c+1, r+1))
                    if c == 0 or pattern_membership.get((r, c-1)) != cur_pat:
                        thick_borders.append((c, r, c, r+1))
                    if c == cols - 1 or pattern_membership.get((r, c+1)) != cur_pat:
                        thick_borders.append((c+1, r, c+1, r+1))

            self.preview.set_data(rows, cols, values, thick_borders, immutable_cells, pattern_membership)
            self.preview.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        except Exception as e:
            print(f"Erreur lors du chargement de la miniature pour {self.file_path}: {e}")

    def mousePressEvent(self, event) -> None:
        """Triggers the opening signal if the grid is accessible."""
        if self.is_unlocked:
            self.clicked.emit(self.file_path)


class GenerateCard(QFrame):
    """Special card-shaped button to instantly generate an 8x8 grid."""
    clicked = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(160, 210) 
        self.setStyleSheet("QFrame { border: 2px dashed #bbb; border-radius: 8px; background-color: #fafafa; }")
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        
        layout = QVBoxLayout(self)
        lbl = QLabel("+ Générer\n8x8")
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl.setStyleSheet("border: none; font-size: 16px; font-weight: bold; color: #444;")
        layout.addWidget(lbl)

    def mousePressEvent(self, event) -> None:
        """Triggers the generation action on click."""
        self.clicked.emit()


class StartupWindow(QWidget):
    """Main white window listing levels and the generation action."""
    start_game_signal = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Neonaure - Sélection du niveau")
        self.resize(850, 600)
        self.setStyleSheet("QWidget { background-color: white; color: black; }")
        
        main_layout = QVBoxLayout(self)
        
        title = QLabel("NEONAURE")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setFont(QFont("Arial", 40, QFont.Weight.Bold))
        title.setStyleSheet("color: black; font-weight: bold;")
        title.setContentsMargins(0, 20, 0, 30)
        main_layout.addWidget(title)
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet("QScrollArea { border: none; background-color: white; }")
        
        container = QWidget()
        container.setStyleSheet("background-color: white;")
        
        self.grid_layout = QGridLayout(container)
        self.grid_layout.setSpacing(15)
        self.grid_layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter)
        
        scroll.setWidget(container)
        main_layout.addWidget(scroll)
        
        self._load_levels()

    def _load_levels(self) -> None:
        """Instantiates and sorts valid level cards (excluding generated ones) for selection."""
        unlocked = load_progress()
        
        gen_card = GenerateCard()
        gen_card.clicked.connect(self._generate_and_play)
        self.grid_layout.addWidget(gen_card, 0, 0)
        
        if not os.path.exists(GRIDS_DIR):
            print(f"Dossier introuvable : {GRIDS_DIR}")
            return

        # Retrieve all .json files in the folder, excluding those starting with "grid_gen_"
        files = glob(os.path.join(GRIDS_DIR, "*.json"))
        files = [os.path.normpath(f) for f in files if not os.path.basename(f).startswith("grid_gen_")]
        
        # Natural sort: grid2 before grid10
        files.sort(key=lambda x: natural_sort_key(os.path.basename(x)))
        
        default_path = os.path.normpath(os.path.join(GRIDS_DIR, "default.json"))
        if default_path in files:
            files.remove(default_path)
            files.insert(0, default_path)
            
        col, row = 1, 0
        for file_path in files:
            filename = os.path.basename(file_path)
            is_unlocked = (filename == "default.json") or (filename in unlocked)
            
            card = LevelCard(file_path, is_unlocked)
            card.clicked.connect(self._on_level_selected)
                
            self.grid_layout.addWidget(card, row, col)
            col += 1
            if col > 3:  
                col = 0
                row += 1

    def _on_level_selected(self, file_path: str) -> None:
        """Transmits the selected file to the main game and cleanly closes the home screen."""
        self.start_game_signal.emit(file_path)
        self.close()

    def _generate_and_play(self) -> None:
        """Generates a random 8x8 configuration, saves it, and launches the game immediately."""
        data = generate_grid(8, 8)
        os.makedirs(GRIDS_DIR, exist_ok=True)
        
        i = 1
        while os.path.exists(os.path.join(GRIDS_DIR, f"grid_gen_{i}.json")):
            i += 1
            
        new_path = os.path.join(GRIDS_DIR, f"grid_gen_{i}.json")
        with open(new_path, "w") as f:
            json.dump(data, f, indent=2)
            
        self.start_game_signal.emit(new_path)
        self.close()