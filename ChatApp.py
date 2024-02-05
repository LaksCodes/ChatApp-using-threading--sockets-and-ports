import socket
import threading
import time
import datetime
import re
from random import randint
from LoginMenu import *
from PyQt5.QtCore import *


# Server Class to handle onnections and messages
class Server:

    connections = [] # List to store client connections
    peers = [] # List to store peer addresses
    members = [] # List to store member usernames
    messages = [] # List to store chat messages
    all_cmd = False # Flag to allow all users to use commands

    #Initialize the server with IP and PORT

    def __init__(self, IP, PORT):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind((IP,PORT))
        sock.listen()
        ui.ConnectionResult_Label.setText("Server Created. Start as Client")

        # Accept incoming connections
        while True:
            client_socket, client_address = sock.accept()
            connections_thread = threading.Thread(target=self.connection_handler, args=(client_socket,client_address))
            connections_thread.daemon = True
            connections_thread.start()
            self.connections.append(client_socket)
            self.peers.append(client_address[0])
            client_socket.send(bytes("Welcome to our Group Chat!!\n\n","utf-8"))
            print(f'Accepted new connection from {client_address[0]}:{client_address[1]}')
            self.sendPeers() # Send list of peers to all clients

    # Method to handle individual client connections
    def connection_handler(self, client_socket,client_address):

        while True:
            data = client_socket.recv(1024)
            usrnme = data.decode("utf-8")
            usrnme = re.search(r"\[([A-Za-z0-9_]+)\]", usrnme)
            
            message = data.decode("utf-8")
            currentTime = datetime.datetime.now().strftime('%H:%M:%S')
            message = (str(currentTime) + message)
            self.messages.append(message)

            # Add username to members list if not already present
            if str(usrnme.group(1))not in self.members:
                self.members.append(usrnme.group(1))
            # Check if user is allowed to use commands
            if usrnme.group(1) == self.members[0] or self.all_cmd == True:
                cmd = data.decode("utf-8")
                try:
                    
                    if cmd[(len(usrnme.group(1))+3)] == "/":

                        # Handle commands

                        if cmd[(len(usrnme.group(1))+4):] == "help":
                            for connection in self.connections:
                                connection.send(bytes("[SERVER] To view all members type '/members'\n To view peers type '/peers'\nTo allow all users to use commands '/togglecmd' \n To Save current conversation type '/save'", "utf-8"))

                        elif cmd[(len(usrnme.group(1))+4):] == "members":
                            memberstring = ""
                            for member in self.members:
                                memberstring = memberstring + "\n" + member
                            for connection in self.connections:
                                connection.send(bytes(((self.members[0])+" is the Co-ordinater and is able to use commands\nOther Members:"+memberstring),"utf-8"))

                        elif cmd[(len(usrnme.group(1))+4):] == "peers":
                            peerstring = ""
                            for peer in self.peers:
                                peerstring = peerstring + "\n" + peer
                            for connection in self.connections:
                                connection.send(bytes((peerstring),"utf-8"))

                        elif cmd[(len(usrnme.group(1))+4):] == "togglecmd":
                            self.all_cmd = True

                            for connection in self.connections:
                                connection.send(bytes("[SERVER]\n All users can use commands.","utf-8"))
                                
                        elif cmd[(len(usrnme.group(1))+4):] == "save":
                            currentTime = datetime.datetime.now().strftime('%Y-%m-%d_%H:%M:%S')
                            Header = str(usrnme.group(1)[0])+ "-" + str(currentTime)
                            file = open("Log.txt", 'a')
                            file.write("\n" + Header+ "\n\n")
                            for message in self.messages:
                                file.write("%s\n" % message)
                            file.close()
                            
                        else:
                            for connection in self.connections:
                                connection.send(bytes("[SERVER] Invalid command","utf-8"))
                except:
                    pass

            # Broadcast message to all clients               
            for connection in self.connections:
                connection.send(bytes(data))
            if not data:
                print(f'Lost connection from {client_address[0]}:{client_address[1]}')
                self.connections.remove(client_socket)
                self.peers.remove(client_address[0])
                client_socket.close()
                self.sendPeers()
                break
        
    # Method to send list of peers to all clients
    def sendPeers(self):
        p = ""
        for peer in self.peers:
            p = p + peer + ","

        for connection in self.connections:
            connection.send(b'\x11' + bytes(p, "utf-8"))

#Client class to handle client-side functionality
class Client:
    

    def __init__(self, username, IP, PORT):
        LoginWindow.close()
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.connect((IP, PORT))
        self.username = username
        ui.ConnectionResult_Label.setText("Connected now closing...check CLI")
        time.sleep(4)
        LoginWindow.close()

        # Start input thread to send messages
        input_thread = threading.Thread(target=self.sendMSG, args=(sock,))
        input_thread.daemon = True
        input_thread.start()

        # Receive messages from server
        while True:
            data = sock.recv(1024)
            if not data:
                break
            if data[0:1] == b'\x11':
                self.updatePeers(data[1:])
            else:
                print(str(data, 'utf-8'))
    # Method to send messages to server
    def sendMSG(self, sock):
        while True:
            sock.send(bytes(f'[{self.username}] ' + (input(">")), "utf-8"))


    # Method to update list of peers
    def updatePeers(self, peerData):
        p2p.peers = str(peerData, "utf-8").split(",")[:-1]

# Class for handling peer-to-peer connections
class p2p:
    peers = ['127.0.0.1']


# Class for the login menu window
class LoginMenuWindow(Ui_Dialog):
    def __init__(self, window):
        self.setupUi(window)
        self.LogInButton.clicked.connect(self.LogInFunc)
        self.StartServerButton.clicked.connect(self.CreateServerFunc)
        

    def ClientThreadFunc(self,ID, IP_Server, Port_Server, IP_Listen, Port_Listen):
        print("Client Thread starting...")
        time.sleep(1)
        try:
            client = Client(str(ID), str(IP_Listen), int(Port_Listen))
            time.sleep(1)
        except KeyboardInterrupt:
            sys.exit(0)
        except:
            pass
        try:
            server = Server(1000, p2p.peers[0])
        except KeyboardInterrupt:
            sys.exit(0)
        except:
            self.ConnectionResult_Label.setText("Connection Failed. Check Details.")


    # Method to start server thread
    def ServerThreadFunc(self, IP_Server, Port_Server):
        print("Server Thread starting...")
        time.sleep(1)
        try:
            print("Server Creation Attempting...")
            server = Server(str(IP_Server), int(Port_Server))
            time.sleep(2)
            self.ConnectionResult_Label.setText("Server created, proceed to connect as user")
            time.sleep(3)
        except:
            self.ConnectionResult_Label.setText("Error while creating server")

    # Method to handle login button click        
    def LogInFunc(self):
        self.ID = self.ID_Input.text()
        self.Port_Listen = self.PortListen_Input.text()
        self.IP_Listen = self.IPListen_Input.text()
        self.Port_Server = self.PortServer_Input.text()
        self.IP_Server = self.IPServer_Input.text()
        self.ConnectionResult_Label.setText("Attempting to connect...Check shell for chat")

        # Start client thread
        ClientThread = threading.Thread(target=self.ClientThreadFunc, args=(self.ID, self.IP_Server, self.Port_Server, self.IP_Listen, self.Port_Listen))
        time.sleep(3)
        ClientThread.start()

    # Method to handle server creation button click
    def CreateServerFunc(self):
        self.Port_Server = self.PortServer_Input.text()
        self.IP_Server = self.IPServer_Input.text()
        self.Port_Server = 1000
        self.IP_Server = '127.0.0.1'
        self.ConnectionResult_Label.setText("Creating Server...")
        ServerThread = threading.Thread(target=self.ServerThreadFunc, args=(self.IP_Server, self.Port_Server))
        time.sleep(2)
        ServerThread.start()

if __name__ == '__main__':
    import sys
    global ui
    app = QtWidgets.QApplication(sys.argv)
    LoginWindow = QtWidgets.QDialog()
    ui = LoginMenuWindow(LoginWindow)
    LoginWindow.show()
    sys.exit(app.exec_())
