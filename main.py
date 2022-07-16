import songserver

server = songserver.Server(backend=songserver.backend.NetBackend())

while True:
    server.run()
