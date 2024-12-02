import tkinter as tk
from tkinter import ttk
import numpy as np
import random as rnd
from threading import Thread
from queue import Queue

disk_color = ['white', 'red', 'orange']
disks = list()

player_type = ['human']
for i in range(42):
    player_type.append('AI: alpha-beta level ' + str(i + 1))

def alpha_beta_decision(board, turn, ai_level, queue, max_player):
    def alpha_beta(board, depth, alpha, beta, maximizing_player):
        if depth == 0 or board.check_victory() or turn >= 42:
            return board.eval(max_player)

        possible_moves = board.get_possible_moves()
        
        # Prioritize winning moves
        for move in possible_moves:
            new_board = board.copy()
            new_board.add_disk(move, max_player if maximizing_player else 3 - max_player, update_display=False)
            if new_board.check_victory():
                return float('inf') if maximizing_player else float('-inf')

        if maximizing_player:
            max_eval = float('-inf')
            for move in possible_moves:
                new_board = board.copy()
                new_board.add_disk(move, max_player, update_display=False)
                eval = alpha_beta(new_board, depth - 1, alpha, beta, False)
                max_eval = max(max_eval, eval)
                alpha = max(alpha, eval)
                if beta <= alpha:
                    break
            return max_eval
        else:
            min_eval = float('inf')
            for move in possible_moves:
                new_board = board.copy()
                new_board.add_disk(move, 3 - max_player, update_display=False)
                eval = alpha_beta(new_board, depth - 1, alpha, beta, True)
                min_eval = min(min_eval, eval)
                beta = min(beta, eval)
                if beta <= alpha:
                    break
            return min_eval

    # Find the best move using alpha-beta
    best_score = float('-inf')
    best_move = None
    for move in board.get_possible_moves():
        new_board = board.copy()
        new_board.add_disk(move, max_player, update_display=False)
        score = alpha_beta(new_board, ai_level, float('-inf'), float('inf'), False)
        if score > best_score:
            best_score = score
            best_move = move

    queue.put(best_move)

class Board:
    def __init__(self):
        self.grid = np.zeros((6, 7), dtype=int)

    def eval(self, player):
        score = 0
        opponent = 3 - player

        def count_alignments(line):
            score = 0
            for i in range(len(line) - 3):
                window = line[i:i + 4]
                if np.count_nonzero(window == player) == 4:
                    score += 10000  # Winning condition
                elif np.count_nonzero(window == player) == 3 and np.count_nonzero(window == 0) == 1:
                    score += 100  # Three aligned and one empty
                elif np.count_nonzero(window == player) == 2 and np.count_nonzero(window == 0) == 2:
                    score += 10  # Two aligned and two empty
                if np.count_nonzero(window == opponent) == 3 and np.count_nonzero(window == 0) == 1:
                    score -= 100  # Block opponent
            return score

        # Check rows, columns, and diagonals
        for row in self.grid:
            score += count_alignments(row)
        for col in self.grid.T:
            score += count_alignments(col)
        for offset in range(-2, 4):  # Diagonal offsets
            score += count_alignments(self.grid.diagonal(offset))
            score += count_alignments(np.fliplr(self.grid).diagonal(offset))

        return score

    def copy(self):
        new_board = Board()
        new_board.grid = np.copy(self.grid)
        return new_board

    def reinit(self):
        self.grid.fill(0)
        for col in range(7):
            for row in range(6):
                canvas1.itemconfig(disks[col][row], fill=disk_color[0])


    def get_possible_moves(self):
        possible_moves = []
        for col in range(7):
            if self.grid[0][col] == 0:
                possible_moves.append(col)
        return possible_moves

    def add_disk(self, column, player, update_display=True):
        for row in range(5, -1, -1):  # Remplir du bas vers le haut
            if self.grid[row][column] == 0:
                self.grid[row][column] = player
                if update_display:
                    canvas1.itemconfig(disks[column][5 - row], fill=disk_color[player])
                break


    def column_filled(self, column):
        print(f"Vérification de la colonne {column}: {self.grid[0][column]}")
        return self.grid[0][column] != 0




    def check_victory(self):
        # Horizontal alignment check
        for row in range(6):
            for col in range(4):
                if self.grid[row][col] == self.grid[row][col + 1] == self.grid[row][col + 2] == self.grid[row][col + 3] != 0:
                    return True
        # Vertical alignment check
        for col in range(7):
            for row in range(3):
                if self.grid[row][col] == self.grid[row + 1][col] == self.grid[row + 2][col] == self.grid[row + 3][col] != 0:
                    return True
        # Diagonal alignment check
        for row in range(3):
            for col in range(4):
                if self.grid[row][col] == self.grid[row + 1][col + 1] == self.grid[row + 2][col + 2] == self.grid[row + 3][col + 3] != 0:
                    return True
                if self.grid[row + 3][col] == self.grid[row + 2][col + 1] == self.grid[row + 1][col + 2] == self.grid[row][col + 3] != 0:
                    return True
        return False
    
    def is_draw(self):
        return not np.any(self.grid == 0)  # Retourne True si toutes les cases sont non nulles


class Connect4:
    def __init__(self):
        self.board = Board()
        self.human_turn = False
        self.turn = 1
        self.players = (0, 0)
        self.ai_move = Queue()

    def current_player(self):
        return 2 - (self.turn % 2)

    def launch(self):
        self.board.reinit()
        self.turn = 0
        information['fg'] = 'black'
        information['text'] = "Turn " + str(self.turn) + " - Player " + str(self.current_player()) + " is playing"
        self.human_turn = False
        self.players = (combobox_player1.current(), combobox_player2.current())
        self.handle_turn()

    def move(self, column):
        if not self.board.column_filled(column):
            self.board.add_disk(column, self.current_player())
            self.handle_turn()

    def click(self, event):
        if self.human_turn:
            column = event.x // row_width
            self.move(column)

    def ai_turn(self, ai_level):
        Thread(target=alpha_beta_decision, args=(self.board, self.turn, ai_level, self.ai_move, self.current_player(),)).start()
        self.ai_wait_for_move()

    def ai_wait_for_move(self):
        if not self.ai_move.empty():
            self.move(self.ai_move.get())
        else:
            window.after(100, self.ai_wait_for_move)

    def handle_turn(self):
        self.human_turn = False
        if self.board.check_victory():
            information['fg'] = 'red'
            information['text'] = "Player " + str(self.current_player()) + " wins!"
            return
        elif self.board.is_draw():  # Vérifie si le match est nul
            information['fg'] = 'red'
            information['text'] = "This is a draw!"
            return
        self.turn += 1
        information['text'] = "Turn " + str(self.turn) + " - Player " + str(self.current_player()) + " is playing"
        if self.players[self.current_player() - 1] != 0:
            self.human_turn = False
            self.ai_turn(self.players[self.current_player() - 1])
        else:
            self.human_turn = True


game = Connect4()

# Graphical settings
width = 700
row_width = width // 7
row_height = row_width
height = row_width * 6
row_margin = row_height // 10

window = tk.Tk()
window.title("Connect 4")
canvas1 = tk.Canvas(window, bg="blue", width=width, height=height)

# Drawing the grid
for i in range(7):
    disks.append(list())
    for j in range(6):
        disks[i].append(canvas1.create_oval(row_margin + i * row_width, row_margin + (5 - j) * row_height, (i + 1) * row_width - row_margin,
                            (6 - j) * row_height - row_margin, fill='white'))

canvas1.grid(row=0, column=0, columnspan=2)

information = tk.Label(window, text="")
information.grid(row=1, column=0, columnspan=2)

label_player1 = tk.Label(window, text="Player 1: ")
label_player1.grid(row=2, column=0)
combobox_player1 = ttk.Combobox(window, state='readonly')
combobox_player1.grid(row=2, column=1)

label_player2 = tk.Label(window, text="Player 2: ")
label_player2.grid(row=3, column=0)
combobox_player2 = ttk.Combobox(window, state='readonly')
combobox_player2.grid(row=3, column=1)

combobox_player1['values'] = player_type
combobox_player1.current(0)
combobox_player2['values'] = player_type
combobox_player2.current(6)

button2 = tk.Button(window, text='New game', command=game.launch)
button2.grid(row=4, column=0)

button = tk.Button(window, text='Quit', command=window.destroy)
button.grid(row=4, column=1)

# Mouse handling
canvas1.bind('<Button-1>', game.click)

window.mainloop()