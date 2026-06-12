"""
Neonaure

Authors :
    - Jean-Francois L. (contact@shibzel.me)
    - Adrien R.
    - Florian S.

Description :
    Module package for every function and objects that allows the game to run.
    Also contains a generic `run()` function that runs the game.
    See README.md for information about the project itself.
"""

from __future__ import annotations

# Version du package
__version__: str = "0.1"

import sys
from PyQt6.QtWidgets import QApplication

from .controller import Controller
from .model import Cell, CellIsImmuable, Grid, Pattern, PatternAlreadyLoaded, Solver
from .view import GridView, MainWindow, NumberSelector
from .startup import StartupWindow

# Chemin par défaut de la grille
DEFAULT_GRID: str = "./data/grids/default.json"


# Lance le jeu (startup screen puis fenêtre principale)
def run(file: str = DEFAULT_GRID) -> None:
    """
    Runs the game. Starts the startup screen, waits for a grid selection,
    then launches the main game window.
    """
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)

    selected_file = None

    # Callback interne pour récupérer la grille sélectionnée
    def on_game_start(path: str):
        nonlocal selected_file
        selected_file = path

    """1. Show the startup screen"""
    app.setStyleSheet("QWidget { background-color: #1E1E1E; color: white; }")
    startup = StartupWindow()
    startup.start_game_signal.connect(on_game_start)
    startup.show()
    app.exec()

    """2. If a file was selected, launch the game"""
    if selected_file:
        """Set the style for the main game window"""
        app.setStyleSheet("QWidget { background-color: white; color: black; }")
        
        try:
            controller = Controller(selected_file)
            controller.view.show()
            sys.exit(app.exec())
        except Exception as e:
            print(f"Error loading the grid: {e}")
