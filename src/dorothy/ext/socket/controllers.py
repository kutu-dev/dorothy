from multiprocessing import Process
import time
import socket

from dorothy import Colors
from dorothy.config import ConfigSchema
from dorothy.models import Controller


class SocketController(Controller):
    config_schema = ConfigSchema(
        node_id="socket-controller",
        node_type=Controller,
        default_config={
            "port": 7171
        }
    )

    def __init__(self):
        super().__init__()

    def start(self) -> None:
        self.host = "127.0.0.1"
        self.port = self.instance_config["port"]
        self.server_socket_process = Process(target=self.start_socket_connection())
        self.server_socket_process.start()

    # TODO Put every client connection in a different thread (see notes on Discord)
    #  Fix address already in use issue
    def start_socket_connection(self) -> None:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind((self.host, self.port))
            self.logger.info(f'Start listening in {Colors.dim}"{self.host}:{self.port}"{Colors.reset}')
            s.listen()

            while True:
                client, addr = s.accept()
                with client:
                    while True:
                        data = client.recv(1024)

                        if not data:
                            self.logger("Client connection closed")
                            break

                        data = data.decode("utf-8")
                        print(data)

    def cleanup(self) -> None:
        self.server_socket_process.terminate()
        self.server_socket_process.close()
