import songserver
import logging

logging.getLogger()
logging.basicConfig(level=logging.INFO)
server = songserver.Server(backend=songserver.backend.NetBackend())


while True:
    server.run()
