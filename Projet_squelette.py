import tkinter as tk
from tkinter import ttk
import numpy as np
import random as rnd
from threading import Thread
from queue import Queue
from threading import Lock

disk_color = ['white', 'red', 'orange']
disks = list()

player_type = ['human']
for i in range(42):
    player_type.append('AI: alpha-beta level ' + str(i + 1))

def alpha_beta_decision(board, turn, ai_level, queue, max_player):
    def alpha_beta(board, depth, alpha, beta, maximizing_player):
        if depth == 0 or board.check_victory() or board.is_draw():
            return board.eval(max_player)

        possible_moves = board.get_possible_moves()

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

    possible_moves = board.get_possible_moves()

    # 1. Prioriser les coups gagnants immédiats
    for move in possible_moves:
        new_board = board.copy()
        new_board.add_disk(move, max_player, update_display=False)
        if new_board.check_victory():
            queue.put(move)
            return

    # 2. Prioriser les blocages de victoire immédiats de l'adversaire
    for move in possible_moves:
        new_board = board.copy()
        new_board.add_disk(move, 3 - max_player, update_display=False)
        if new_board.check_victory():
            queue.put(move)
            return

    # 3. Évaluer tous les autres coups via Alpha-Bêta
    best_score = float('-inf')
    best_move = None
    for move in possible_moves:
        new_board = board.copy()
        new_board.add_disk(move, max_player, update_display=False)
        score = alpha_beta(new_board, ai_level, float('-inf'), float('inf'), False)
        if score > best_score:
            best_score = score
            best_move = move

    if best_move is not None:
        queue.put(best_move)
    else:
        queue.put(rnd.choice(possible_moves))  # Fallback si aucun meilleur coup



class Board:
    def __init__(self):
        self.grid = np.zeros((6, 7), dtype=int)

    def eval(self, player):
        opponent = 3 - player  # L'adversaire
        score = 0

        def evaluate_window(window):
            player_count = window.count(player)
            opponent_count = window.count(opponent)
            empty_count = window.count(0)

            if player_count == 4:  # Victoire pour le joueur
                return 10000
            elif player_count == 3 and empty_count == 1:
                return 100  # Menace à 3 jetons
            elif player_count == 2 and empty_count == 2:
                return 10  # Menace faible

            if opponent_count == 4:  # Victoire pour l'adversaire
                return -10000
            elif opponent_count == 3 and empty_count == 1:
                return -200  # Blocage nécessaire
            elif opponent_count == 2 and empty_count == 2:
                return -10  # Alignement faible adversaire

            return 0

        # Parcourir toutes les fenêtres possibles
        for row in self.grid:
            for col in range(4):
                score += evaluate_window(list(row[col:col + 4]))

        for col in self.grid.T:
            for row in range(3):
                score += evaluate_window(list(col[row:row + 4]))

        for offset in range(-2, 4):
            score += sum(evaluate_window(list(self.grid.diagonal(offset)[i:i + 4]))
                        for i in range(len(self.grid.diagonal(offset)) - 3))
            score += sum(evaluate_window(list(np.fliplr(self.grid).diagonal(offset)[i:i + 4]))
                        for i in range(len(np.fliplr(self.grid).diagonal(offset)) - 3))

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
        return self.grid[0][column] != 0

    def check_victory(self):
        # Horizontal alignment check
        for row in range(6):
            for col in range(4):
                if self.grid[row][col] == self.grid[row][col + 1] == self.grid[row][col + 2] == self.grid[row][col + 3] != 0:
                    #print(f"Horizontal win detected at row {row}, starting col {col}")
                    return True
        # Vertical alignment check
        for col in range(7):
            for row in range(3):
                if self.grid[row][col] == self.grid[row + 1][col] == self.grid[row + 2][col] == self.grid[row + 3][col] != 0:
                    #print(f"Vertical win detected at col {col}, starting row {row}")
                    return True
        # Diagonal alignment check
        for row in range(3):
            for col in range(4):
                if self.grid[row][col] == self.grid[row + 1][col + 1] == self.grid[row + 2][col + 2] == self.grid[row + 3][col + 3] != 0:
                    #print(f"Diagonal win detected from top-left at row {row}, col {col}")
                    return True
                if self.grid[row + 3][col] == self.grid[row + 2][col + 1] == self.grid[row + 1][col + 2] == self.grid[row][col + 3] != 0:
                    #print(f"Diagonal win detected from bottom-left at row {row + 3}, col {col}")
                    return True
        return False

    
    def is_draw(self):
        return not np.any(self.grid == 0)  # Retourne True si toutes les cases sont non nulles


class Connect4:
    def __init__(self):
        self.board = Board()
        self.lock = Lock()
        self.human_turn = False
        self.turn = 1
        self.players = (0, 0)
        self.ai_move = Queue()
        self.ai_thread_running = False

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
            if self.board.check_victory():
                #print(f"Player {self.current_player()} wins!")
                information['fg'] = 'red'
                information['text'] = f"Player {self.current_player()} wins!"
                return
            elif self.board.is_draw():
                #print("It's a draw!")
                information['fg'] = 'red'
                information['text'] = "It's a draw!"
                return
            self.handle_turn()
        else:
            print("Column is filled, choose another one.")

    def click(self, event):
        if self.human_turn:
            column = event.x // row_width
            self.move(column)

    def ai_turn(self, ai_level):
        if self.ai_thread_running:
            return
        self.ai_thread_running = True
        Thread(target=self._run_ai, args=(ai_level,)).start()

    def _run_ai(self, ai_level):
        with self.lock:  # Verrouiller l'accès au plateau
            alpha_beta_decision(self.board, self.turn, ai_level, self.ai_move, self.current_player())
        self.ai_thread_running = False
        self.ai_wait_for_move()

    def ai_wait_for_move(self):
        if not self.ai_move.empty():
            column = self.ai_move.get()
            if column is not None and column in self.board.get_possible_moves():
                self.move(column)
            else:
                information['fg'] = 'red'
                information['text'] = f"Error: Invalid move by AI. Ending game."
        else:
            window.after(100, self.ai_wait_for_move)


    def handle_turn(self):
        self.human_turn = False
        if self.board.check_victory():
            information['fg'] = 'red'
            information['text'] = "Player " + str(self.current_player()) + " wins!"
            return
        elif self.board.is_draw():
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