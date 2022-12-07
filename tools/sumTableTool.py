import os
import re
import xlrd as xl

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

        self.asc_pattern = re.compile(r'^\d{8}@\d+\.asc$')

        self.asc_filter = {'from': None, 'to': None}
        self.comment_filter = ''

        self.load_workbook()

    def load_workbook(self):
        try:
            self.excel = xl.open_workbook(filename=self.path)
        except Exception:
            print('error on open_workbook // path: {}'.format(self.path))
            return None

        try:
            self.wb = self.excel
        except Exception:
            return None

        try:
            if 'Sum_table' in self.wb.sheet_names():
                self.ws = self.wb.sheet_by_name('Sum_table')
            elif 'Data' in self.wb.sheet_names():
                self.ws = self.wb.sheet_by_name('Data')
            else:
                raise ValueError('No appropriate worksheet.')
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
        return '$A${}'.format(self.find_last_row() + 1)
        # return self.excel.ActiveCell.Address

    def get_selected_value(self):
        last_row = self.find_last_row()
        try:
            return self.ws.cell_value(last_row + 1, 0)
        except IndexError:
            return ''
        # return self.excel.ActiveCell.Value

    def find_columns(self, labels, spreadsheet=True):
        headers = self.get_headers()
        offset = 0
        try:
            return [headers.index(l) + offset for l in labels]
        except ValueError:
            print('find_columns: Label Not Found')
            return None

    def find_last_row(self):
        return len(self.ws.col_values(0)) - 1

    def find_last_column(self):
        return len(self.get_headers()) - 1

    def get_headers(self):
        return self.ws.row_values(0, 0)

    def get_values(self):
        last_row = self.find_last_row()
        # last_col = self.find_last_column() + 1  # needs '+1' because source code uses _cell_values[rowx][start_colx:end_colx]
        self.values = [list(r) for r in self.ws._cell_values if r[0]
                       is not None and self.asc_pattern.match(r[0])]
        if self.asc_filter['from'] is not None or self.asc_filter['to'] is not None:
            self.values = self.filter_by_asc(
                self.asc_filter['from'], self.asc_filter['to'])
        elif self.comment_filter != '':
            print('comfil: ', self.comment_filter)
            self.values = self.filter_by_comment(self.comment_filter)
            print('value: ', self.values)
        return self.values

    def get_asc_list(self):
        if self.values == []:
            self.get_values()
        return [r[0] for r in self.values]

    def filter_by_comment(self, pattern):
        comm_col = self.find_columns(['Comment'])[0]
        pat = re.compile(pattern, re.I)
        if self.values == []:
            self.values = self.get_values()

        return [r for r in self.values if pat.search(r[comm_col])]

    def filter_by_asc(self, start=None, end=None):
        # start=None, end=None: All (from smallest to largest)
        # start=None, end=xxx: from smallest to xxx
        # start=xxx, end=None: from xxx to largest
        # start=xxx, end=yyy: from xxx to yyy
        if self.values == []:
            self.values = self.get_values()
        asc = [r[0] for r in self.values]
        rNum = len(self.values)
        if start is None:
            if end is None:
                return self.values
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
                return self.values
        except ValueError:
            return self.values

        return self.values[s_idx:e_idx + 1]

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
            out = [r for r in range(len(self.values)) if r >= len(
                self.prev) or not self.prev[r] == self.values[r]]

        return out
