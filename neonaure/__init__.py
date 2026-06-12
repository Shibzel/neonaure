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
from .startup import StartupWindow

# Chemin par defaut de la grille
DEFAULT_GRID = "./data/grids/default.json"


# Lance le jeu (startup screen puis fenetre principale)
# Quand le joueur gagne et clique "Retour au menu", on reboucle
def run(file=DEFAULT_GRID):
    """
    Runs the game. Loops between startup screen and game window.
    When the player wins and clicks "Retour au menu", goes back to startup.
    """
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)

    while True:
        selected = [None]

        # Callback interne pour recuperer la grille selectionnee
        def on_game_start(path):
            selected[0] = path

        # 1. Show the startup screen
        app.setStyleSheet("QWidget { background-color: #1E1E1E; color: white; }")
        startup = StartupWindow()
        startup.start_game_signal.connect(on_game_start)
        startup.show()
        app.exec()

        # 2. If a file was selected, launch the game
        if not selected[0]:
            break

        app.setStyleSheet("QWidget { background-color: white; color: black; }")

        try:
            controller = Controller(selected[0])
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
