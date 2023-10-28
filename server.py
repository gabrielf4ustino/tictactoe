import datetime
import socket
import threading


# User class to represent user information
class User:
    def __init__(self, name, username, password):
        self.name = name
        self.username = username
        self.password = password
        self.address = None  # Initial address
        self.status = "INACTIVE"  # Initial status


# Game class to represent a game
class Game:
    def __init__(self, player1, player2):
        self.player1 = player1
        self.player2 = player2
        self.state = "IN PROGRESS"  # Initial game state


# Function to find a user by their username
def find_user(username):
    # Read user data from the log file and populate the users dictionary
    for line in open("data", "r"):
        _, name, found_username, password = line.strip().split(" ")
        if found_username == username:
            return User(name, found_username, password)
    return None


# Function to authenticate a user based on their username and password
def authenticate_user(username, password):
    user = find_user(username)
    if user is not None:
        if user.password == password:
            return user
    return False


# Class representing the Authentication and Information Server
class AuthenticationInformationServer:
    def __init__(self):
        self.users = {}  # Dictionary to store users
        self.games = {}  # Dictionary to store games
        self.waiting_invite_response = False  # Flag to indicate if a game is starting
        self.invite_response = False  # Flag to indicate if a game is starting
        self.log_file = open("game.log", "a")  # Log file
        self.data_file = open("data", "a+")  # Data file
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind(('localhost', 1024))
        self.server_socket.listen(5)
        self.clients = {}

    # Function to register a new user
    def register_user(self, user):
        self.data_file.write("User {} {} {}\n".format(user.name, user.username, user.password))
        self.data_file.flush()
        self.log("User {} registered".format(user.name))

    # Function to start a game between two users
    def start_game(self, client_socket, player1, player2):
        game = Game(player1, player2)
        self.games[(player1, player2)] = game
        self.users[player1].status = "ACTIVE"
        self.users[player2].status = "ACTIVE"
        client_socket.send(
            "GAME_ACK: {} {} host {} {}".format(self.users[player2].address[0], self.users[player2].address[1], player1,
                                                player2)
            .encode())
        self.clients[player2].send("GAME_ACK: {} {} client {} {}".format(self.users[player2].address[0],
                                                                         self.users[player2].address[1], player2,
                                                                         player1).encode())

        self.log("Users {} and {} started a game".format(player1, player2))

    # Function to log a message with a timestamp
    def log(self, message):
        date_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = "{}: {}\n".format(date_time, message)
        print(log_entry)
        self.log_file.write(log_entry)
        self.log_file.flush()

    # Function to close the connection for a user
    def close_connection(self, user):
        self.log("User {} disconnected from the network".format(user.username))
        self.users.pop(user.username)
        return None

    # Function to end a game between two players
    def end_game(self, player1, player2):
        self.log("Users {} and {}: GAME_OVER".format(player1, player2))
        self.users[player1].status = "INACTIVE"
        self.users[player2].status = "INACTIVE"
        self.log("User {} turned INACTIVE".format(player1))
        self.log("User {} turned INACTIVE".format(player2))
        del self.games[(player1, player2)]

    # Function to handle user registration
    def handle_register(self, client_socket, message):
        _, name, username, password = message.split(" ")
        user = User(name, username, password)
        self.register_user(user)
        client_socket.send("Registration successful".encode())

    # Function to handle user login
    def handle_login(self, client_socket, addr, message):
        _, username, password = message.split(" ")
        print(self.users)
        if self.users.__contains__(username):
            raise Exception("User already logged in")
        user = authenticate_user(username, password)
        if user is not False:
            user.status = "ACTIVE"
            user.address = addr
            self.users[username] = user
            self.clients[username] = client_socket
            client_socket.send("Authentication successful".encode())
            self.log("User {} logged in".format(user.username))
            return user
        else:
            client_socket.send("Authentication failed".encode())
            return None

    # Function to handle listing online users
    def handle_list_users(self, client_socket, is_playing=False):
        if is_playing:
            online_users = [(user.name, user.username, user.address, user.status) for user in self.users.values() if
                            user.status == "ACTIVE"]
        else:
            online_users = [(user.name, user.username, user.address, user.status) for user in self.users.values()]
        client_socket.send(str(online_users).encode())

    # Function to handle game invites
    def handle_invite(self, client_socket, current_user, message):
        _, receiver_username = message.split(" ")
        if current_user.username == receiver_username:
            raise Exception("You cannot invite yourself")
        receiver_socket = self.clients[receiver_username]
        receiver_socket.send("User {} wants to play with you. To accept, type yes and to reject, type no".format(
            current_user.username).encode())
        client_socket.send("Invite sent. Waiting for response...".encode())
        while True:
            self.waiting_invite_response = True
            response = self.invite_response
            if response == "GAME_ACK":
                self.start_game(client_socket, current_user.username, receiver_username)
                self.invite_response = None
                break
            elif response == "GAME_NEG":
                print("Game rejected")
                client_socket.send("GAME_NEG".encode())
                self.invite_response = None
                break

    # Function to handle the end of a game
    def handle_game_over(self, message):
        _, player1, player2 = message.split(" ")
        self.end_game(player1, player2)

    # Function to handle a client connection
    def handle_client(self, client_socket, addr):
        current_user = None  # Current user
        while True:
            try:
                message = client_socket.recv(1024).decode().strip()  # Receives message from the client
                print(message)
                if message.startswith("REGISTER"):
                    try:
                        self.handle_register(client_socket, message)
                    except Exception as e:
                        client_socket.send("Registration failed. Reason: {}".format(e).encode())
                elif message.startswith("LOGIN"):
                    try:
                        if current_user is not None:
                            raise Exception("You are already logged in")
                        else:
                            current_user = self.handle_login(client_socket, addr, message)
                    except Exception as e:
                        client_socket.send("Login failed. Reason: {}".format(e).encode())
                elif message.startswith("LIST-USER-ON-LINE"):
                    try:
                        self.handle_list_users(client_socket)
                    except Exception as e:
                        client_socket.send("List users on-line failed. Reason: {}".format(e).encode())
                elif message.startswith("LIST-USER-PLAYING"):
                    try:
                        self.handle_list_users(client_socket, True)
                    except Exception as e:
                        client_socket.send("List users playing failed. Reason: {}".format(e).encode())
                elif message.startswith("GAME_INI"):
                    try:
                        self.handle_invite(client_socket, current_user, message)
                    except Exception as e:
                        client_socket.send("Invite failed. Reason: {}".format(e).encode())
                elif message.startswith("GAME_OVER"):
                    try:
                        self.handle_game_over(message)
                    except Exception as e:
                        client_socket.send("Game over failed. Reason: {}".format(e).encode())
                elif message.startswith("EXIT"):
                    try:
                        if current_user is None:
                            client_socket.send("exit".encode())
                        else:
                            self.close_connection(self.users[current_user.username])
                            client_socket.send("exit".encode())
                    except Exception as e:
                        client_socket.send("Exit failed. Reason: {}".format(e).encode())
                    break
                elif message.startswith("YES"):
                    if self.waiting_invite_response:
                        self.invite_response = "GAME_ACK"
                        self.waiting_invite_response = False
                    else:
                        client_socket.send("Invalid command".encode())
                elif message.startswith("NO"):
                    if self.waiting_invite_response:
                        self.invite_response = "GAME_NEG"
                        self.waiting_invite_response = False
                    else:
                        client_socket.send("Invalid command".encode())
                else:
                    client_socket.send("Invalid command".encode())
            except ConnectionResetError:
                if current_user is not None:
                    self.close_connection(self.users[current_user.username])
                break

    # Function to start the server and handle client connections
    def start_server(self):
        while True:
            client_socket, addr = self.server_socket.accept()
            client_thread = threading.Thread(target=self.handle_client, args=(client_socket, addr))
            client_thread.start()


# Main entry point of the program
if __name__ == "__main__":
    server = AuthenticationInformationServer()
    server.start_server()
