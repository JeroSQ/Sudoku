import numpy as np
import time

class Sudoku:
    def __init__(self, file_name):
        self.board = np.genfromtxt(fname=file_name, delimiter=',', dtype='int8')

    def get_row(self, row, assigned=True):
       """Returns the values in row `row`"""
       a = self.board[row]
       if assigned:
        return a[a != 0]
       return a[a == 0]

    def get_col(self, col, assigned=True):
        """Returns the values in column `col`""" 
        a = self.board[:,col]
        if assigned:
            return a[a != 0]
        return a[a == 0]

    def get_9x9(self, pos, assigned=True):
        """Returns the values in the 9x9 area in which the cell with position `pos` is""" 
        row, col = pos
        row_9x9, col_9x9 = int(row / 3), int(col / 3)

        a = self.board[row_9x9*3:row_9x9*3+3, col_9x9*3:col_9x9*3+3].flatten()
        if assigned:
            return a[a != 0]
        return a[a == 0]

    def get_9x9_indices(self, pos_9x9, assigned=False):
        """Returns the indices of the cells in a 9x9 area"""
        if assigned:
            return [(i,j) for i in range(pos_9x9[0]*3, pos_9x9[0]*3+3) for j in range(pos_9x9[1]*3, pos_9x9[1]*3+3) if self.board[i,j] != 0]
        return [(i,j) for i in range(pos_9x9[0]*3, pos_9x9[0]*3+3) for j in range(pos_9x9[1]*3, pos_9x9[1]*3+3) if self.board[i,j] == 0]

    def get_values(self, pos, assigned=True):
        """Returns the values that the cell with position `pos` can/cannot take according to the current assigned values"""
        return [i for i in range(1, 10) if i not in np.hstack((self.get_row(pos[0], assigned), self.get_col(pos[1], assigned), self.get_9x9(pos, assigned)))]

    def get_unassigned_indices(self):
        """Returns the indices of the cells that have not been assigned a value yet"""
        return [(i,j) for i in range(9) for j in range(9) if self.board[i,j] == 0]

    def is_consistent(self):
        """Returns  `True` if the sudoku is consistent `False`"""
        for i, j in [(i,j) for i in range(9) for j in range(9) if self.board[i,j] != 0]:
            value = self.board[i,j]
            if value not in self.get_values((i,j), assigned=False):
                return False
        return True

    def is_complete(self):
        """Returns `True` if the sudoku is complete else `False`"""
        return all(i != 0 for i in self.board.flatten())

    def pretty_print(self):
        """Prints the sudoku board in the terminal"""
        def print_line_sep():
            print("+-+-+-+-+-+-+-+-+-+-+-+-+")
        print_line_sep()
        for j, row in enumerate(self.board):
            print("| ", end="")
            for i, col in enumerate(row):
                print(f"{col} ",end="")
                if (i+1) % 3 == 0:
                    print("| ", end="")
            print("\n", end="")
            if (j+1) % 3 == 0:
                print_line_sep()

    def output_img(self, file_name="sudoku.png"):
        """Creates an image of the sudoku board"""
        from PIL import Image, ImageDraw
        pass

class Solver():
    def __init__(self, file_name):
        self.sudoku = Sudoku(file_name)
        self.domains = dict()
        self.solve()

    def update_domains(self):
        """Updates a dictionary mapping unassigned cells to the possible values they could take"""
        if self.domains:
            self.domains = {index:[i for i in self.sudoku.get_values(index) if i in self.domains[index]] for index in self.sudoku.get_unassigned_indices()}
        else:
            self.domains = {index:self.sudoku.get_values(index) for index in self.sudoku.get_unassigned_indices()}

    def check_only_option(self):
        """Checks if there's only one domain in a 9x9 area that contains a value and updates the board if there is. Returns `True` if changes were made else `False`"""
        revised = True
        changes_made = False
        while revised:
            revised = False
            for area_9x9 in [(i,j) for i in range(3) for j in range(3)]:
                cells = self.sudoku.get_9x9_indices(area_9x9)
                check = {i:list() for i in range(1,10)}
                for cell in cells:
                    for d in self.domains[cell]:
                        check[d].append(cell)
                for key, value in check.items():
                    if len(value) == 1:# and value[0] in self.domains.keys():
                        self.sudoku.board[value[0]] = key
                        self.domains.pop(value[0])
                        self.update_domains()
                        revised = True
                        changes_made = True
            
    def check_unique_candidates(self):
        """Checks if a cell's domain has only one value and updates the board if it has. Returns `True` if changes were made else `False`"""
        revised = True
        changes_made = False
        while revised:
            revised = False
            for index, domain in self.domains.items():
                if len(domain) == 1:
                    self.sudoku.board[index[0], index[1]] = domain[0]
                    self.update_domains()
                    revised = True
                    changes_made = True
            self.update_domains()

        return changes_made

    def check_double_candidates(self):
        """Checks if 2 cells share the same domain and updates the domains if they do. Returns `True` if changes were made else `False`"""
        revised = True
        changes_made = False
        while revised:
            revised = False
            for area_9x9 in [(i,j) for i in range(3) for j in range(3)]:
                cells = self.sudoku.get_9x9_indices(area_9x9)
                for cell in cells:
                    if len(self.domains[cell]) != 2:
                        continue
                    cells_with_same_domain = self.get_cells_with_domain(self.domains[cell], area_9x9)
                    if len(cells_with_same_domain) == 2:
                        for c in [i for i in cells if i not in cells_with_same_domain]:
                            try:
                                if self.domains[cell][0] in self.domains[c]:
                                    self.domains[c].remove(self.domains[cell][0])
                                    revised = True
                                    changes_made = True
                                self.domains[c].remove(self.domains[cell][1])
                                revised = True
                                changes_made = True
                            except:
                                pass
        return changes_made

    def check_inline_candidates(self):
        """Checks if a domain value is only present in a row or col and updates the domains if they are. Returns `True` if changes were made else `False`"""
        revised = True
        changes_made = False
        while revised:
            revised = False
            for area_9x9 in [(i,j) for i in range(3) for j in range(3)]:
                cells = self.sudoku.get_9x9_indices(area_9x9)
                check = {i:{"rows":set(), "cols":set()} for i in range(1, 10)}
                for cell in cells:
                    for d in self.domains[cell]:
                        check[d]["rows"].add(cell[0])
                        check[d]["cols"].add(cell[1])
                tmp = ("rows", "cols")
                for i in range(2):
                    for d, row_cols in check.items():
                        if not row_cols[tmp[i]]:
                            continue
                        if len(row_cols[tmp[i]]) == 1:
                            rc = row_cols[tmp[i]].pop()
                            if i == 0:
                                for j in range(9):
                                    if (rc, j) in self.domains.keys() and (rc, j) not in cells:
                                        try:
                                            self.domains[rc, j].remove(d)
                                            revised = True
                                            changes_made = True
                                        except:
                                            pass
                            else:
                                for j in range(9):
                                    if (j, rc) in self.domains.keys() and (j, rc) not in cells:
                                        try:
                                            self.domains[j, rc].remove(d)
                                            revised = True
                                            changes_made = True
                                        except:
                                            pass

            time.sleep(0.1)

        return changes_made

    def get_cells_with_domain(self, domain, area_9x9):
        """Returns the cells with domain `domain` in `area_9x9`"""
        cells = []
        for cell in self.sudoku.get_9x9_indices(area_9x9):
            if cell in self.domains.keys() and self.domains[cell] == domain:
                cells.append(cell)

        return cells
        
    def solve(self):
        """Solves the sudoku if it has a solution"""
        changes = [True]
        self.sudoku.pretty_print()
        while any(changes):
            self.update_domains()
            changes = []
            changes.extend([
                self.check_unique_candidates(),
                self.check_double_candidates(),
                self.check_only_option(),
                self.check_inline_candidates()])

        if self.sudoku.is_complete() and self.sudoku.is_consistent():
            print("Solution Found")
            self.sudoku.pretty_print()
            self.sudoku.output_img()

        else:
            print("The current version of the program cannot solve the sudoku")

s = Solver("sudoku/sudoku.txt")