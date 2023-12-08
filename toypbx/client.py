import time
from contextlib import contextmanager
from enum import StrEnum

from toypbx.net import UDPClient
from toypbx.protocols.sip.context import Context, Dialog, Transaction
from toypbx.protocols.sip.message import (
    AckMessage,
    ByeMessage,
    ClientMethod,
    InviteMessage,
    RegisterMessage,
    RequestMessage,
    ResponseMessage,
)


class Status(StrEnum):
    UNAVAILABLE = "UNAVAILABLE"
    AVAILABLE = "AVAILABLE"
    CALLING = "CALLING"

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}.{self.name}"


class Client:
    def __init__(
        self,
        domain: str,
        username: str,
        password: str,
        server: str | None = None,
        port: int = 5060,
    ) -> None:
        self.domain = domain
        self.username = username
        self.password = password
        self.udp_client = UDPClient(server or domain, port=port, callback=self)
        self.status = Status.UNAVAILABLE
        self.context = Context(
            domain=domain,
            username=username,
            password=password,
        )

    def __call__(self, response: str):
        self.on_receive(response)

    def on_receive(self, response: str):
        response = ResponseMessage.from_raw(response)
        self.context.add_response(response)

        print(response.start_line.status_code, response.method)
        match (response.start_line.status_code, response.method):
            case (100, ClientMethod.INVITE):
                pass

            case (200, ClientMethod.REGISTER):
                if response.method == ClientMethod.REGISTER:
                    if response.headers["Expires"].expires == 0:
                        self.status = Status.UNAVAILABLE
                    else:
                        self.status = Status.AVAILABLE
            case (200, ClientMethod.INVITE):
                self.status = Status.CALLING
                self.ack(response)

            case (200, ClientMethod.BYE):
                self.status = Status.AVAILABLE

            case (401, ClientMethod.REGISTER):
                request = self.context.register_transaction.last_request
                digest_request = request.digest(self.username, self.password, response)
                if digest_request:
                    self.send(digest_request)
                else:
                    print("FAILURE")

            case (401, _):
                request = self.context.dialogs[-1].transactions[-1].last_request
                digest_request = request.digest(self.username, self.password, response)
                if digest_request:
                    self.send(digest_request)
                else:
                    print("FAILURE")

            case _:
                print("UNEXPECTED RESPONSE")
                print(response)

    def send(self, request: RequestMessage) -> None:
        print(request.start_line.method)
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
                transaction = Transaction()
                self.context.register_transaction = transaction
                request = RegisterMessage.create(
                    domain=self.domain,
                    username=self.username,
                    expires=expires,
                    transaction=transaction,
                )
                self.send(request)
                self.expect(Status.AVAILABLE)
                yield self
            finally:
                if self.status == Status.AVAILABLE:
                    request = RegisterMessage.create(
                        domain=self.domain,
                        username=self.username,
                        # 0 for UNREGISTER
                        expires=0,
                        transaction=Transaction(call_id=transaction.call_id),
                    )
                    self.send(request)
            self.expect(Status.UNAVAILABLE)

    @contextmanager
    def invite(
        self,
    ) -> ResponseMessage:
        transaction = Transaction()
        dialog = Dialog(transactions=[transaction])
        self.context.dialogs.append(dialog)
        request = InviteMessage.create(
            target="100",
            domain=self.domain,
            username=self.username,
            transaction=transaction,
        )
        try:
            self.send(request)
            self.expect(Status.CALLING)
            yield self.context.dialogs[-1]
        finally:
            # transaction = Transaction()
            # dialog.transactions.append(transaction)
            request = ByeMessage.create(
                target="100",
                domain=self.domain,
                username=self.username,
                transaction=transaction,
            )
            self.send(request)
            self.expect(Status.AVAILABLE)

    def ack(self, response: ResponseMessage) -> None:
        transaction = self.context.dialogs[-1].transactions[-1]
        request = AckMessage.create(
            target="100",
            domain=self.domain,
            username=self.username,
            transaction=transaction,
        )
        self.send(request)
        self.expect(Status.CALLING)
