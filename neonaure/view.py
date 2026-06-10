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
from PyQt6.QtCore import Qt, QRect

class VueGrille(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.lignes = 0
        self.colonnes = 0
        self.taille_case = 50
        self.valeurs = {}
        self.bords_epais = []

    def set_donnees(self, lignes, colonnes, valeurs, bords_epais):
        self.lignes = lignes
        self.colonnes = colonnes
        self.valeurs = valeurs
        self.bords_epais = bords_epais
        self.setMinimumSize(self.colonnes * self.taille_case + 20, self.lignes * self.taille_case + 20)
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        painter.fillRect(self.rect(), Qt.GlobalColor.white)

        stylo_fin = QPen(QColor(200, 200, 200), 1)
        painter.setPen(stylo_fin)

        for i in range(self.lignes):
            for j in range(self.colonnes):
                x = j * self.taille_case + 10
                y = i * self.taille_case + 10
                painter.drawRect(x, y, self.taille_case, self.taille_case)

        painter.setPen(QPen(Qt.GlobalColor.black))
        font = QFont("Arial", 16)
        painter.setFont(font)

        for (i, j), valeur in self.valeurs.items():
            x = j * self.taille_case + 10
            y = i * self.taille_case + 10
            rect = QRect(x, y, self.taille_case, self.taille_case)
            painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, str(valeur))

        stylo_epais = QPen(Qt.GlobalColor.black, 4)
        painter.setPen(stylo_epais)

        for bord in self.bords_epais:
            x1 = bord[0] * self.taille_case + 10
            y1 = bord[1] * self.taille_case + 10
            x2 = bord[2] * self.taille_case + 10
            y2 = bord[3] * self.taille_case + 10
            painter.drawLine(x1, y1, x2, y2)


data_test = {
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


def preparer_donnees_test(data):
    valeurs = {}
    bords_epais = []
    lignes = 8
    colonnes = 8
    
    appartenance_motif = {}
    for nom_motif, cellules in data.items():
        for l, c, v in cellules:
            appartenance_motif[(l, c)] = nom_motif
            if v > 0:
                valeurs[(l, c)] = v
                
    for l in range(lignes):
        for c in range(colonnes):
            motif_courant = appartenance_motif.get((l, c))
            
            if l == 0 or appartenance_motif.get((l-1, c)) != motif_courant:
                bords_epais.append((c, l, c+1, l))
            if l == lignes - 1 or appartenance_motif.get((l+1, c)) != motif_courant:
                bords_epais.append((c, l+1, c+1, l+1))
            if c == 0 or appartenance_motif.get((l, c-1)) != motif_courant:
                bords_epais.append((c, l, c, l+1))
            if c == colonnes - 1 or appartenance_motif.get((l, c+1)) != motif_courant:
                bords_epais.append((c+1, l, c+1, l+1))
                
    return lignes, colonnes, valeurs, bords_epais


class FenetreTest(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Test Vue Néonaure")
        self.vue = VueGrille(self)
        self.setCentralWidget(self.vue)
        
        l, c, val, bords = preparer_donnees_test(data_test)
        self.vue.set_donnees(l, c, val, bords)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyleSheet("QWidget { background-color: white; color: black; }")
    fenetre = FenetreTest()
    fenetre.show()
    sys.exit(app.exec())