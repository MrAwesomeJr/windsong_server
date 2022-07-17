import sys
from os.path import exists
from pathlib import Path
from songserver.client import Client
import json
import logging


class Config:
    def __init__(self, config_file_name=""):
        self.config_file_name = ""
        self.config_dictionary = {}
        self.logger = logging.getLogger("config")

        self.load_file(config_file_name)

    def load_file(self, config_file_name):
        default_config_file_name = "./config.json"

        # accept file as command line argument
        if len(sys.argv) >= 2:
            if exists(sys.argv[1]) and Path(sys.argv[1]).is_file():
                self.config_file_name = sys.argv[1]
        if self.config_file_name == "":
            if exists(config_file_name) and Path(config_file_name).is_file():
                self.config_file_name = config_file_name
            else:
                self.config_file_name = default_config_file_name

        file = open(self.config_file_name,"r+")
        self.config_dictionary = json.loads(file.read())
        file.close()
        self.logger.debug(f"Config file {self.config_file_name} read")

    def get_sync_addr(self):
        self.logger.debug(f"Sync address of {self.config_file_name} retrieved")

        sync_addr = ("0.0.0.0", 22101)

        if "sync_ip" in self.config_dictionary:
            sync_addr = (self.config_dictionary["sync_ip"], sync_addr[1])
        if "sync_port" in self.config_dictionary:
            sync_addr = (sync_addr[0], self.config_dictionary["sync_port"])

        return sync_addr

    def get_clients(self):
        self.logger.debug(f"Clients of {self.config_file_name} retrieved")

        clients = []

        if "clients" in self.config_dictionary:
            clients = self.config_dictionary["clients"]

        for index, client in enumerate(clients):
            clients[index] = Client(client[0], client[1])

        return clients

    def get_ips(self):
        self.logger.debug(f"IPs of {self.config_file_name} retrieved")

        ips = []

        if "clients" in self.config_dictionary:
            ips = self.config_dictionary["clients"]

        for index, ip in enumerate(ips):
            ips[index] = ip[1]

        return ips

    def get_master_clock(self):
        self.logger.debug(f"Master Clock of {self.config_file_name} retrieved")
        # accepts either an existing client ip or the game server clock by default.
        # possible values are ["game"|"server"|<ip>]
        default_master_clock = "game"
        master_clock = default_master_clock

        if "master_clock" in self.config_dictionary:
            master_clock = self.config_dictionary["master_clock"]

        if master_clock not in ("game","server"):
            if master_clock not in self.get_ips():
                master_clock = default_master_clock

        return master_clock
