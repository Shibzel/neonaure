"""
Generateur de grilles aleatoires pour Neonaure.

Usage:
    python generate_grid.py                  # grille 8x8 par defaut
    python generate_grid.py 6                # grille 6x6
"""

import json
import random
import os
import sys

from neonaure.model import Grid, Solver

# Ratio d'indices laisses visibles
DEFAULT_CLUE_RATIO = 0.35


# Decoupe la grille en regions connexes compactes
def generate_regions(width: int, height: int) -> dict[str, list[list[int]]]:
    """
    Decoupe une grille en regions connexes compactes de taille ~5.

    Le decoupage se fait en blocs reguliers horizontaux, ce qui garantit
    des regions solvables par le backtracking du Solver.
    Les ids de region sont melanges pour varier l'ordre des motifs.
    """
    owner = [[-1] * width for _ in range(height)]
    regions = []
    rid = 0

    y = 0
    while y < height:
        x = 0
        while x < width:
            if owner[y][x] != -1:
                x += 1
                continue

            reg = []
            cx = x
            while cx < width and owner[y][cx] == -1 and len(reg) < 5:
                owner[y][cx] = rid
                reg.append((cx, y))
                cx += 1

            if len(reg) < 5 and y + 1 < height:
                cx2 = x
                while cx2 < width and owner[y + 1][cx2] == -1 and len(reg) < 5:
                    owner[y + 1][cx2] = rid
                    reg.append((cx2, y + 1))
                    cx2 += 1

            regions.append(reg)
            rid += 1
            x = cx
        y += 1

    random.shuffle(regions)

    # On construit le dictionnaire final avec les noms de motifs
    data = {}
    for i in range(len(regions)):
        cells = regions[i]
        cell_data = []
        for x, y in cells:
            cell_data.append([x, y, 0])
        data["motif" + str(i + 1)] = cell_data

    return data


# Resout la grille puis masque une partie des valeurs
def solve_and_strip(
    data: dict[str, list[list[int]]],
    clue_ratio: float = DEFAULT_CLUE_RATIO,
) -> dict[str, list[list[int]]]:
    """
    Resout la grille completement puis masque des valeurs.

    Le Solver remplit tout, puis on ne garde qu'une fraction des valeurs
    comme indices. Le reste repasse a 0 (= a completer par le joueur).
    """
    grid = Grid.from_data(data)
    solver = Solver(grid)

    if not solver.solve():
        print("Erreur : la grille est insoluble")
        return {}

    # On rassemble toutes les cellules avec leur motif, coordonnees et valeur
    all_cells = []
    for pattern in grid.patterns:
        for cell in pattern.cells:
            all_cells.append((pattern.name, cell.x, cell.y, cell.value))

    # On melange pour choisir les indices au hasard
    random.shuffle(all_cells)
    n_clues = max(1, int(len(all_cells) * clue_ratio))

    # On garde les coordonnees des indices (cellules qui resteront visibles)
    clues_set = set()
    for i in range(n_clues):
        _, x, y, _ = all_cells[i]
        clues_set.add((x, y))

    # On construit le resultat : les indices gardent leur valeur, le reste passe a 0
    result = {}
    for pattern in grid.patterns:
        cell_list = []
        for cell in pattern.cells:
            if (cell.x, cell.y) in clues_set:
                cell_list.append([cell.x, cell.y, cell.value])
            else:
                cell_list.append([cell.x, cell.y, 0])
        result[pattern.name] = cell_list

    return result


# Pipeline complet : decoupe -> resout -> masque
def generate_grid(
    width: int = 8,
    height: int = 8,
    clue_ratio: float = DEFAULT_CLUE_RATIO,
) -> dict[str, list[list[int]]]:
    """Pipeline complet : decoupe -> resout -> masque."""
    data = generate_regions(width, height)
    return solve_and_strip(data, clue_ratio)


# Point d'entree CLI
def main():
    taille = 8
    if len(sys.argv) > 1:
        taille = int(sys.argv[1])

    print("Generation d'une grille " + str(taille) + "x" + str(taille) + "...")
    data = generate_grid(taille, taille)

    # compter les cellules et les indices
    total = 0
    indices = 0
    for cells in data.values():
        total += len(cells)
        for c in cells:
            if c[2] != 0:
                indices += 1
    print("Cellules: " + str(total) + ", Indices: " + str(indices))

    os.makedirs("data/grids", exist_ok=True)
    with open("data/grids/grid_gen.json", "w") as f:
        json.dump(data, f, indent=2)
    print("Grille sauvegardee !")


if __name__ == "__main__":
    main()
