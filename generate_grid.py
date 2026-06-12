"""
Générateur de grilles aléatoires pour Neonaure.

Usage:
    python generate_grid.py                  # grille 8x8 par défaut
    python generate_grid.py --size 6         # grille 6x6
    python generate_grid.py --output ma_grille.json
"""

from __future__ import annotations

import json
import random
import argparse
from pathlib import Path

from neonaure.model import Grid, Solver

# Ratio d'indices laissés visibles
DEFAULT_CLUE_RATIO: float = 0.35


# Découpe la grille en régions connexes compactes
def generate_regions(width: int, height: int) -> dict[str, list[list[int]]]:
    """
    Découpe une grille en régions connexes compactes de taille ~5.

    Le découpage se fait en blocs réguliers horizontaux, ce qui garantit
    des régions solvables par le backtracking du Solver.
    Les ids de région sont mélangés pour varier l'ordre des motifs.
    """
    owner: list[list[int]] = [[-1] * width for _ in range(height)]
    regions: list[list[tuple[int, int]]] = []
    rid: int = 0

    y: int = 0
    while y < height:
        x: int = 0
        while x < width:
            if owner[y][x] != -1:
                x += 1
                continue

            reg: list[tuple[int, int]] = []
            cx: int = x
            while cx < width and owner[y][cx] == -1 and len(reg) < 5:
                owner[y][cx] = rid
                reg.append((cx, y))
                cx += 1

            if len(reg) < 5 and y + 1 < height:
                cx2: int = x
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


# Résout la grille puis masque une partie des valeurs
def solve_and_strip(
    data: dict[str, list[list[int]]],
    clue_ratio: float = DEFAULT_CLUE_RATIO,
) -> dict[str, list[list[int]]]:
    """
    Résout la grille complète puis masque des valeurs.

    Le Solver remplit tout, puis on ne garde qu'une fraction des valeurs
    comme indices. Le reste repasse à 0 (= à compléter par le joueur).
    """
    grid: Grid = Grid.from_data(data)
    solver: Solver = Solver(grid)

    if not solver.solve():
        raise RuntimeError("Grille insoluble")

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


# Pipeline complet : découpe -> résout -> masque
def generate_grid(
    width: int = 8,
    height: int = 8,
    clue_ratio: float = DEFAULT_CLUE_RATIO,
) -> dict[str, list[list[int]]]:
    """Pipeline complet : découpe -> résout -> masque."""
    data: dict[str, list[list[int]]] = generate_regions(width, height)
    return solve_and_strip(data, clue_ratio)


# Point d'entrée CLI
def main() -> None:
    parser: argparse.ArgumentParser = argparse.ArgumentParser(
        description="Générateur de grilles Neonaure"
    )
    parser.add_argument("--size", type=int, default=8, help="Taille de la grille (carrée)")
    parser.add_argument("--width", type=int, default=None, help="Largeur (override --size)")
    parser.add_argument("--height", type=int, default=None, help="Hauteur (override --size)")
    parser.add_argument("--output", type=str, default=None, help="Nom du fichier de sortie")
    parser.add_argument("--clues", type=float, default=DEFAULT_CLUE_RATIO, help="Ratio d'indices (0-1)")
    args = parser.parse_args()

    w: int = args.width or args.size
    h: int = args.height or args.size

    print(f"Génération d'une grille {w}×{h}...")
    result: dict[str, list[list[int]]] = generate_grid(w, h, args.clues)

    # On compte le nombre total de cellules et d'indices
    total = 0
    clues = 0
    for cells in result.values():
        total += len(cells)
        for c in cells:
            if c[2] != 0:
                clues += 1
    print(f"Cellules: {total}, Indices: {clues}")

    output_dir: Path = Path("data/grids")
    output_dir.mkdir(parents=True, exist_ok=True)

    if args.output:
        filepath: Path = output_dir / args.output
    else:
        existing: list[Path] = list(output_dir.glob("grid*.json"))
        max_id: int = max(
            (int(f.stem.replace("grid", "")) for f in existing if f.stem.replace("grid", "").isdigit()),
            default=0,
        )
        filepath = output_dir / f"grid{max_id + 1}.json"

    with open(filepath, "w") as f:
        json.dump(result, f, indent=2)

    print(f"Grille sauvegardée : {filepath}")


if __name__ == "__main__":
    main()
