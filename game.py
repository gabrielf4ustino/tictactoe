import socket
import sys
import threading
import tkinter as tk
from tkinter import messagebox  # Import the messagebox module


# Class to represent the Tic-Tac-Toe game GUI
class TicTacToeGUI:
    def __init__(self, root, host, port, is_host):
        """
        Initialize the Tic-Tac-Toe GUI.
        :param root: Tkinter root window
        :param host: Server host address
        :param port: Server port number
        :param is_host: Boolean indicating if the current instance is the host
        """
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
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        threading.Thread(target=self.receive_data).start()

    def create_board_buttons(self):
        """
        Create buttons for Tic-Tac-Toe grid.
        """
        self.buttons = [[None, None, None] for _ in range(3)]
        for i in range(3):
            for j in range(3):
                self.buttons[i][j] = tk.Button(self.root, text='', font=('normal', 40), width=5, height=2,
                                               command=lambda i=i, j=j: self.on_button_click(i, j))
                self.buttons[i][j].grid(row=i, column=j)

    def on_button_click(self, i, j):
        """
        Handle button click event.
        :param i: Row index of the clicked button
        :param j: Column index of the clicked button
        """
        if self.buttons[i][j]['text'] == '' and self.you == self.current_player:
            move = f"{i},{j}"
            self.client.send(bytes(move, 'utf-8'))
            self.buttons[i][j]['text'] = self.you
            self.check_winner(self.you)
            self.current_player = self.opponent

    def receive_data(self):
        """
        Receive move data from the opponent.
        """
        while True:
            data = self.client.recv(1024).decode('utf-8')
            if not data:
                break
            move = data.split(',')
            row, col = int(move[0]), int(move[1])
            self.buttons[row][col]['text'] = self.opponent
            self.check_winner(self.opponent)
            self.current_player = self.you

    def check_winner(self, player):
        """
        Check if a player has won the game.
        :param player: Current player ('X' or 'O')
        :return: True if the player wins, False otherwise
        """
        # Check rows
        for row in range(3):
            if all([self.buttons[row][col]['text'] == player for col in range(3)]):
                messagebox.showinfo("Game Over", f"Player {player} wins!")
                self.on_closing()
                return True

        # Check columns
        for col in range(3):
            if all([self.buttons[row][col]['text'] == player for row in range(3)]):
                messagebox.showinfo("Game Over", f"Player {player} wins!")
                self.on_closing()
                return True

        # Check diagonals
        if all([self.buttons[i][i]['text'] == player for i in range(3)]) or \
                all([self.buttons[i][2 - i]['text'] == player for i in range(3)]):
            messagebox.showinfo("Game Over", f"Player {player} wins!")
            self.on_closing()
            return True

        # Check for a draw
        if all([self.buttons[i][j]['text'] != '' for i in range(3) for j in range(3)]):
            messagebox.showinfo("Game Over", "It's a draw!")
            self.on_closing()
            return True

        return False

    def on_closing(self):
        """
        Handle window closing event.
        """
        self.client.close()
        self.socket.close()
        self.root.destroy()


# Main function
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
