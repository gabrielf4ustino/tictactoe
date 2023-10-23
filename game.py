import socket
import sys
import threading
import tkinter as tk
from tkinter import messagebox


class TicTacToeGUI:
    def __init__(self, root, host, port, is_host):
        self.root = root
        self.root.title("Tic-Tac-Toe")
        self.host = host
        self.port = port
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        if is_host:
            self.socket.bind((host, port))
            self.socket.listen(1)
            self.client, self.address = self.socket.accept()
            self.you = 'X'
            self.opponent = 'O'
            self.current_player = self.you
        else:
            self.socket.connect((host, port))
            self.client = self.socket
            self.you = 'O'
            self.opponent = 'X'
            self.current_player = self.opponent
        self.create_board_buttons()
        self.create_scoreboard()
        self.create_exit_button()
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        threading.Thread(target=self.receive_data).start()

    def create_board_buttons(self):
        self.buttons = [[None, None, None] for _ in range(3)]
        for i in range(3):
            for j in range(3):
                self.buttons[i][j] = tk.Button(self.root, text='', font=('normal', 40), width=5, height=2,
                                               command=lambda i=i, j=j: self.on_button_click(i, j))
                self.buttons[i][j].grid(row=i, column=j)

    def create_scoreboard(self):
        self.player_x_wins = 0
        self.player_o_wins = 0
        self.label_player_x = tk.Label(self.root, text='Player X Wins: 0', font=('normal', 14))
        self.label_player_x.grid(row=3, column=0, columnspan=3)
        self.label_player_o = tk.Label(self.root, text='Player O Wins: 0', font=('normal', 14))
        self.label_player_o.grid(row=4, column=0, columnspan=3)

    def create_exit_button(self):
        self.exit_button = tk.Button(self.root, text='Exit Game', font=('normal', 14), command=self.on_closing)
        self.exit_button.grid(row=5, column=0, columnspan=3)

    def clear_board(self):
        for i in range(3):
            for j in range(3):
                self.buttons[i][j]['text'] = ''

    def on_button_click(self, i, j):
        if self.buttons[i][j]['text'] == '' and self.you == self.current_player:
            move = f"{i},{j}"
            self.client.send(bytes(move, 'utf-8'))
            self.buttons[i][j]['text'] = self.you
            if self.check_winner(self.you):
                self.update_scoreboard(self.you)
                self.clear_board()
            self.current_player = self.opponent

    def receive_data(self):
        while True:
            data = self.client.recv(1024).decode('utf-8')
            if not data or data == "exit":  # Se a mensagem for "exit", fecha a interface
                self.client.close()
                self.socket.close()
                self.root.destroy()
                break
            move = data.split(',')
            row, col = int(move[0]), int(move[1])
            self.buttons[row][col]['text'] = self.opponent
            if self.check_winner(self.opponent):
                self.update_scoreboard(self.opponent)
                self.clear_board()
            self.current_player = self.you

    def check_winner(self, player):
        for row in range(3):
            if all([self.buttons[row][col]['text'] == player for col in range(3)]):
                messagebox.showinfo("Game Over", f"Player {player} wins!")
                return True

        for col in range(3):
            if all([self.buttons[row][col]['text'] == player for row in range(3)]):
                messagebox.showinfo("Game Over", f"Player {player} wins!")
                return True

        if all([self.buttons[i][i]['text'] == player for i in range(3)]) or \
                all([self.buttons[i][2 - i]['text'] == player for i in range(3)]):
            messagebox.showinfo("Game Over", f"Player {player} wins!")
            return True

        if all([self.buttons[i][j]['text'] != '' for i in range(3) for j in range(3)]):
            messagebox.showinfo("Game Over", "It's a draw!")
            return True

        return False

    def update_scoreboard(self, player):
        if player == 'X':
            self.player_x_wins += 1
            self.label_player_x.config(text=f'Player X Wins: {self.player_x_wins}')
        elif player == 'O':
            self.player_o_wins += 1
            self.label_player_o.config(text=f'Player O Wins: {self.player_o_wins}')

    def on_closing(self):
        self.client.send(bytes("exit", 'utf-8'))  # Envia mensagem de saída para o outro jogador
        self.client.close()
        self.socket.close()
        self.root.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    host = sys.argv[2]
    port = int(sys.argv[3])

    param = sys.argv[1]
    if param == 'host':
        is_host = True
    elif param == 'client':
        is_host = False
    else:
        raise ValueError(f"Invalid parameter {param}")

    app = TicTacToeGUI(root, host, port, is_host)
    root.mainloop()
