from server import Server
import backend

server = Server(backend=backend.NetBackend)

while True:
    server.run()