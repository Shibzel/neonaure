"""
Tests unitaires pour le modele Neonaure (Cell, Pattern, Grid, Solver).

On teste chaque classe independamment, puis on teste le chargement
des grilles JSON et la resolution par le solveur.
"""

import os
import pytest
from neonaure.model import Cell, Pattern, Grid, Solver, CellIsImmuable, PatternAlreadyLoaded


# ============================================================
# Tests pour la classe Cell
# ============================================================

class TestCell:

    def test_create_cell_default(self):
        """Une cellule creee sans valeur est a 0 et non immuable."""
        cell = Cell(3, 5)
        assert cell.x == 3
        assert cell.y == 5
        assert cell.value == 0
        assert cell.immuable == False

    def test_create_cell_with_value(self):
        """On peut creer une cellule avec une valeur et la rendre immuable."""
        cell = Cell(1, 2, value=5, immuable=True)
        assert cell.value == 5
        assert cell.immuable == True

    def test_set_value_normal(self):
        """On peut modifier la valeur d'une cellule non immuable."""
        cell = Cell(0, 0)
        cell.set_value(7)
        assert cell.value == 7

    def test_set_value_immuable_raises(self):
        """Modifier une cellule immuable leve une exception CellIsImmuable."""
        cell = Cell(0, 0, value=3, immuable=True)
        with pytest.raises(CellIsImmuable):
            cell.set_value(5)

    def test_set_value_to_zero(self):
        """On peut remettre une cellule a 0."""
        cell = Cell(0, 0, value=5)
        cell.set_value(0)
        assert cell.value == 0

    def test_eq_same_position(self):
        """Deux cellules a la meme position sont egales."""
        c1 = Cell(2, 3, value=5)
        c2 = Cell(2, 3, value=9)
        assert c1 == c2

    def test_eq_different_position(self):
        """Deux cellules a des positions differentes ne sont pas egales."""
        c1 = Cell(0, 0, value=5)
        c2 = Cell(1, 0, value=5)
        assert c1 != c2

    def test_eq_not_cell(self):
        """Comparer une Cell avec un autre type renvoie False."""
        cell = Cell(0, 0)
        assert cell != "pas une cellule"
        assert cell != 42
        assert cell != None

    def test_hash_same_position(self):
        """Deux cellules a la meme position ont le meme hash."""
        c1 = Cell(2, 3, value=1)
        c2 = Cell(2, 3, value=9)
        assert hash(c1) == hash(c2)

    def test_hash_different_position(self):
        """Deux cellules a des positions differentes ont des hash differents."""
        c1 = Cell(0, 0)
        c2 = Cell(1, 1)
        assert hash(c1) != hash(c2)

    def test_cell_in_set(self):
        """On peut utiliser des Cell dans un set (grace a __hash__)."""
        s = set()
        s.add(Cell(0, 0, value=5))
        s.add(Cell(0, 0, value=3))
        s.add(Cell(1, 1, value=5))
        # (0,0) est la meme position donc compte une seule fois
        assert len(s) == 2

    def test_cell_in_dict(self):
        """On peut utiliser des Cell comme cles de dict."""
        d = {}
        c = Cell(3, 4, value=7)
        d[c] = "info"
        assert d[c] == "info"

    def test_to_list(self):
        """to_list retourne [x, y, value, immuable]."""
        cell = Cell(2, 5, value=3, immuable=True)
        result = cell.to_list()
        assert result == [2, 5, 3, True]

    def test_to_list_default(self):
        """to_list d'une cellule par defaut."""
        cell = Cell(0, 0)
        assert cell.to_list() == [0, 0, 0, False]

    def test_str(self):
        """__str__ affiche les coordonnees et la valeur."""
        cell = Cell(1, 2, value=5)
        texte = str(cell)
        assert "1" in texte
        assert "2" in texte
        assert "5" in texte

    def test_repr(self):
        """__repr__ affiche toutes les infos de la cellule."""
        cell = Cell(3, 4, value=2, immuable=True)
        texte = repr(cell)
        assert "Cell" in texte
        assert "3" in texte
        assert "4" in texte


# ============================================================
# Tests pour la classe Pattern
# ============================================================

class TestPattern:

    def test_create_empty(self):
        """Un pattern cree sans cellules est vide."""
        p = Pattern("motif1")
        assert p.name == "motif1"
        assert p.size() == 0
        assert p.cells == []

    def test_create_with_cells(self):
        """On peut creer un pattern avec des cellules."""
        cells = [Cell(0, 0, 1), Cell(1, 0), Cell(0, 1)]
        p = Pattern("motif1", cells)
        assert p.size() == 3

    def test_size(self):
        """size() retourne le nombre de cellules."""
        p = Pattern("motif1", [Cell(0, 0), Cell(1, 0)])
        assert p.size() == 2

    def test_values_empty(self):
        """values() retourne une liste vide si toutes les valeurs sont 0."""
        p = Pattern("motif1", [Cell(0, 0), Cell(1, 0)])
        assert p.values() == []

    def test_values_with_numbers(self):
        """values() retourne les valeurs non-nulles."""
        p = Pattern("motif1", [
            Cell(0, 0, value=3),
            Cell(1, 0, value=0),
            Cell(2, 0, value=5),
        ])
        result = p.values()
        assert 3 in result
        assert 5 in result
        assert len(result) == 2

    def test_contains_value_true(self):
        """contains_value retourne True si la valeur est presente."""
        p = Pattern("motif1", [Cell(0, 0, value=3)])
        assert p.contains_value(3) == True

    def test_contains_value_false(self):
        """contains_value retourne False si la valeur n'est pas presente."""
        p = Pattern("motif1", [Cell(0, 0, value=3)])
        assert p.contains_value(5) == False

    def test_contains_value_zero(self):
        """contains_value avec 0 retourne True si une cellule est vide."""
        p = Pattern("motif1", [Cell(0, 0, value=0)])
        assert p.contains_value(0) == True

    def test_set_cell_new(self):
        """set_cell ajoute une cellule si elle n'existe pas."""
        p = Pattern("motif1")
        p.set_cell(0, 0, 5)
        assert p.size() == 1
        assert p.cells[0].value == 5

    def test_set_cell_update_existing(self):
        """set_cell met a jour une cellule existante."""
        p = Pattern("motif1", [Cell(0, 0, value=3)])
        p.set_cell(0, 0, 7)
        assert p.size() == 1
        assert p.cells[0].value == 7

    def test_set_cell_immuable(self):
        """set_cell cree une cellule immuable."""
        p = Pattern("motif1")
        p.set_cell(0, 0, 5, immuable=True)
        assert p.cells[0].immuable == True

    def test_from_raw_cells_3_elements(self):
        """from_raw_cells avec 3 elements : valeur != 0 -> immuable."""
        raw = [[0, 0, 5], [1, 0, 0]]
        p = Pattern.from_raw_cells("motif1", raw)
        assert p.size() == 2
        assert p.cells[0].value == 5
        assert p.cells[0].immuable == True
        assert p.cells[1].value == 0
        assert p.cells[1].immuable == False

    def test_from_raw_cells_4_elements(self):
        """from_raw_cells avec 4 elements : immuable = 4eme element."""
        raw = [[0, 0, 5, True], [1, 0, 3, False]]
        p = Pattern.from_raw_cells("motif1", raw)
        assert p.cells[0].immuable == True
        assert p.cells[1].immuable == False

    def test_to_list(self):
        """to_list serialise le motif."""
        p = Pattern("motif1", [Cell(0, 0, 5, True)])
        result = p.to_list()
        assert result == [[0, 0, 5, True]]

    def test_repr(self):
        """__repr__ affiche le nom et le nombre de cellules."""
        p = Pattern("motif1", [Cell(0, 0), Cell(1, 0)])
        texte = repr(p)
        assert "motif1" in texte
        assert "2" in texte


# ============================================================
# Tests pour la classe Grid
# ============================================================

# Grille simple 3x2 pour les tests :
# motif1 = (0,0) (1,0) (0,1)
# motif2 = (1,1) (2,0) (2,1)
def _make_test_grid_data():
    """Cree des donnees de grille 3x2 pour les tests."""
    return {
        "motif1": [[0, 0, 0], [1, 0, 0], [0, 1, 0]],
        "motif2": [[1, 1, 0], [2, 0, 0], [2, 1, 0]],
    }


class TestGrid:

    def test_create_grid(self):
        """Une grille se cree correctement a partir de donnees."""
        data = _make_test_grid_data()
        grid = Grid.from_data(data)
        assert grid.width == 3
        assert grid.height == 2

    def test_get_dimensions(self):
        """get_dimensions retourne (largeur, hauteur)."""
        data = _make_test_grid_data()
        grid = Grid.from_data(data)
        w, h = grid.get_dimensions()
        assert w == 3
        assert h == 2

    def test_get_cell_exists(self):
        """get_cell retourne la bonne cellule si elle existe."""
        data = _make_test_grid_data()
        grid = Grid.from_data(data)
        cell = grid.get_cell(1, 0)
        assert cell is not None
        assert cell.x == 1
        assert cell.y == 0

    def test_get_cell_out_of_bounds(self):
        """get_cell retourne None si les coordonnees sont hors limites."""
        data = _make_test_grid_data()
        grid = Grid.from_data(data)
        assert grid.get_cell(10, 10) is None
        assert grid.get_cell(-1, 0) is None

    def test_get_pattern_of(self):
        """get_pattern_of retourne le bon motif."""
        data = _make_test_grid_data()
        grid = Grid.from_data(data)
        pattern = grid.get_pattern_of(0, 0)
        assert pattern is not None
        assert pattern.name == "motif1"
        pattern2 = grid.get_pattern_of(2, 1)
        assert pattern2 is not None
        assert pattern2.name == "motif2"

    def test_get_pattern_of_invalid(self):
        """get_pattern_of retourne None pour des coordonnees invalides."""
        data = _make_test_grid_data()
        grid = Grid.from_data(data)
        assert grid.get_pattern_of(99, 99) is None

    def test_neighbours_center(self):
        """Au centre d'une grille 3x3, il y a 8 voisins."""
        # Grille 3x3 avec un seul motif
        data = {
            "motif1": [
                [0, 0, 0], [1, 0, 0], [2, 0, 0],
                [0, 1, 0], [1, 1, 0], [2, 1, 0],
                [0, 2, 0], [1, 2, 0], [2, 2, 0],
            ]
        }
        grid = Grid.from_data(data)
        neighbours = grid.neighbours(1, 1)
        assert len(neighbours) == 8

    def test_neighbours_corner(self):
        """Au coin (0,0) d'une grille 3x3, il y a 3 voisins."""
        data = {
            "motif1": [
                [0, 0, 0], [1, 0, 0], [2, 0, 0],
                [0, 1, 0], [1, 1, 0], [2, 1, 0],
                [0, 2, 0], [1, 2, 0], [2, 2, 0],
            ]
        }
        grid = Grid.from_data(data)
        neighbours = grid.neighbours(0, 0)
        assert len(neighbours) == 3

    def test_neighbours_edge(self):
        """Sur le bord (1,0) d'une grille 3x3, il y a 5 voisins."""
        data = {
            "motif1": [
                [0, 0, 0], [1, 0, 0], [2, 0, 0],
                [0, 1, 0], [1, 1, 0], [2, 1, 0],
                [0, 2, 0], [1, 2, 0], [2, 2, 0],
            ]
        }
        grid = Grid.from_data(data)
        neighbours = grid.neighbours(1, 0)
        assert len(neighbours) == 5

    def test_duplicate_pattern_name_raises(self):
        """Deux patterns avec le meme nom levent PatternAlreadyLoaded."""
        p1 = Pattern("motif1", [Cell(0, 0)])
        p2 = Pattern("motif1", [Cell(1, 0)])
        with pytest.raises(PatternAlreadyLoaded):
            Grid([p1, p2])

    def test_to_dict(self):
        """to_dict serialise la grille en dictionnaire."""
        data = _make_test_grid_data()
        grid = Grid.from_data(data)
        d = grid.to_dict()
        assert "motif1" in d
        assert "motif2" in d

    def test_matrix_references(self):
        """La matrice contient bien les references aux cellules."""
        data = _make_test_grid_data()
        grid = Grid.from_data(data)
        # La cellule en (0,0) dans la matrice doit etre la meme
        # que celle du motif
        cell = grid.get_cell(0, 0)
        pattern = grid.get_pattern_of(0, 0)
        # On verifie que c'est le meme objet en memoire
        found = False
        for c in pattern.cells:
            if c.x == 0 and c.y == 0:
                assert c is cell
                found = True
        assert found == True

    def test_from_data_ignores_non_motif_keys(self):
        """from_data ignore les cles qui ne commencent pas par 'motif'."""
        data = {
            "motif1": [[0, 0, 0]],
            "autre_cle": [[1, 1, 0]],
        }
        grid = Grid.from_data(data)
        assert len(grid.patterns) == 1

    def test_grid_with_single_cell_pattern(self):
        """Un motif d'une seule cellule fonctionne."""
        data = {"motif1": [[0, 0, 0]]}
        grid = Grid.from_data(data)
        assert grid.width == 1
        assert grid.height == 1
        assert len(grid.patterns) == 1
        assert grid.patterns[0].size() == 1

    def test_is_complete_empty_grid(self):
        """Une grille avec des cases vides n'est pas complete."""
        data = _make_test_grid_data()
        grid = Grid.from_data(data)
        assert grid.is_complete() == False

    def test_is_complete_with_empty_cell(self):
        """Une grille partiellement remplie n'est pas complete."""
        data = {
            "motif1": [[0, 0, 1], [1, 0, 0]],
            "motif2": [[0, 1, 2], [1, 1, 1]],
        }
        grid = Grid.from_data(data)
        # La cellule (1,0) est vide (valeur 0)
        assert grid.is_complete() == False

    def test_is_complete_with_neighbor_conflict(self):
        """Une grille remplie mais avec un conflit voisin n'est pas complete."""
        data = {
            "motif1": [[0, 0, 1], [1, 0, 0]],
            "motif2": [[0, 1, 1], [1, 1, 2]],
        }
        grid = Grid.from_data(data)
        # (0,0) et (0,1) sont voisins et ont la meme valeur 1
        assert grid.is_complete() == False

    def test_is_complete_with_pattern_duplicate(self):
        """Une grille remplie mais avec un doublon dans un motif n'est pas complete."""
        data = {
            "motif1": [[0, 0, 1], [1, 0, 1]],
        }
        grid = Grid.from_data(data)
        # motif1 a deux fois la valeur 1
        assert grid.is_complete() == False

    def test_is_complete_solved_grid(self):
        """Une grille resolue correctement est complete."""
        # Grille 4x2 avec 2 motifs de 4 cellules, sans conflit
        data = {
            "motif1": [[0, 0, 1], [1, 0, 2], [2, 0, 3], [3, 0, 4]],
            "motif2": [[0, 1, 3], [1, 1, 4], [2, 1, 1], [3, 1, 2]],
        }
        grid = Grid.from_data(data)
        assert grid.is_complete() == True

    def test_is_complete_after_solver(self):
        """Apres resolution par le solver, is_complete retourne True."""
        import os
        grids_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "grids")
        path = os.path.join(grids_dir, "grid8.json")
        if not os.path.exists(path):
            pytest.skip("grid8.json non trouve")
        grid = Grid.from_json(path)
        solver = Solver(grid)
        solver.solve_grid()
        assert grid.is_complete() == True


# ============================================================
# Tests pour le chargement des grilles JSON
# ============================================================

class TestGridJSON:

    # Dossier des grilles
    GRIDS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "grids")

    def _grid_files(self):
        """Retourne la liste des fichiers JSON de grilles."""
        files = []
        if os.path.exists(self.GRIDS_DIR):
            for f in os.listdir(self.GRIDS_DIR):
                if f.endswith(".json"):
                    files.append(os.path.join(self.GRIDS_DIR, f))
        return files

    def test_all_grids_load(self):
        """Toutes les grilles se chargent sans erreur."""
        for path in self._grid_files():
            grid = Grid.from_json(path)
            assert grid.width > 0
            assert grid.height > 0
            assert len(grid.patterns) > 0

    def test_all_grids_have_cells(self):
        """Chaque motif de chaque grille a au moins 1 cellule."""
        for path in self._grid_files():
            grid = Grid.from_json(path)
            for pattern in grid.patterns:
                assert pattern.size() >= 1

    def test_roundtrip_json(self):
        """Charger une grille, la serialiser, et la recharger donne le meme resultat."""
        data = _make_test_grid_data()
        grid1 = Grid.from_data(data)

        # Serialiser
        d = grid1.to_dict()

        # Recharger
        grid2 = Grid.from_data(d)

        assert grid1.width == grid2.width
        assert grid1.height == grid2.height
        assert len(grid1.patterns) == len(grid2.patterns)

    def test_from_json_specific_file(self):
        """Charger grid8.json (6x4) et verifier les dimensions."""
        path = os.path.join(self.GRIDS_DIR, "grid8.json")
        if os.path.exists(path):
            grid = Grid.from_json(path)
            w, h = grid.get_dimensions()
            assert w == 6
            assert h == 4

    def test_from_json_grid7(self):
        """Charger grid7.json (5x6) et verifier les dimensions."""
        path = os.path.join(self.GRIDS_DIR, "grid7.json")
        if os.path.exists(path):
            grid = Grid.from_json(path)
            w, h = grid.get_dimensions()
            assert w == 5
            assert h == 6


# ============================================================
# Tests pour le Solveur (Solver)
# ============================================================

class TestSolver:

    # Dossier des grilles
    GRIDS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "grids")

    def _get_grid_path(self, filename):
        """Retourne le chemin complet d'un fichier grille."""
        return os.path.join(self.GRIDS_DIR, filename)

    def test_solve_small_grid(self):
        """Le solveur resout grid8.json (grille 6x4, petite)."""
        path = self._get_grid_path("grid8.json")
        if not os.path.exists(path):
            pytest.skip("grid8.json non trouve")
        grid = Grid.from_json(path)
        solver = Solver(grid)
        result = solver.solve_grid()
        assert result == True

        # Verifier que toutes les cellules sont remplies
        for pattern in grid.patterns:
            for cell in pattern.cells:
                assert cell.value != 0

    def test_solve_grid_already_complete(self):
        """Le solveur retourne True si on lui donne une grille deja resolue."""
        path = self._get_grid_path("grid8.json")
        if not os.path.exists(path):
            pytest.skip("grid8.json non trouve")
        # On charge et on resout d'abord
        grid = Grid.from_json(path)
        solver = Solver(grid)
        solver.solve_grid()
        # Maintenant la grille est complete, on relance le solveur
        solver2 = Solver(grid)
        result = solver2.solve_grid()
        assert result == True

    def test_solve_grid_with_initial_clues(self):
        """Le solveur resout grid7.json (grille 5x6 avec des indices)."""
        path = self._get_grid_path("grid7.json")
        if not os.path.exists(path):
            pytest.skip("grid7.json non trouve")
        grid = Grid.from_json(path)
        solver = Solver(grid)
        result = solver.solve_grid()
        assert result == True

    def test_solve_grid_impossible_neighbor_conflict(self):
        """Le solveur retourne False si les indices causent un conflit voisin."""
        # Deux voisins avec la meme valeur 1 -> impossible
        data = {
            "motif1": [[0, 0, 1], [1, 0, 0]],
            "motif2": [[0, 1, 1], [1, 1, 0]],
        }
        grid = Grid.from_data(data)
        solver = Solver(grid)
        result = solver.solve_grid()
        assert result == False

    def test_solve_grid_impossible_pattern_conflict(self):
        """Le solveur retourne False si un motif a un doublon."""
        # motif1 a deux cellules avec la valeur 2
        data = {
            "motif1": [[0, 0, 2], [1, 0, 2]],
        }
        grid = Grid.from_data(data)
        solver = Solver(grid)
        result = solver.solve_grid()
        assert result == False

    def test_solve_grid8(self):
        """Le solveur resout grid8.json (petite grille 6x4)."""
        grids_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "grids")
        path = os.path.join(grids_dir, "grid8.json")
        if not os.path.exists(path):
            pytest.skip("grid8.json non trouve")
        grid = Grid.from_json(path)
        solver = Solver(grid)
        result = solver.solve_grid()
        assert result == True

    def test_solve_grid7(self):
        """Le solveur resout grid7.json (grille 5x6)."""
        grids_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "grids")
        path = os.path.join(grids_dir, "grid7.json")
        if not os.path.exists(path):
            pytest.skip("grid7.json non trouve")
        grid = Grid.from_json(path)
        solver = Solver(grid)
        result = solver.solve_grid()
        assert result == True

    def test_solve_all_grids(self):
        """Le solveur resout toutes les grilles du dossier."""
        grids_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "grids")
        if not os.path.exists(grids_dir):
            pytest.skip("Dossier data/grids non trouve")

        for filename in os.listdir(grids_dir):
            if not filename.endswith(".json"):
                continue
            path = os.path.join(grids_dir, filename)
            grid = Grid.from_json(path)
            solver = Solver(grid)
            result = solver.solve_grid()
            # grid6.json est connue comme etant impossible
            if filename == "grid6.json":
                assert result == False
            else:
                assert result == True, f"Le solveur a echoue sur {filename}"

    def test_solve_is_alias(self):
        """solve() est un alias pour solve_grid()."""
        path = self._get_grid_path("grid8.json")
        if not os.path.exists(path):
            pytest.skip("grid8.json non trouve")
        grid = Grid.from_json(path)
        solver = Solver(grid)
        assert solver.solve() == True

    def test_solve_respects_neighbor_constraint(self):
        """Apres resolution, aucun voisin n'a la meme valeur."""
        path = self._get_grid_path("grid8.json")
        if not os.path.exists(path):
            pytest.skip("grid8.json non trouve")
        grid = Grid.from_json(path)
        solver = Solver(grid)
        result = solver.solve_grid()
        assert result == True

        # Verifier qu'aucun voisin n'a la meme valeur
        for pattern in grid.patterns:
            for cell in pattern.cells:
                for neighbour in grid.neighbours(cell.x, cell.y):
                    if neighbour.value != 0:
                        assert cell.value != neighbour.value, \
                            f"Conflit en ({cell.x},{cell.y}) et ({neighbour.x},{neighbour.y})"

    def test_get_possible_values(self):
        """_get_possible_values retourne les bonnes valeurs candidates."""
        data = {
            "motif1": [[0, 0, 1], [1, 0, 0]],
            "motif2": [[0, 1, 0], [1, 1, 0]],
        }
        grid = Grid.from_data(data)
        solver = Solver(grid)

        # La cellule (1,0) est dans motif1 qui a 2 cellules
        # La valeur 1 est deja prise dans motif1, et le voisin (0,0) a 1
        # Donc les valeurs possibles sont seulement [2]
        cell = grid.get_cell(1, 0)
        possible = solver._get_possible_values(cell)
        assert 1 not in possible

    def test_has_conflict_true(self):
        """_has_conflict detecte un conflit entre voisins."""
        data = {
            "motif1": [[0, 0, 5], [1, 0, 5]],
            "motif2": [[0, 1, 0], [1, 1, 0]],
        }
        grid = Grid.from_data(data)
        solver = Solver(grid)
        cell = grid.get_cell(0, 0)
        assert solver._has_conflict(cell) == True

    def test_has_conflict_false(self):
        """_has_conflict ne detecte pas de conflit si les voisins sont differents."""
        data = {
            "motif1": [[0, 0, 1], [1, 0, 2]],
            "motif2": [[0, 1, 3], [1, 1, 4]],
        }
        grid = Grid.from_data(data)
        solver = Solver(grid)
        cell = grid.get_cell(0, 0)
        assert solver._has_conflict(cell) == False

    def test_has_conflict_zero_value(self):
        """_has_conflict ignore les voisins avec valeur 0."""
        data = {
            "motif1": [[0, 0, 5], [1, 0, 0]],
            "motif2": [[0, 1, 0], [1, 1, 0]],
        }
        grid = Grid.from_data(data)
        solver = Solver(grid)
        cell = grid.get_cell(0, 0)
        assert solver._has_conflict(cell) == False


# ============================================================
# Tests pour le generateur de grilles
# ============================================================

class TestGenerateGrid:

    def test_generate_grid_default(self):
        """generate_grid genere une grille par defaut."""
        from generate_grid import generate_grid
        data = generate_grid()
        assert len(data) > 0
        # Chaque motif doit avoir au moins 1 cellule
        for name, cells in data.items():
            assert len(cells) >= 1

    def test_generate_grid_custom_size(self):
        """generate_grid genere une grille aux dimensions donnees."""
        from generate_grid import generate_grid
        data = generate_grid(width=5, height=5)

        # Reconstruire la grille pour verifier les dimensions
        grid = Grid.from_data(data)
        assert grid.width == 5
        assert grid.height == 5

    def test_generate_grid_has_clues(self):
        """La grille generee a au moins 1 indice (valeur non-nulle)."""
        from generate_grid import generate_grid
        data = generate_grid(width=4, height=4)

        clues = 0
        for cells in data.values():
            for cell in cells:
                if cell[2] != 0:
                    clues += 1
        assert clues >= 1

    def test_generate_grid_solvable(self):
        """La grille generee est resolvable par le solveur."""
        from generate_grid import generate_grid
        data = generate_grid(width=4, height=4)
        grid = Grid.from_data(data)
        solver = Solver(grid)
        assert solver.solve_grid() == True

    def test_generate_regions(self):
        """generate_regions cree des regions qui couvrent toute la grille."""
        from generate_grid import generate_regions
        data = generate_regions(4, 4)

        # Compter le nombre total de cellules
        total = 0
        for cells in data.values():
            total += len(cells)
        assert total == 16  # 4x4

    def test_solve_and_strip(self):
        """solve_and_strip retourne des donnees valides."""
        from generate_grid import generate_regions, solve_and_strip
        data = generate_regions(4, 4)
        result = solve_and_strip(data, clue_ratio=0.5)

        # Il doit y avoir des indices et des cases vides
        has_clue = False
        has_empty = False
        for cells in result.values():
            for cell in cells:
                if cell[2] != 0:
                    has_clue = True
                else:
                    has_empty = True
        assert has_clue == True
        assert has_empty == True
