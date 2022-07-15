class Client:
    def __init__(self, name, ip):
        self.name = name
        self.addr = (ip, 0)
        self.connected = False
        self.connection = None
