import os
import re

class _OpenpyxlSheet:
    """Expose the small worksheet API used by SumTableTool."""

    def __init__(self, sheet):
        self.sheet = sheet
        self.nrows = sheet.max_row

    def row_values(self, index, start_colx=0):
        row = next(
            self.sheet.iter_rows(min_row=index + 1, max_row=index + 1, values_only=True),
            (),
        )
        return ["" if value is None else value for value in row[start_colx:]]

    def col_values(self, index):
        return [self.row_values(row)[index] for row in range(self.nrows)]

    def cell_value(self, row, column):
        value = self.sheet.cell(row + 1, column + 1).value
        return "" if value is None else value


class SumTableTool:
    def __init__(self, wb_path):
        self.path = wb_path
        self.excel = None
        self.wb = None
        self.ws = None
        self.load_error = None

        self.prev = []
        self.values = []

        self.asc_pattern = re.compile(r"^\d{8}@\d+\.asc$")

        self.asc_filter = {"from": None, "to": None}
        self.comment_filter = ""

        if os.path.exists(self.path):
            self.load_workbook()
        else:
            self.load_error = "File not found."

    def load_workbook(self):
        self.excel = None
        self.wb = None
        self.ws = None
        self.load_error = None
        self.values = []
        try:
            if self.path.lower().endswith(".xlsx"):
                from openpyxl import load_workbook

                self.excel = load_workbook(self.path, read_only=True, data_only=True)
            else:
                import xlrd

                self.excel = xlrd.open_workbook(filename=self.path)
        except Exception as error:
            self.load_error = str(error)
            return None

        self.wb = self.excel

        try:
            sheet_names = self.wb.sheetnames if self.path.lower().endswith(".xlsx") else self.wb.sheet_names()
            if "Sum_table" in sheet_names:
                name = "Sum_table"
            elif "Data" in sheet_names:
                name = "Data"
            else:
                raise ValueError("No appropriate worksheet.")
            if self.path.lower().endswith(".xlsx"):
                self.ws = _OpenpyxlSheet(self.wb[name])
            else:
                self.ws = self.wb.sheet_by_name(name)
        except ValueError as err:
            self.load_error = str(err)
            return None

    def reload_workbook(self):
        self.excel = None
        self.load_workbook()

    def get_workbook_name(self):
        return os.path.basename(self.path)

    def get_workbook_path(self):
        return self.path

    def get_selected_address(self):
        # return an address of Cells(last row + 1, 1) // column A
        return "$A${}".format(self.find_last_row() + 1)
        # return self.excel.ActiveCell.Address

    def get_selected_value(self):
        last_row = self.find_last_row()
        try:
            return self.ws.cell_value(last_row + 1, 0)
        except IndexError:
            return ""
        # return self.excel.ActiveCell.Value

    def find_columns(self, labels, spreadsheet=True):
        headers = self.get_headers()
        offset = 0
        try:
            return [headers.index(label) + offset for label in labels]
        except ValueError:
            print("find_columns: Label Not Found")
            return None

    def find_last_row(self):
        return len(self.ws.col_values(0)) - 1

    def find_last_column(self):
        return len(self.get_headers()) - 1

    def get_headers(self):
        return self.ws.row_values(0, 0)

    def get_values(self):
        self.values = self._all_data_rows()
        if self.asc_filter["from"] is not None or self.asc_filter["to"] is not None:
            self.values = self.filter_by_asc(self.asc_filter["from"], self.asc_filter["to"])
        elif self.comment_filter != "":
            self.values = self.filter_by_comment(self.comment_filter)
        return self.values

    def _all_data_rows(self):
        if self.ws is None:
            return []
        rows = (self.ws.row_values(index) for index in range(1, self.ws.nrows))
        return [row for row in rows if row and isinstance(row[0], str) and self.asc_pattern.match(row[0])]

    def get_asc_list(self):
        if self.values == []:
            self.get_values()
        return [r[0] for r in self.values]

    def filter_by_comment(self, pattern):
        columns = self.find_columns(["Comment"])
        if columns is None:
            return []
        comm_col = columns[0]
        pat = re.compile(pattern, re.I)
        return [r for r in self._all_data_rows() if pat.search(str(r[comm_col]))]

    def filter_by_asc(self, start=None, end=None):
        # start=None, end=None: All (from smallest to largest)
        # start=None, end=xxx: from smallest to xxx
        # start=xxx, end=None: from xxx to largest
        # start=xxx, end=yyy: from xxx to yyy
        values = self._all_data_rows()
        if not values:
            return []
        asc = [r[0] for r in values]
        rNum = len(values)
        if start is None:
            if end is None:
                return values
            else:
                smallest = asc[0]
                largest = end
        elif end is None:
            smallest = start
            largest = asc[rNum - 1]
        else:
            smallest = start
            largest = end

        try:
            s_idx = asc.index(smallest)
            e_idx = asc.index(largest)
            if s_idx < 0 or e_idx < 0:
                return values
        except ValueError:
            return values

        return values[s_idx : e_idx + 1]

    def is_modified(self, val=None):
        if val is None:
            if self.values == []:
                val = self.get_values()
            else:
                val = self.values
        return not self.prev == val

    def modified_rows(self):
        out = []
        self.get_values()
        if self.is_modified():
            out = [r for r in range(len(self.values)) if r >= len(self.prev) or not self.prev[r] == self.values[r]]

        return out
