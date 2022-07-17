import logging
import socket
from songserver import backend
from songserver.config import Config
import urllib.request
import logging


class Server:
    def __init__(self, backend, config_file_name=""):
        self.backend = backend

        self.logger = logging.getLogger("server")

        self.config = Config(config_file_name)
        self.sync_addr = self.config.get_sync_addr()
        self.clients = self.config.get_clients()

        self.socket = socket.socket()
        self.socket.bind(self.sync_addr)
        self.logger.info(f"Socket bound to {self._stringify_addr(self.sync_addr)}")
        self.logger.info(f"Your ip is {urllib.request.urlopen('https://v4.ident.me').read().decode('utf8')}:{self.sync_addr[1]}")
        self.socket.listen(5)
        self.logger.info(f"Listening for {len(self.clients)} connection(s)...")

    def _stringify_addr(self, addr):
        return f"{addr[0]}:{addr[1]}"

    def run(self):
        self._await_connections()
        self.backend.run(self.socket, self.clients)

    def _await_connections(self):
        # waits until all clients have connected as True before continuing
        self.socket.setblocking(True)
        while True:
            connection, addr = self.socket.accept()
            if addr[0] in map(lambda client: client.addr[0], self.clients):
                for client in self.clients:
                    if client.addr[0] == addr[0] and client.connected is False:
                        client.connected = True
                        client.connection = connection
                        client.connection.setblocking(False)
                        client.addr = addr
                        self.logger.info(f"Connected client {client.name} at address {self._stringify_addr(client.addr)}")
                        break
            else:
                self.logger.info(f"Unexpected connection at address {self._stringify_addr(addr)}")

            for client in self.clients:
                backend.get_message(client)

            if all(map(lambda client: client.connected, self.clients)):
                break

        self.logger.info("All expected clients connected.")
