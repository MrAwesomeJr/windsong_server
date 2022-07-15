from server.server import Server
from server import backend

server = Server(backend=backend.NetBackend)

while True:
    server.run()
