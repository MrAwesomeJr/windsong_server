from songserver.config import Config
import socket
import time
from songserver.client import Client


def get_message(client):
    if client.connected:
        blocking_status = client.connection.getblocking()
        client.connection.setblocking(False)
        try:
            msg = client.connection.recv(1024)
            if len(msg) == 0:
                client.connected = False
                client.connection.close()
            else:
                client.connection.setblocking(blocking_status)
                return msg
        except socket.timeout:
            client.connected = False
            client.connection.close()

    return None


class NullBackend:
    def __init__(self):
        pass

    def run(self, sock, clients):
        print("Backend Ran. Nothing happened because you set your backend to NullBackend.")


class OnInitBackend(NullBackend):
    def run(self, sock, clients):
        start_time = time.time() + 3
        print("Start time set to", start_time)

        for client in clients:
            client.connection.send(str(start_time).encode())
            client.connection.shutdown(socket.SHUT_RDWR)
            client.connection.close()

        print("All clients received start time.")


class NetBackend(NullBackend):
    class PingedClient(Client):
        def __init__(self, client):
            self.name = client.name
            self.addr = client.addr
            self.connected = client.connected
            self.connection = client.connection
            self.ping = None
            self.pinged_clients = []

            self.config = Config()
            self.master_clock = self.config.get_master_clock()

    def get_client_desync(self, client):
        # could probably replace this with a switch case but most people aren't using 3.10 yet so...
        if self.master_clock == "game":
            return (client.ping / 2)
        elif self.master_clock == "server":
            return "NTP"
        else:
            # self.master_clock is a client ip
            desync = 0
            for pinged_client in self.pinged_clients:
                if pinged_client.addr[0] == self.master_clock:
                    return ((pinged_client.ping + client.ping) / 2)

    def run(self, sock, clients):
        self.pinged_clients = []
        for client in clients:
            self.pinged_clients.append(client)

        start_time = time.time() + 3
        print("Start time set to", start_time)

        # clients expect a start time before they start sending pings to the server.

        for client in self.pinged_clients:
            if client.connected:
                client.connection.send(str(start_time).encode())

        print("All clients received start time.")

        for client in self.pinged_clients:
            if client.connected:
                client.ping = get_message(client)
                if client.connected:
                    client.connection.send(str(self.get_client_desync(client)).encode())
