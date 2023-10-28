import socket
import threading
import tkinter as tk
from tkinter import messagebox

# Initialize game-related variables
game_init = False
game_host = None
game_port = None
game_is_host = None
name_you = None
name_opponent = None
should_close_game = False
host_server = 'localhost'
port_server = 1024
playing = False


class TicTacToeGUI:
    def __init__(self, host_client, port_client, is_host, name_you, name_opponent):
        # Initialize GUI elements and game settings
        self.name_you = name_you
        self.name_opponent = name_opponent
        self.exit_button = None
        self.label_player_o = None
        self.label_player_x = None
        self.buttons = None
        self.player_o_wins = None
        self.player_x_wins = None
        self.root = tk.Tk()
        self.root.title("Tic-Tac-Toe")
        self.host = host_client
        self.port = port_client
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # Set up server/client based on the is_host flag
        if is_host:
            self.socket.bind((host_client, port_client))
            self.socket.listen(1)
            self.client, self.address = self.socket.accept()
            self.you = 'X'
            self.opponent = 'O'
            self.current_player = self.you
        else:
            self.socket.connect((host_client, port_client))
            self.client = self.socket
            self.you = 'O'
            self.opponent = 'X'
            self.current_player = self.opponent
        # Create game board buttons and GUI elements
        self.create_board_buttons()
        self.create_scoreboard()
        self.create_exit_button()
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        threading.Thread(target=self.receive_data_from_opponent).start()
        self.root.mainloop()
        global game_init, host_server, port_server
        game_init = False

        if is_host:
            self.socket_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket_server.connect((host_server, port_server))
            self.client_server = self.socket_server
            self.client_server.send(bytes(f"GAME_OVER {self.name_you} {self.name_opponent}", 'utf-8'))

    def create_board_buttons(self):
        # Create the Tic-Tac-Toe game board buttons
        self.buttons = [[None, None, None] for _ in range(3)]
        for i in range(3):
            for j in range(3):
                self.buttons[i][j] = tk.Button(self.root, text='', font=('normal', 40), width=5, height=2,
                                               command=lambda i=i, j=j: self.on_button_click(i, j))
                self.buttons[i][j].grid(row=i, column=j)

    def create_scoreboard(self):
        # Create and initialize the player score labels
        self.player_x_wins = 0
        self.player_o_wins = 0
        self.label_player_x = tk.Label(self.root,
                                       text=f'Player X ({'You' if self.you == 'X' else self.name_opponent}) Wins: 0',
                                       font=('normal', 14))
        self.label_player_x.grid(row=3, column=0, columnspan=3)
        self.label_player_o = tk.Label(self.root,
                                       text=f'Player O ({'You' if self.you == 'O' else self.name_opponent}) Wins: 0',
                                       font=('normal', 14))
        self.label_player_o.grid(row=4, column=0, columnspan=3)

    def create_exit_button(self):
        # Create an exit button to gracefully exit the game
        self.exit_button = tk.Button(self.root, text='Exit Game', font=('normal', 14), command=self.on_closing)
        self.exit_button.grid(row=5, column=0, columnspan=3)

    def clear_board(self):
        # Clear the game board (reset buttons)
        for i in range(3):
            for j in range(3):
                self.buttons[i][j]['text'] = ''

    def on_button_click(self, i, j):
        # Handle a button click event, make a move
        if self.buttons[i][j]['text'] == '' and self.you == self.current_player:
            move = f"{i},{j}"
            self.client.send(bytes(move, 'utf-8'))
            self.buttons[i][j]['text'] = self.you
            if self.check_winner(self.you):
                self.update_scoreboard(self.you)
                self.clear_board()
            self.current_player = self.opponent

    def receive_data_from_opponent(self):
        # Receive moves from the opponent and update the game board
        try:
            while True:
                global should_close_game
                if should_close_game:
                    self.on_closing()
                data = self.client.recv(1024).decode('utf-8')
                move = data.split(',')
                row, col = int(move[0]), int(move[1])
                self.buttons[row][col]['text'] = self.opponent
                if self.check_winner(self.opponent):
                    self.update_scoreboard(self.opponent)
                    self.clear_board()
                self.current_player = self.you
        except (ConnectionResetError, ConnectionAbortedError):
            print("Opponent disconnected.")
            self.on_closing()

    def check_winner(self, player):
        # Check if the player has won or if it's a draw
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
            self.clear_board()
            return False

        return False

    def update_scoreboard(self, player):
        # Update the player's score on the scoreboard
        if player == 'X':
            self.player_x_wins += 1
            self.label_player_x.config(
                text=f'Player X ({'You' if self.you == 'X' else self.name_opponent}) Wins: {self.player_x_wins}')

        elif player == 'O':
            self.player_o_wins += 1
            self.label_player_o.config(
                text=f'Player O ({'You' if self.you == 'O' else self.name_opponent}) Wins: {self.player_o_wins}')

    def on_closing(self):
        # Handle the closing of the game window
        global playing
        playing = False
        self.client.close()
        self.socket.close()
        self.root.destroy()
        print("Your game has ended.")


class ServerCommunication:
    def __init__(self):
        try:
            global host_server, port_server
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((host_server, port_server))
            self.client = self.socket
        except ConnectionRefusedError:
            print("Server is not available.")
            exit(1)

    def receive_data_from_server(self):
        # Receive and process data from the server
        while True:
            try:
                data = self.client.recv(1024).decode('utf-8').strip()
                if not data or data == "exit":
                    print("You have been disconnected from the server.")
                    break
                print(data)
                if data.startswith("GAME_ACK"):
                    global should_close_game, playing
                    if playing:
                        should_close_game = True
                    _, opponent_host, opponent_port, is_host, you, opponent = data.split(" ")
                    if is_host == "host":
                        is_host = True
                    else:
                        is_host = False
                    global game_init, game_host, game_port, game_is_host, name_you, name_opponent
                    game_host = opponent_host
                    game_port = int(opponent_port)
                    game_is_host = is_host
                    name_you = you
                    name_opponent = opponent
                    playing = True
                    game_init = True
                elif data.startswith("GAME_NEG"):
                    print("Game request denied.")
            except ConnectionResetError:
                print("Server disconnected.")
                break

    def send_data_to_server(self):
        # Send data to the server
        while True:
            try:
                data = input()
                if data == "EXIT":
                    self.client.send(bytes(data, 'utf-8'))
                    break
                else:
                    self.client.send(bytes(data, 'utf-8'))
            except ConnectionResetError:
                print("Server disconnected.")
                break


if __name__ == "__main__":
    server = ServerCommunication()
    threading.Thread(target=server.receive_data_from_server).start()
    threading.Thread(target=server.send_data_to_server).start()
    while True:
        if game_init is True:
            print("Game is starting...")
            if game_is_host:
                app = TicTacToeGUI(host_server, 9999, True, name_you, name_opponent)
            else:
                app = TicTacToeGUI(host_server, 9999, False, name_you, name_opponent)
