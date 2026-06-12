"""
Neonaure - Startup Module

Gère l'écran de démarrage du jeu, la sélection des grilles, 
la prévisualisation et le suivi de la progression.
"""

import os
import json
from glob import glob
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QLabel, QGridLayout, 
                             QScrollArea, QFrame, QGraphicsOpacityEffect)
from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtGui import QFont

from .model import Grid
from .view import GridView

try:
    from generate_grid import generate_grid
except ImportError:
    import sys
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from generate_grid import generate_grid

PROGRESS_FILE = "./data/progress.json"
GRIDS_DIR = "./data/grids"


def load_progress() -> list[str]:
    """Charge la liste des grilles débloquées depuis le fichier de sauvegarde."""
    if os.path.exists(PROGRESS_FILE):
        with open(PROGRESS_FILE, "r") as f:
            return json.load(f).get("unlocked", ["default.json"])
    return ["default.json"]


def save_progress(unlocked: list[str]) -> None:
    """Sauvegarde la liste des grilles débloquées dans le fichier de progression."""
    os.makedirs(os.path.dirname(PROGRESS_FILE), exist_ok=True)
    with open(PROGRESS_FILE, "w") as f:
        json.dump({"unlocked": unlocked}, f)


def unlock_next_grid(current_file_path: str) -> None:
    """Débloque la grille suivante dans l'ordre alphabétique."""
    unlocked = load_progress()
    current_name = os.path.basename(current_file_path)
    
    files = [os.path.basename(f) for f in glob(os.path.join(GRIDS_DIR, "*.json"))]
    files.sort()
    
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


class LevelCard(QFrame):
    """Carte cliquable affichant une prévisualisation de grille de niveau."""
    clicked = pyqtSignal(str)

    def __init__(self, file_path: str, is_unlocked: bool, parent=None):
        super().__init__(parent)
        self.file_path = file_path
        self.is_unlocked = is_unlocked
        self.setFixedSize(160, 180)
        self.setStyleSheet("QFrame { border: 1px solid #ccc; border-radius: 8px; background-color: #fff; }")

        layout = QVBoxLayout(self)
        
        self.preview = GridView(self)
        self._setup_preview()
        layout.addWidget(self.preview, stretch=1)
        
        name = os.path.basename(file_path).replace(".json", "")
        lbl = QLabel(name)
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl.setStyleSheet("border: none; font-weight: bold; color: black;")
        layout.addWidget(lbl)

        if not is_unlocked:
            effect = QGraphicsOpacityEffect(self)
            effect.setOpacity(0.2)
            self.setGraphicsEffect(effect)
            
    def _setup_preview(self) -> None:
        """Charge la grille et prépare les données pour l'affichage miniature."""
        grid = Grid.from_json(self.file_path)
        values = {}
        thick_borders = []
        immutable_cells = set()
        pattern_membership = {}
        
        rows, cols = grid.get_dimensions()
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

    def mousePressEvent(self, event) -> None:
        """Emet le signal de clic uniquement si le niveau est débloqué."""
        if self.is_unlocked:
            self.clicked.emit(self.file_path)


class GenerateCard(QFrame):
    """Carte spéciale générant une nouvelle grille 8x8 au clic."""
    clicked = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(160, 180)
        self.setStyleSheet("QFrame { border: 2px dashed #888; border-radius: 8px; background-color: #f9f9f9; }")
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        layout = QVBoxLayout(self)
        lbl = QLabel("+ Générer 8x8")
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl.setStyleSheet("border: none; font-size: 16px; font-weight: bold; color: black;")
        layout.addWidget(lbl)

    def mousePressEvent(self, event) -> None:
        """Déclenche l'événement de génération."""
        self.clicked.emit()


class StartupWindow(QWidget):
    """Fenêtre principale de démarrage affichant le menu des niveaux."""
    start_game_signal = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Neonaure - Niveaux")
        self.resize(850, 600)
        self.setStyleSheet("QWidget { background-color: white; color: black; }")
        
        main_layout = QVBoxLayout(self)
        
        title = QLabel("NEONAURE")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setFont(QFont("Arial", 40, QFont.Weight.Bold))
        title.setContentsMargins(0, 20, 0, 30)
        main_layout.addWidget(title)
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; }")
        
        container = QWidget()
        self.grid_layout = QGridLayout(container)
        self.grid_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        scroll.setWidget(container)
        main_layout.addWidget(scroll)
        
        self._load_levels()

    def _load_levels(self) -> None:
        """Instancie et place toutes les cartes de niveaux dans la grille."""
        unlocked = load_progress()
        
        gen_card = GenerateCard()
        gen_card.clicked.connect(self._generate_and_play)
        self.grid_layout.addWidget(gen_card, 0, 0)
        
        files = glob(os.path.join(GRIDS_DIR, "*.json"))
        files.sort()
        
        default_path = os.path.join(GRIDS_DIR, "default.json")
        if default_path in files:
            files.remove(default_path)
            files.insert(0, default_path)
            
        col, row = 1, 0
        for file_path in files:
            filename = os.path.basename(file_path)
            is_unlocked = filename in unlocked
            
            card = LevelCard(file_path, is_unlocked)
            card.clicked.connect(self.start_game_signal.emit)
            if is_unlocked:
                card.setCursor(Qt.CursorShape.PointingHandCursor)
                
            self.grid_layout.addWidget(card, row, col)
            col += 1
            if col > 4:
                col = 0
                row += 1

    def _generate_and_play(self) -> None:
        """Génère une carte, la sauvegarde de manière incrémentale et la lance."""
        data = generate_grid(8, 8)
        os.makedirs(GRIDS_DIR, exist_ok=True)
        
        i = 1
        while os.path.exists(os.path.join(GRIDS_DIR, f"grid_gen_{i}.json")):
            i += 1
            
        new_path = os.path.join(GRIDS_DIR, f"grid_gen_{i}.json")
        with open(new_path, "w") as f:
            json.dump(data, f, indent=2)
            
        unlocked = load_progress()
        unlocked.append(f"grid_gen_{i}.json")
        save_progress(unlocked)
        
        self.start_game_signal.emit(new_path)