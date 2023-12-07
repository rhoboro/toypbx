import socket
import threading
from collections.abc import Callable
from contextlib import contextmanager
from weakref import ref

BUF_SIZE = 4096
SOCKET_TIMEOUT = 1


class UDPClient:
    def __init__(self, domain: str, port: int, callback: Callable[[str], None]) -> None:
        self.domain = domain
        self.port = port
        self.socket: socket.socket | None = None
        self.callback = ref(callback)

    @contextmanager
    def connect(self):
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as cs:
            self.socket = cs
            self.socket.settimeout(SOCKET_TIMEOUT)
            try:
                recv_thread = threading.Thread(target=self.receive_forever)
                recv_thread.start()
                yield self
            finally:
                self.socket = None
                recv_thread.join(SOCKET_TIMEOUT * 2)

    def send(self, message: str) -> None:
        if self.socket:
            self.socket.sendto(message.encode("utf-8"), (self.domain, self.port))

    def receive_forever(self) -> None:
        while self.socket:
            try:
                data = self.socket.recv(BUF_SIZE)
                response = data.decode("utf-8")
                if callback := self.callback():
                    callback(response)
            except TimeoutError:
                pass
