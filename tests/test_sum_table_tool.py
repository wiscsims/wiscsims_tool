"""Workbook filtering regressions that do not require QGIS."""

import importlib.util
import pathlib
import sys
import tempfile
import types
import unittest
from unittest.mock import patch


MODULE_PATH = pathlib.Path(__file__).resolve().parents[1] / "tools/imports/sumTableTool.py"


class FakeSheet:
    def __init__(self, rows):
        self.rows = rows
        self.nrows = len(rows)

    def row_values(self, index, start_colx=0):
        return self.rows[index][start_colx:]


class FakeWorkbook:
    def __init__(self, rows):
        self.sheet = FakeSheet(rows)

    def sheet_names(self):
        return ["Sum_table"]

    def sheet_by_name(self, name):
        return self.sheet


class FakeOpenpyxlSheet:
    def __init__(self, rows):
        self.rows = rows
        self.max_row = len(rows)

    def iter_rows(self, min_row, max_row, values_only):
        return iter([self.rows[min_row - 1]])

    def cell(self, row, column):
        return types.SimpleNamespace(value=self.rows[row - 1][column - 1])


class FakeOpenpyxlWorkbook:
    sheetnames = ["Data"]

    def __init__(self, rows):
        self.sheet = FakeOpenpyxlSheet(rows)

    def __getitem__(self, name):
        return self.sheet


class SumTableToolTests(unittest.TestCase):
    def setUp(self):
        self.excel = types.ModuleType("xlrd")
        self.excel.open_workbook = lambda filename: FakeWorkbook(self.rows)
        self.excel_patch = patch.dict(sys.modules, {"xlrd": self.excel})
        self.excel_patch.start()
        spec = importlib.util.spec_from_file_location("sum_table_under_test", MODULE_PATH)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        self.tool_class = module.SumTableTool
        self.path = tempfile.NamedTemporaryFile(suffix=".xls")

    def tearDown(self):
        self.path.close()
        self.excel_patch.stop()

    @property
    def rows(self):
        return self._rows

    def test_empty_sheet_has_no_data_or_filter_recursion(self):
        self._rows = [["File", "Comment", "X", "Y"]]
        tool = self.tool_class(self.path.name)
        tool.asc_filter["from"] = "20200101@1.asc"
        self.assertEqual(tool.get_values(), [])
        self.assertEqual(tool.filter_by_asc(), [])
        self.assertEqual(tool.get_asc_list(), [])

    def test_range_and_comment_filters_start_from_all_rows(self):
        self._rows = [
            ["File", "Comment", "X", "Y"],
            ["20200101@1.asc", "a", 1, 2],
            ["20200101@2.asc", "b", 3, 4],
            ["20200101@3.asc", 42, 5, 6],
        ]
        tool = self.tool_class(self.path.name)
        self.assertEqual(len(tool.filter_by_asc("20200101@2.asc", "20200101@3.asc")), 2)
        self.assertEqual(len(tool.filter_by_comment("a")), 1)
        self.assertEqual(len(tool.filter_by_asc()), 3)

    def test_unreadable_workbook_has_explicit_empty_state(self):
        self._rows = []
        self.excel.open_workbook = lambda filename: (_ for _ in ()).throw(ValueError("bad"))
        tool = self.tool_class(self.path.name)
        self.assertIsNone(tool.ws)
        self.assertEqual(tool.get_values(), [])

    def test_xlsx_uses_openpyxl_and_preserves_data_rows(self):
        self._rows = [
            ["File", "Comment", "X", "Y"],
            ["20200101@1.asc", "spot", 1, 2],
        ]
        openpyxl = types.ModuleType("openpyxl")
        openpyxl.load_workbook = lambda path, read_only, data_only: FakeOpenpyxlWorkbook(self.rows)
        with tempfile.NamedTemporaryFile(suffix=".xlsx") as path:
            with patch.dict(sys.modules, {"openpyxl": openpyxl}):
                tool = self.tool_class(path.name)
                self.assertEqual(tool.get_values(), [self.rows[1]])
                self.assertEqual(tool.find_columns(["X", "Y"]), [2, 3])


if __name__ == "__main__":
    unittest.main()
