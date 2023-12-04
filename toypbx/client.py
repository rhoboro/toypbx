from contextlib import contextmanager
from enum import StrEnum

from toypbx.net import send
from toypbx.protocols.sip.context import Context
from toypbx.protocols.sip.message import (
    RegisterMessage,
    RequestMessage,
    ResponseMessage,
)


class Status(StrEnum):
    NOT_REGISTERED = "NOT_REGISTERED"
    REGISTERED = "REGISTERED"

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}.{self.name}"


class Client:
    def __init__(
        self,
        domain: str,
        username: str,
        password: str,
    ) -> None:
        self.domain = domain
        self.username = username
        self.password = password
        self.status = Status.NOT_REGISTERED
        self.context = Context()

    @contextmanager
    def register(
        self,
        expire: int = 300,
    ) -> ResponseMessage:
        self._register(expire=expire)
        try:
            yield self
        finally:
            if self.status == Status.REGISTERED:
                self._unregister()

    @contextmanager
    def invite(
        self,
    ) -> ResponseMessage:
        if self.status == Status.NOT_REGISTERED:
            raise RuntimeError()

        try:
            print("INVITE")
            yield {}
        finally:
            print("BYE")

    def _send(self, request: RequestMessage) -> ResponseMessage:
        self.context.add_request(request)
        response = ResponseMessage.from_raw(send(self.domain, 5060, request.to_message()))
        self.context.add_response(response)
        return response

    def _register(
        self,
        expire: int,
    ) -> ResponseMessage:
        request = RegisterMessage.create(
            domain=self.domain,
            username=self.username,
            password=self.password,
            expire=expire,
            call_id=self.context.call_id,
            c_seq=self.context.local_c_seq,
            branch=self.context.branch,
            local_tag=self.context.local_tag,
        )
        response = self._send(request)
        if (
            response.start_line.status_code == 401
            and "WWW-Authenticate" in response.headers
            and request.has_password()
        ):
            digest_request = request.digest(response)
            response = self._send(digest_request)

        if response.start_line.status_code == 200:
            self.status = Status.REGISTERED

        return response

    def _unregister(self) -> ResponseMessage | None:
        if self.status == Status.NOT_REGISTERED:
            return None

        request = RegisterMessage.create(
            domain=self.domain,
            username=self.username,
            password=self.password,
            call_id=self.context.call_id,
            c_seq=self.context.next_local_c_seq,
            # 0 for UNREGISTER
            expire=0,
        )
        response = self._send(request)
        if (
            response.start_line.status_code == 401
            and "WWW-Authenticate" in response.headers
            and request.has_password()
        ):
            digest_request = request.digest(response)
            response = self._send(digest_request)

        self.status = Status.NOT_REGISTERED
        return response
