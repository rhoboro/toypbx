import time
from contextlib import contextmanager
from enum import StrEnum

from toypbx.net import UDPClient
from toypbx.protocols.sip.context import Context
from toypbx.protocols.sip.message import (
    ClientMethod,
    RegisterMessage,
    RequestMessage,
    ResponseMessage,
)


class Status(StrEnum):
    UNAVAILABLE = "UNAVAILABLE"
    AVAILABLE = "AVAILABLE"

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}.{self.name}"


class Client:
    def __init__(
        self,
        domain: str,
        username: str,
        password: str,
        port: int = 5060,
    ) -> None:
        self.udp_client = UDPClient(domain, port=port, callback=self)
        self.domain = domain
        self.username = username
        self.password = password
        self.status = Status.UNAVAILABLE
        self.context = Context()

    def __call__(self, response: str):
        self.on_receive(response)

    def on_receive(self, response: str):
        response = ResponseMessage.from_raw(response)
        self.context.add_response(response)

        print(response.start_line.status_code, response.method)
        match (response.start_line.status_code, response.method):
            case (200, ClientMethod.REGISTER):
                if response.method == ClientMethod.REGISTER:
                    if response.headers["Expires"].expires == 0:
                        self.status = Status.UNAVAILABLE
                        print("UNAVAILABLE")
                    else:
                        self.status = Status.AVAILABLE
                        print("AVAILABLE")

            case (401, ClientMethod.REGISTER):
                request = self.context.last_request
                digest_request = request.digest(response)
                if digest_request:
                    self.send(digest_request)
                else:
                    print("FAILURE")

            case (403, ClientMethod.REGISTER):
                print("UNEXPECTED RESPONSE")

            case _:
                print(response)
                print("UNEXPECTED RESPONSE")

    def send(self, request: RequestMessage) -> None:
        self.context.add_request(request)
        self.udp_client.send(request.to_message())

    def expect(self, status: Status, duration: float = 0.2, attempt: int = 10):
        for _ in range(attempt):
            if self.status == status:
                break
            time.sleep(duration)
        else:
            raise ValueError()

    @contextmanager
    def register(
        self,
        expires: int = 300,
    ) -> ResponseMessage:
        with self.udp_client.connect():
            try:
                request = RegisterMessage.create(
                    domain=self.domain,
                    username=self.username,
                    password=self.password,
                    expires=expires,
                    call_id=self.context.call_id,
                    c_seq=self.context.local_c_seq,
                    branch=self.context.branch,
                    local_tag=self.context.local_tag,
                )
                self.send(request)
                self.expect(Status.AVAILABLE)
                yield self
            finally:
                if self.status == Status.AVAILABLE:
                    request = RegisterMessage.create(
                        domain=self.domain,
                        username=self.username,
                        password=self.password,
                        call_id=self.context.call_id,
                        c_seq=self.context.next_local_c_seq,
                        # 0 for UNREGISTER
                        expires=0,
                    )
                    self.send(request)
            self.expect(Status.UNAVAILABLE)
