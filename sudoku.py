import numpy as np
import itertools
import time

class Sudoku:
    def __init__(self, file_name):
        self.board = np.genfromtxt(fname=file_name, delimiter=',', dtype='int8')
        self.initial_board = self.board.copy()

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
        """Creates an imag of the sudoku board"""
        from PIL import Image, ImageDraw, ImageFont
        cell_size = 50
        cell_border = 3
        block_border = 5
        num_size = 40
        initial_num_color = "blue"
        num_color = "black"
        cell_color = "white"
        background_color = "black"

        SIZE = 9*cell_size + 9*cell_border + 4*block_border
        img = Image.new(mode="RGBA", size=(SIZE, SIZE), color=background_color)
        draw = ImageDraw.Draw(img)

        for i, row in enumerate(self.board):
            for j, col in enumerate(row):
                draw.rectangle([
                    j*cell_size + block_border*(int(j/3)+1) + j*cell_border, i*cell_size + block_border*(int(i/3)+1) + i*cell_border,
                    (j+1)*cell_size + block_border*(int(j/3)+1) + j*cell_border, (i+1)*cell_size + block_border*(int(i/3)+1) + i*cell_border],
                    cell_color)

                font = ImageFont.truetype("OpenSans-Regular.ttf", num_size)
                w, h = draw.textsize(str(col), font)
                draw.text((
                    j*cell_size + block_border*(int(j/3)+1) + j*cell_border + ((cell_size - w) / 2),
                    i*cell_size + block_border*(int(i/3)+1) + i*cell_border + ((cell_size - h) / 4)),
                str(col), fill=num_color if self.initial_board[i,j] == 0 else initial_num_color, font=font)        

        img.save(file_name)

class Solver():
    def __init__(self, file_name):
        self.sudoku = Sudoku(file_name)
        self.candidates = dict()
        self.solve()

    def update_candidates(self):
        """Updates a dictionary mapping unassigned cells to the possible values they could take"""
        if self.candidates:
            self.candidates = {index:[i for i in self.sudoku.get_values(index) if i in self.candidates[index]] for index in self.sudoku.get_unassigned_indices()}
        else:
            self.candidates = {index:self.sudoku.get_values(index) for index in self.sudoku.get_unassigned_indices()}

    def check_naked_single(self):
        """Checks for naked singles and updates the board if one is found. Returns `True` if changes were made else `False`"""
        revised = True
        changes_made = False
        while revised:
            revised = False
            for index, candidate in self.candidates.items():
                if len(candidate) == 1:
                    self.sudoku.board[index[0], index[1]] = candidate[0]
                    self.update_candidates()
                    revised = True
                    changes_made = True
            self.update_candidates()

        return changes_made

    def check_hidden_single(self):
        """Checks for hidden singles and updates the board if one is found. Returns `True` if changes were made else `False`"""
        revised = True
        changes_made = False

        def check_hidden(cells):
            in_revised = False
            check = {i:list() for i in range(1,10)}
            for cell in cells:
                for d in self.candidates[cell]:
                    check[d].append(cell)
            for key, value in check.items():
                if len(value) == 1 and value[0] in self.candidates.keys():
                    self.sudoku.board[value[0]] = key
                    self.candidates.pop(value[0])
                    self.update_candidates()
                    in_revised = True
            return in_revised
        
        while revised:
            revised = False
            for area_9x9 in [(i,j) for i in range(3) for j in range(3)]:
                revised = False if not check_hidden(self.sudoku.get_9x9_indices(area_9x9)) and not revised else True
            for i in range(9):
                revised = False if not check_hidden([(i, j) for j in range(9) if self.sudoku.board[i,j] == 0]) and not revised else True
                revised = False if not check_hidden([(j, i) for j in range(9) if self.sudoku.board[j,i] == 0]) and not revised else True
            if revised:
                changes_made = True
        return changes_made

    def check_naked_candidates(self, n):
        """Checks for naked pairs and updates the candidates is one is found. Returns `True` if changes were made else `False`"""
        revised = True
        changes_made = False

        def check_naked(cells):
            in_revised = False
            for cell in cells:
                if len(self.candidates[cell]) != n:
                    continue
                cells_with_same_candidate = self.get_cells_with_candidate(self.candidates[cell], cells)
                if len(cells_with_same_candidate) == n:
                    for c in [i for i in cells if i not in cells_with_same_candidate]:
                        for to_remove in self.candidates[cell]:
                            try:
                                self.candidates[c].remove(to_remove)
                                in_revised = True
                            except:
                                pass
            return in_revised

        while revised:
            revised = False
            for area_9x9 in [(i,j) for i in range(3) for j in range(3)]:
                revised = False if not check_naked(self.sudoku.get_9x9_indices(area_9x9)) and not revised else True
            for i in range(9):
                revised = False if not check_naked([(i, j) for j in range(9) if self.sudoku.board[i,j] == 0]) and not revised else True
                revised = False if not check_naked([(j, i) for j in range(9) if self.sudoku.board[j,i] == 0]) and not revised else True
            if revised:
                changes_made = True
        return changes_made

    def check_hidden_candidates(self, n):
        """Checks for hidden pairs and updates the candidates if one is found. Returns `True` if changes were made else `False`"""
        revised = True
        changes_made = False

        def check_hidden(cells):
            in_revised = False
            check = {i:set() for i in itertools.combinations(range(1,10), n)}
            for combination in check.items():
                for cell in cells:
                    if any(True if i in self.candidates[cell] else False for i in combination[0]):
                        check[combination[0]].add(cell)

            for combination, c in check.items():
                if len(c) == n and len(set([j for i in c for j in self.candidates[i] if j in combination])) == n:
                    for cell in c:
                        a = sorted(self.candidates[cell])
                        self.candidates[cell] = [i for i in self.candidates[cell] if i in combination]
                        if a != sorted(self.candidates[cell]):
                            in_revised = True
            return in_revised

        while revised:
            revised = False
            for area_9x9 in [(i,j) for i in range(3) for j in range(3)]:
                revised = False if not check_hidden(self.sudoku.get_9x9_indices(area_9x9)) and not revised else True
            for i in range(9):
                revised = False if not check_hidden([(i, j) for j in range(9) if self.sudoku.board[i,j] == 0]) and not revised else True
                revised = False if not check_hidden([(j, i) for j in range(9) if self.sudoku.board[j,i] == 0]) and not revised else True
            if revised:
                changes_made = True
    
        return changes_made

    def check_all_pointing(self):
        """Checks for pointing pairs and triples and updates the board if one is found. Returns `True` if changes were made else `False`"""
        revised = True
        changes_made = False

        def check_pointing(cells):
            in_revised = False
            check = {i:{"rows":set(), "cols":set()} for i in range(1, 10)}
            check_candidate = {i:set() for i in range(1, 10)}
            for cell in cells:
                for d in self.candidates[cell]:
                    check[d]["rows"].add(cell[0])
                    check[d]["cols"].add(cell[1])
                    check_candidate[d].add(cell)
            tmp = ("rows", "cols")
            for i in range(2):
                for d, row_cols in check.items():
                    if not row_cols[tmp[i]]:
                        continue
                    if len(row_cols[tmp[i]]) == 1:
                        rc = row_cols[tmp[i]].pop()
                        if i == 0:
                            for j in range(9):
                                if (rc, j) in self.candidates.keys() and (rc, j) not in cells:
                                    try:
                                        self.candidates[rc, j].remove(d)
                                        in_revised = True
                                    except:
                                        pass
                            if len(set([int(k[1] / 3) for k in check_candidate[d] if k[0] == rc])) == 1:
                                pointing_cells = [k for k in check_candidate[d] if k[0] == rc]
                                for c in self.sudoku.get_9x9_indices((int(rc / 3), int(pointing_cells[0][1] / 3))):
                                    if c not in pointing_cells:
                                        try:
                                            self.candidates[c].remove(d)
                                            in_revised = True
                                        except:
                                            pass

                        else:
                            for j in range(9):
                                if (j, rc) in self.candidates.keys() and (j, rc) not in cells:
                                    try:
                                        self.candidates[j, rc].remove(d)
                                        in_revised = True
                                    except:
                                        pass

                            if len(set([int(k[0] / 3) for k in check_candidate[d] if k[1] == rc])) == 1:
                                pointing_cells = [k for k in check_candidate[d] if k[1] == rc]
                                for c in self.sudoku.get_9x9_indices((int(pointing_cells[0][0] / 3), int(rc / 3))):
                                    if c not in pointing_cells:
                                        try:
                                            self.candidates[c].remove(d)
                                            in_revised = True
                                        except:
                                            pass
                        
            return in_revised

        while revised:
            revised = False
            for i in range(9):
                revised = False if not check_pointing([(i, j) for j in range(9) if self.sudoku.board[i,j] == 0]) and not revised else True
                revised = False if not check_pointing([(j, i) for j in range(9) if self.sudoku.board[j,i] == 0]) and not revised else True
            if revised:
                changes_made = True
        return changes_made

    def check_all_hidden(self):
        """Checks for hidden singles, pairs, triples, quad. Returns `True` if changes were made else `False`"""
        changes_made = []
        changes_made.append(self.check_hidden_single())
        for i in range(2,5):
            changes_made.append(self.check_hidden_candidates(i))

        return any(changes_made)

    def check_all_naked(self):
        """Checks for naked singles, pairs, triples, quad. Returns `True` if changes were made else `False`"""
        changes_made = []
        changes_made.append(self.check_naked_single())
        for i in range(2,5):
            changes_made.append(self.check_naked_candidates(i))

        return any(changes_made)

    def get_cells_with_candidate(self, candidate, cells):
        """Returns the cells with candidate `candidate` in `cells`"""
        same_cells = []
        for cell in cells:
            if cell in self.candidates.keys() and self.candidates[cell] == candidate:
                same_cells.append(cell)

        return same_cells
        
    def solve(self):
        """Solves the sudoku if it has a solution"""
        changes = [True]
        while any(changes):
            changes = []
            changes.extend([
                self.check_all_naked(),
                self.check_all_hidden(),
                self.check_all_pointing()
            ])

        if self.sudoku.is_complete() and self.sudoku.is_consistent():
            print("Solution Found")
            self.sudoku.pretty_print()
            self.sudoku.output_img()

        else:
            print("The current version of the program cannot solve the sudoku")

a = time.time_ns()
s = Solver("sudokus/sudoku3.txt")
b = time.time_ns()
print(f"Time: {(b-a)/1000000}")