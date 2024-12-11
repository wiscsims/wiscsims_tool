import os
import re
from importlib.metadata import version
import pandas as pd

# if os.name == 'nt':
#     import win32com.client
#     import win32gui
#     import win32con


class SumTableTool:
    def __init__(self, wb_path):
        self.path = wb_path

        if not os.path.exists(self.path):
            return None

        # self.excel = None
        # self.wb = None
        # self.ws = None

        self.prev = []
        self.values = []

        self.asc_pattern = re.compile(r"^\d{8}@\d+\.asc$")

        self.asc_filter = {"from": None, "to": None}
        self.comment_filter = ""
        self.ws: pd.DataFrame

        self.load_workbook()

    def load_workbook(self):
        engine = "xlrd"

        if int(version("xlrd").split(".")[0]) > 1:
            engine = "openpyxl"

        try:
            # self.excel = pd.read_excel(self.path, sheet_name=None, engine="xlrd")
            self.excel = pd.read_excel(self.path, sheet_name=None, engine=engine)
            # self.excel = xl.open_workbook(filename=self.path)
        except Exception as e:
            print(f"error on open_workbook // path: {self.path}")
            print(e)
            return None

        try:
            self.wb = self.excel
        except Exception:
            return None

        try:
            sheet_list = list(self.wb.keys())
            if "Sum_table" in sheet_list:
                self.ws = self.wb["Sum_table"]
            elif "Data" in sheet_list:
                self.ws = self.wb["Data"]
            else:
                raise ValueError("No appropriate worksheet.")

            self.ws = self.ws[~self.ws["File"].isna()]

            k = list(self.ws.keys())

            # convert Date and Time to str
            if "Date" in k:
                self.ws["Date"] = [r.strftime("%m/%d/%Y") for r in self.ws["Date"]]
            if "Time" in k:
                self.ws["Time"] = [r.strftime("%H:%M") for r in self.ws["Time"]]

            self.ws = self.ws.astype("object")

            pat = re.compile(r"@([0-9]+)\.asc$")
            self.ws["n"] = [int(pat.search(f).groups()[0]) for f in self.ws["File"]]

        except ValueError as err:
            print(err)
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
            return [headers.index(l) + offset for l in labels]
        except ValueError:
            print("find_columns: Label Not Found")
            return None

    def find_last_row(self):
        last_r, _ = self.ws.shape
        return last_r - 1

    def find_last_column(self):
        _, last_c = self.ws.shape
        # return len(self.get_headers()) - 1
        return last_c - 1

    def get_headers(self):
        return self.ws.columns.tolist()
        # return self.ws.row_values(0, 0)

    def get_values(self):
        last_row = self.find_last_row()
        # last_col = self.find_last_column() + 1  # needs '+1' because source code uses _cell_values[rowx][start_colx:end_colx]
        # self.values = [list(r) for r in self.ws._cell_values if r[0] is not None and self.asc_pattern.match(r[0])]
        if self.asc_filter["from"] is not None or self.asc_filter["to"] is not None:
            self.values = self.filter_by_asc(self.asc_filter["from"], self.asc_filter["to"])
        elif self.comment_filter != "":
            self.values = self.filter_by_comment(self.comment_filter)
        return self.values

    def get_asc_list(self):
        return self.ws["File"].tolist()

    def filter_by_comment(self, pattern):
        pattern = pattern.replace("*", "\\*")
        out = None
        try:
            out = self.ws[self.ws["Comment"].str.contains(pattern)]
            print(out)
        except Exception as e:
            print("ERROR")
            print(e)

        return out

    def filter_by_asc(self, start="", end=""):
        pat = re.compile(r"@(\d+)\.asc$")

        s_m = pat.search(start)
        e_m = pat.search(end)
        if s_m is None or e_m is None:
            return

        start_n = int(s_m.groups()[0])
        end_n = int(e_m.groups()[0])

        return self.ws[self.ws["n"].between(start_n, end_n)]

    def is_modified(self, val=None):
        if val is None:
            if self.values == []:
                self.get_values()
            else:
                val = self.values
        return not self.prev == val

    def modified_rows(self):
        out = []
        self.get_values()
        if self.is_modified():
            out = [r for r in range(len(self.values)) if r >= len(self.prev) or not self.prev[r] == self.values[r]]

        return out
