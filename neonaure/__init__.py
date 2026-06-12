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

__version__ = "0.1"

import sys
from PyQt6.QtWidgets import QApplication

from .controller import Controller
from .model import Cell, CellIsImmuable, Grid, Pattern, PatternAlreadyLoaded, Solver
from .view import GridView, MainWindow, NumberSelector
from .startup import StartupWindow

# Chemin par défaut de la grille
DEFAULT_GRID: str = "./data/grids/default.json"


# Lance le jeu (startup screen puis fenêtre principale)
# Quand le joueur gagne et clique "Retour au menu", on reboucle
def run(file: str = DEFAULT_GRID) -> None:
    """
    Runs the game. Loops between startup screen and game window.
    When the player wins and clicks "Retour au menu", goes back to startup.
    """
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)

    while True:
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
        if not selected_file:
            break

        app.setStyleSheet("QWidget { background-color: white; color: black; }")

        try:
            controller = Controller(selected_file)
            controller.view.show()
            app.exec()

            # Si le joueur veut revenir au menu, on reboucle
            if controller._return_to_menu:
                continue
            else:
                break
        except Exception as e:
            print(f"Error loading the grid: {e}")
            break
