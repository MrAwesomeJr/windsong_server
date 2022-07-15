import socket
import time
import backend
from config import Config
from client import Client
import threading

class Server:
    def __init__(self, backend, config_file_name=""):
        self.backend = backend

        self.config = Config(config_file_name)
        self.sync_addr = self.config.get_sync_addr()
        self.clients = self.config.get_clients()

        self.socket = socket.socket()
        self.socket.bind(self.sync_addr)
        print("Socket bound to", self.sync_addr[0]+":"+str(self.sync_addr[1]))
        self.socket.listen(5)
        print("Listening for connections...")

    def run(self):
        self.await_connections()
        self.backend.run(self.socket, self.client)

    def await_connections(self):
        # waits until all clients have connected = True before continuing
        while True:
            connection, addr = self.socket.accept()
            if addr[0] in map(lambda client: client.addr[0], self.clients):
                for client in self.clients:
                    if client.addr[0] == addr[0] and client.connected == False:
                        client.connected = True
                        client.connection = connection
                        client.connection.setblocking(False)
                        client.addr = addr
                        print("Connected client \""+client.name+"\" at address "+str(client.addr[0])+":"+str(client.addr[1]))
                        break
            else:
                print("Unexpected connection at address"+str(addr[0])+":"+str(addr[1]))

            for client in self.clients:
                backend.get_message(client)

            if all(map(lambda client: client.connected, self.clients)):
                break

        print("All expected clients connected.")

        for client in self.clients:
            client.connection.setblocking(True)