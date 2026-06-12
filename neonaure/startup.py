"""
Neonaure - Startup Module

Handles the game's startup screen, campaign grid detection,
clean preview (without text), visual locking, and progression.
"""

import os
import json
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

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROGRESS_FILE = os.path.join(BASE_DIR, "data", "progress.txt")
GRIDS_DIR = os.path.join(BASE_DIR, "data", "grids")


def extraire_numero(nom):
    """Extrait le numero d'un nom de fichier pour le tri."""
    numero = nom.replace("grid", "").replace(".json", "")
    if numero.isdigit():
        return int(numero)
    return 0


def load_progress():
    """Charge la liste des grilles debloquees."""
    try:
        with open(PROGRESS_FILE, "r") as f:
            lignes = f.readlines()
            resultat = []
            for l in lignes:
                resultat.append(l.strip())
            return resultat
    except:
        return ["default.json"]


def save_progress(unlocked):
    """Sauvegarde la liste des grilles debloquees."""
    os.makedirs(os.path.dirname(PROGRESS_FILE), exist_ok=True)
    with open(PROGRESS_FILE, "w") as f:
        for nom in unlocked:
            f.write(nom + "\n")


def unlock_next_grid(current_file_path):
    """Debloque la prochaine grille de la campagne."""
    unlocked = load_progress()
    current_name = os.path.basename(current_file_path)

    if not os.path.exists(GRIDS_DIR):
        return

    files = [os.path.basename(f) for f in glob(os.path.join(GRIDS_DIR, "*.json"))]
    files = [f for f in files if not f.startswith("grid_gen_")]
    files.sort(key=extraire_numero)

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
    """Apercu adapte. Dessine la grille sans texte."""

    def __init__(self, is_unlocked, parent=None):
        super().__init__(parent)
        self.is_unlocked = is_unlocked

    def paintEvent(self, event):
        """Dessin complet avec centrage et sans texte."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        bg_color = Qt.GlobalColor.white if self.is_unlocked else QColor(245, 245, 245)
        painter.fillRect(self.rect(), bg_color)

        if self.rows == 0 or self.cols == 0:
            return

        margin = 16
        avail_w = self.width() - (margin * 2)
        avail_h = self.height() - (margin * 2)

        cs = max(1, min(avail_w // self.cols, avail_h // self.rows))

        grid_w = cs * self.cols
        grid_h = cs * self.rows

        ox = (self.width() - grid_w) // 2
        oy = (self.height() - grid_h) // 2

        grid_line_color = QColor(200, 200, 200) if self.is_unlocked else QColor(220, 220, 220)
        thick_line_color = Qt.GlobalColor.black if self.is_unlocked else QColor(160, 160, 160)
        immuable_bg_color = QColor(210, 210, 210) if self.is_unlocked else QColor(235, 235, 235)

        thin_pen = QPen(grid_line_color, 1)
        for i in range(self.rows):
            for j in range(self.cols):
                x = j * cs + ox
                y = i * cs + oy

                if (i, j) in self.immutable_cells:
                    painter.fillRect(x, y, cs, cs, immuable_bg_color)

                painter.setPen(thin_pen)
                painter.drawRect(x, y, cs, cs)

        thick_pen = QPen(thick_line_color, max(2, int(cs * 0.1)))
        thick_pen.setCapStyle(Qt.PenCapStyle.SquareCap)
        painter.setPen(thick_pen)

        for border in self.thick_borders:
            x1 = border[0] * cs + ox
            y1 = border[1] * cs + oy
            x2 = border[2] * cs + ox
            y2 = border[3] * cs + oy
            painter.drawLine(x1, y1, x2, y2)


class LevelCard(QFrame):
    """Carte cliquable avec apercu dynamique d'une grille."""
    clicked = pyqtSignal(str)

    def __init__(self, file_path, is_unlocked, parent=None):
        super().__init__(parent)
        self.file_path = file_path
        self.is_unlocked = is_unlocked

        self.setFixedSize(160, 210)

        if is_unlocked:
            self.setStyleSheet("QFrame { border: 1px solid gray; background-color: white; }")
            self.setCursor(Qt.CursorShape.PointingHandCursor)
        else:
            self.setStyleSheet("QFrame { border: 1px solid lightgray; background-color: #f5f5f5; }")

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
            lbl.setStyleSheet("font-weight: bold; color: black; font-size: 12px;")
        else:
            lbl.setStyleSheet("font-weight: bold; color: #bbb; font-size: 12px;")
        layout.addWidget(lbl)

    def _setup_preview(self):
        """Charge les donnees du modele pour la miniature."""
        try:
            grid = Grid.from_json(self.file_path)
            values = {}
            thick_borders = []
            immutable_cells = set()
            pattern_membership = {}

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

    def mousePressEvent(self, event):
        """Declenche le signal si la grille est debloquee."""
        if self.is_unlocked:
            self.clicked.emit(self.file_path)


class GenerateCard(QFrame):
    """Carte speciale pour generer une grille aleatoire 8x8."""
    clicked = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(160, 210)
        self.setStyleSheet("QFrame { border: 2px dashed gray; background-color: #f5f5f5; }")
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        layout = QVBoxLayout(self)
        lbl = QLabel("+ Generer\n8x8")
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl.setStyleSheet("font-size: 16px; font-weight: bold; color: #444;")
        layout.addWidget(lbl)

    def mousePressEvent(self, event):
        """Declenche la generation au clic."""
        self.clicked.emit()


class StartupWindow(QWidget):
    """Fenetre principale listant les niveaux et la generation."""
    start_game_signal = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Neonaure - Selection du niveau")
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

    def _load_levels(self):
        """Charge et trie les cartes de niveaux."""
        unlocked = load_progress()

        gen_card = GenerateCard()
        gen_card.clicked.connect(self._generate_and_play)
        self.grid_layout.addWidget(gen_card, 0, 0)

        if not os.path.exists(GRIDS_DIR):
            print(f"Dossier introuvable : {GRIDS_DIR}")
            return

        files = glob(os.path.join(GRIDS_DIR, "*.json"))
        files = [os.path.normpath(f) for f in files if not os.path.basename(f).startswith("grid_gen_")]

        files.sort(key=lambda x: extraire_numero(os.path.basename(x)))

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

    def _on_level_selected(self, file_path):
        """Transmet le fichier selectionne et ferme l'ecran d'accueil."""
        self.start_game_signal.emit(file_path)
        self.close()

    def _generate_and_play(self):
        """Genere une grille 8x8 aleatoire et lance la partie."""
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
