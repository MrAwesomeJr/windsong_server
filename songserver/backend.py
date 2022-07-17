from songserver.config import Config
import socket
import time
from songserver.client import Client
import logging


def get_message(client):
    logger = logging.getLogger("server")
    # TODO: FIX THIS THINGY
    # gets insta dced for some reason (why?)

    if client.connected:
        # client connection should be non-blocking
        try:
            msg = client.connection.recv(1024)
        except BlockingIOError:
            return None
        except ConnectionResetError:
            logger.warning(f"Connection with \"{client.name}\" at address {client.addr[0]}:{client.addr[1]} reset by client.")
            return None

        if msg == b'':
            client.connected = False
            logger.warning(f"Connection with \"{client.name}\" at address {client.addr[0]}:{client.addr[1]} closed by client.")
            client.connection.close()
        else:
            return msg.decode()

    return None


class NullBackend:
    def __init__(self):
        self.logger = logging.getLogger("backend")

    def run(self, sock, clients):
        self.logger.info("Backend Ran. Nothing happened because you set your backend to NullBackend.")


class OnInitBackend(NullBackend):
    def run(self, sock, clients):
        start_time = time.time() + 3
        self.logger.info("Start time set to", start_time)

        for client in clients:
            client.connection.send(str(start_time).encode())
            client.connection.shutdown(socket.SHUT_RDWR)
            client.connection.close()
            self.logger.debug(f"Client socket \"{client.name}\" shutdown cleanly.")

        self.logger.info("All clients received start time.")


class NetBackend(NullBackend):
    class _PingedClient(Client):
        def __init__(self, client):
            self.name = client.name
            self.addr = client.addr
            self.connected = client.connected
            self.connection = client.connection
            self.ping = None

    def __init__(self):
        super().__init__()
        self.pinged_clients = []

        self.config = Config()
        self.master_clock = self.config.get_master_clock()

    def _get_client_desync(self, client):
        # TODO: check positive/negative
        # could probably replace this with a switch case but most people aren't using 3.10 yet so...
        if self.master_clock == "game":
            return (client.ping / 2)
        elif self.master_clock == "server":
            return "NTP"
        else:
            # TODO: if you're master
            # self.master_clock is a client ip
            desync = 0
            for pinged_client in self.pinged_clients:
                if pinged_client.addr[0] == self.master_clock:
                    if pinged_client.ping is not None and client.ping is not None:
                        return ((pinged_client.ping + client.ping) / 2)
                    else:
                        return 0

    def run(self, sock, clients):
        sock.setblocking(False)
        self.pinged_clients = []
        for client in clients:
            self.pinged_clients.append(self._PingedClient(client))

        # 3 is an arbitrary value to give time for all clients to process before starting.
        # 0 isn't possible because by the time the clients receive the time it will already have passed
        # and therefore all clients will start late.
        start_time = time.time() + 3
        self.logger.info(f"Start time set to {start_time}.")

        # clients expect a start time before they start sending pings to the server.

        for client in self.pinged_clients:
            if client.connected:
                client.connection.send(str(start_time).encode())

        self.logger.info("All clients received start time.")

        last_request = time.perf_counter()
        # expect one ping every 5 seconds per client
        while (time.perf_counter() - last_request) < 10:
            for client in self.pinged_clients:
                if client.connected:
                    last_request = time.perf_counter()
                    ping = get_message(client)
                    if ping is not None:
                        client.ping = float(ping)
                        self.logger.debug(f"Ping of {client.ping} received from \"{client.name}\".")
                        desync = self._get_client_desync(client)
                        client.connection.send(str(desync).encode())
                        self.logger.debug(f"Desync of {desync} sent to \"{client.name}\".")
                    else:
                        self.logger.error(f"Ping not received from client \"{client.name}\".")
                        
            # attempt reconnection to clients. socket should be in non-blocking mode.
            try:
                connection, addr = sock.accept()
            except BlockingIOError:
                # will throw error when no client is requesting connection
                pass
            else:
                if addr[0] in map(lambda client: client.addr[0], clients):
                    for client in clients:
                        if client.addr[0] == addr[0] and client.connected == False:
                            client.connected = True
                            client.connection = connection
                            client.connection.setblocking(False)
                            client.addr = addr
                            self.logger.info(f"Connected client {client.name} at address {self._stringify_addr(client.addr)}")
                            break
                else:
                    self.logger.info(f"Unexpected connection at address {self._stringify_addr(addr)}")
                    