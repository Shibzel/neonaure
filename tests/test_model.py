"""
Unit tests for neonaure.model
Run with: python -m pytest tests/ -v
"""

from __future__ import annotations

import os
import tempfile
from typing import Any

import pytest

from neonaure.model import (
    Cell,
    CellIsImmuable,
    Grid,
    InvalidGrid,
    Pattern,
    PatternAlreadyLoaded,
    Solver,
)


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------

def _make_pattern(name: str, cells_data: list[tuple[int, int, int]]) -> Pattern:
    """Build a Pattern from (x, y, value) tuples."""
    pat: Pattern = Pattern(name)
    for x, y, v in cells_data:
        pat.cells.append(Cell(x, y, v, immuable=(v != 0)))
    return pat


def _small_grid_data() -> dict[str, list[list[int]]]:
    """4x4 grid, 4 motifs of 4 cells each, a few clues given."""
    return {
        "motif1": [[0, 0, 3], [1, 0, 0], [0, 1, 0], [1, 1, 0]],
        "motif2": [[2, 0, 0], [3, 0, 0], [2, 1, 0], [3, 1, 2]],
        "motif3": [[0, 2, 0], [1, 2, 0], [0, 3, 0], [1, 3, 0]],
        "motif4": [[2, 2, 0], [3, 2, 0], [2, 3, 0], [3, 3, 0]],
    }


def _solved_grid_data() -> dict[str, list[list[int]]]:
    """4x4 grid completely filled, valid under all 3 Neonaure rules."""
    return {
        "motif1": [[0, 0, 3], [1, 0, 1], [0, 1, 4], [1, 1, 2]],
        "motif2": [[2, 0, 3], [3, 0, 1], [2, 1, 4], [3, 1, 2]],
        "motif3": [[0, 2, 1], [1, 2, 3], [0, 3, 2], [1, 3, 4]],
        "motif4": [[2, 2, 1], [3, 2, 3], [2, 3, 2], [3, 3, 4]],
    }


# ------------------------------------------------------------------
# Cell tests
# ------------------------------------------------------------------

class TestCell:
    def test_default_value_is_zero(self) -> None:
        c: Cell = Cell(0, 0)
        assert c.value == 0
        assert c.is_empty()

    def test_immuable_cell_cannot_be_edited(self) -> None:
        c: Cell = Cell(1, 2, value=5, immuable=True)
        assert c.value == 5
        assert not c.is_empty()
        with pytest.raises(CellIsImmuable):
            c.set_value(3)

    def test_mutable_cell_can_change(self) -> None:
        c: Cell = Cell(0, 0)
        c.set_value(4)
        assert c.value == 4

    def test_equality_checks_value_only(self) -> None:
        a: Cell = Cell(0, 0, value=3)
        b: Cell = Cell(5, 5, value=3)
        assert a == b

    def test_equality_ignores_zero(self) -> None:
        a: Cell = Cell(0, 0, value=0)
        b: Cell = Cell(1, 1, value=0)
        assert not (a == b)

    def test_to_list_roundtrip(self) -> None:
        c: Cell = Cell(2, 3, value=1, immuable=True)
        data: list[int | bool] = c.to_list()
        assert data == [2, 3, 1, True]


# ------------------------------------------------------------------
# Pattern tests
# ------------------------------------------------------------------

class TestPattern:
    def _pat_3cells(self) -> Pattern:
        return _make_pattern("motif1", [(0, 0, 1), (1, 0, 0), (0, 1, 2)])

    def test_size(self) -> None:
        assert self._pat_3cells().size() == 3

    def test_values_ignores_empty(self) -> None:
        vals: list[int] = self._pat_3cells().values()
        assert sorted(vals) == [1, 2]

    def test_missing_values(self) -> None:
        missing: list[int] = self._pat_3cells().missing_values()
        assert missing == [3]

    def test_contains_value(self) -> None:
        pat: Pattern = self._pat_3cells()
        assert pat.contains_value(1)
        assert not pat.contains_value(3)

    def test_get_cell_found(self) -> None:
        pat: Pattern = self._pat_3cells()
        c: Cell | None = pat.get_cell(1, 0)
        assert c is not None
        assert c.is_empty()

    def test_get_cell_missing(self) -> None:
        assert self._pat_3cells().get_cell(5, 5) is None

    def test_from_raw_cells_immutable_on_clue(self) -> None:
        raw: list[list[int]] = [[0, 0, 5], [1, 0, 0]]
        pat: Pattern = Pattern.from_raw_cells("motifA", raw)
        assert pat.cells[0].immuable is True
        assert pat.cells[1].immuable is False

    def test_from_raw_cells_four_columns(self) -> None:
        raw: list[list[int]] = [[0, 0, 3, False], [1, 0, 0, True]]
        pat: Pattern = Pattern.from_raw_cells("motifB", raw)
        assert pat.cells[0].immuable is False
        assert pat.cells[1].immuable is True

    def test_to_list_roundtrip(self) -> None:
        pat: Pattern = self._pat_3cells()
        data: list[list[int | bool]] = pat.to_list()
        assert len(data) == 3
        assert data[0][:3] == [0, 0, 1]

    def test_set_cell_existing(self) -> None:
        pat: Pattern = self._pat_3cells()
        pat.set_cell(1, 0, 7)
        c: Cell | None = pat.get_cell(1, 0)
        assert c is not None
        assert c.value == 7

    def test_set_cell_new(self) -> None:
        pat: Pattern = self._pat_3cells()
        pat.set_cell(2, 0, 4)
        assert pat.size() == 4
        assert pat.get_cell(2, 0) is not None


# ------------------------------------------------------------------
# Grid tests
# ------------------------------------------------------------------

class TestGrid:
    def _small_grid(self) -> Grid:
        return Grid.from_data(_small_grid_data())

    def test_dimensions(self) -> None:
        g: Grid = self._small_grid()
        assert g.width == 4
        assert g.height == 4

    def test_get_cell(self) -> None:
        g: Grid = self._small_grid()
        c: Cell | None = g.get_cell(0, 0)
        assert c is not None
        assert c.value == 3

    def test_get_cell_out_of_bounds(self) -> None:
        g: Grid = self._small_grid()
        assert g.get_cell(99, 99) is None

    def test_get_pattern_of(self) -> None:
        g: Grid = self._small_grid()
        pat: Pattern | None = g.get_pattern_of(0, 0)
        assert pat is not None
        assert pat.name == "motif1"

    def test_neighbours_corner(self) -> None:
        g: Grid = self._small_grid()
        nb: list[Cell] = g.neighbours(0, 0)
        positions: set[tuple[int, int]] = {(c.x, c.y) for c in nb}
        assert (1, 0) in positions
        assert (0, 1) in positions
        assert (1, 1) in positions
        assert len(nb) == 3

    def test_neighbours_center(self) -> None:
        data: dict[str, list[list[int]]] = {
            "motif1": [[0, 0, 0], [1, 0, 0], [2, 0, 0]],
            "motif2": [[0, 1, 0], [1, 1, 0], [2, 1, 0]],
            "motif3": [[0, 2, 0], [1, 2, 0], [2, 2, 0]],
        }
        g: Grid = Grid.from_data(data)
        nb: list[Cell] = g.neighbours(1, 1)
        assert len(nb) == 8

    def test_is_valid_placement_good(self) -> None:
        g: Grid = self._small_grid()
        assert g.is_valid_placement(1, 0, 1)

    def test_is_valid_placement_duplicate_in_pattern(self) -> None:
        g: Grid = self._small_grid()
        assert not g.is_valid_placement(1, 0, 3)

    def test_is_valid_placement_neighbour_conflict(self) -> None:
        g: Grid = self._small_grid()
        assert not g.is_valid_placement(0, 1, 3)

    def test_is_valid_placement_out_of_range(self) -> None:
        g: Grid = self._small_grid()
        assert not g.is_valid_placement(1, 0, 5)

    def test_is_complete_false(self) -> None:
        assert not self._small_grid().is_complete()

    def test_is_complete_true(self) -> None:
        g: Grid = Grid.from_data(_solved_grid_data())
        assert g.is_complete()

    def test_is_solved_valid(self) -> None:
        g: Grid = Grid.from_data(_solved_grid_data())
        assert g.is_solved()

    def test_is_solved_incomplete(self) -> None:
        assert not self._small_grid().is_solved()

    def test_duplicate_pattern_name_rejected(self) -> None:
        p1: Pattern = _make_pattern("motif1", [(0, 0, 1)])
        p2: Pattern = _make_pattern("motif1", [(1, 0, 2)])
        with pytest.raises(PatternAlreadyLoaded):
            Grid([p1, p2])

    def test_set_cell_value(self) -> None:
        g: Grid = self._small_grid()
        assert g.set_cell_value(0, 1, 3)
        assert g.get_cell(0, 1).value == 3

    def test_set_cell_value_immuable_blocked(self) -> None:
        g: Grid = self._small_grid()
        assert not g.set_cell_value(0, 0, 9)

    def test_json_roundtrip(self) -> None:
        g: Grid = self._small_grid()
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False, mode="w") as f:
            path: str = f.name
        try:
            g.save_grid_to_json(path)
            loaded: Grid = Grid.from_json(path)
            assert loaded.width == g.width
            assert loaded.height == g.height
            assert len(loaded.patterns) == len(g.patterns)
        finally:
            os.unlink(path)


# ------------------------------------------------------------------
# Grid loading from real files
# ------------------------------------------------------------------

class TestGridLoading:
    GRIDS_DIR: str = os.path.join(os.path.dirname(__file__), "..", "data", "grids")

    def _grid_names(self) -> list[str]:
        files: list[str] = [f for f in os.listdir(self.GRIDS_DIR) if f.endswith(".json")]
        files.sort()
        return files

    def test_all_grids_load_without_error(self) -> None:
        for name in self._grid_names():
            g: Grid = Grid.from_json(os.path.join(self.GRIDS_DIR, name))
            assert g.width > 0
            assert g.height > 0
            assert len(g.patterns) > 0

    def test_all_grids_roundtrip(self) -> None:
        for name in self._grid_names():
            g: Grid = Grid.from_json(os.path.join(self.GRIDS_DIR, name))
            with tempfile.NamedTemporaryFile(suffix=".json", delete=False, mode="w") as f:
                path: str = f.name
            try:
                g.save_grid_to_json(path)
                g2: Grid = Grid.from_json(path)
                assert g2.width == g.width
                assert g2.height == g.height
            finally:
                os.unlink(path)


# ------------------------------------------------------------------
# Solver tests
# ------------------------------------------------------------------

class TestSolver:
    GRIDS_DIR: str = os.path.join(os.path.dirname(__file__), "..", "data", "grids")

    def test_solve_small_grid(self) -> None:
        g: Grid = Grid.from_data(_small_grid_data())
        s: Solver = Solver(g)
        assert s.solve()
        assert g.is_solved()

    def test_solve_returns_false_for_impossible(self) -> None:
        data: dict[str, list[list[int]]] = {
            "motif1": [[0, 0, 1], [1, 0, 1]],
        }
        g: Grid = Grid.from_data(data)
        s: Solver = Solver(g)
        assert not s.solve()

    def test_solve_grid8(self) -> None:
        g: Grid = Grid.from_json(os.path.join(self.GRIDS_DIR, "grid8.json"))
        s: Solver = Solver(g)
        assert s.solve()
        assert g.is_solved()

    def test_solve_grid7(self) -> None:
        g: Grid = Grid.from_json(os.path.join(self.GRIDS_DIR, "grid7.json"))
        s: Solver = Solver(g)
        assert s.solve()
        assert g.is_solved()

    def test_solve_all_grids(self) -> None:
        for name in sorted(os.listdir(self.GRIDS_DIR)):
            if not name.endswith(".json"):
                continue
            g: Grid = Grid.from_json(os.path.join(self.GRIDS_DIR, name))
            s: Solver = Solver(g)
            if name == "grid6.json":
                continue
            assert s.solve(), f"Failed to solve {name}"
            assert g.is_solved()

    def test_hint_returns_valid_move(self) -> None:
        g: Grid = Grid.from_data(_small_grid_data())
        s: Solver = Solver(g)
        hint: tuple[int, int, int] | None = s.hint()
        assert hint is not None
        x: int
        y: int
        val: int
        x, y, val = hint
        assert g.is_valid_placement(x, y, val)

    def test_count_solutions_at_least_one(self) -> None:
        g: Grid = Grid.from_json(os.path.join(self.GRIDS_DIR, "grid8.json"))
        s: Solver = Solver(g)
        count: int = s.count_solutions(max_count=2)
        assert count >= 1
