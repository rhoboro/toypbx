from dataclasses import dataclass, field

from .headers import *
from .message import RequestMessage, ResponseMessage
from .methods import ClientMethod


@dataclass
class Transaction:
    local_tag: str = field(default_factory=From.gen_tag)
    branch: str = field(default_factory=Via.gen_branch)
    call_id: str = field(default_factory=CallID.gen_call_id)
    local_c_seq: int = field(default_factory=CSeq.gen_c_seq)
    request_messages: list[RequestMessage] = field(default_factory=list)
    response_messages: list[ResponseMessage] = field(default_factory=list)
    remote_tag: str | None = None
    remote_c_seq: int | None = None

    def add_request(self, request: RequestMessage) -> None:
        self.local_tag = request.headers["From"].tag
        self.local_c_seq = request.headers["CSeq"].c_seq
        self.request_messages.append(request)

    def add_response(self, response: ResponseMessage) -> None:
        self.remote_tag = response.headers["To"].tag
        self.branch = response.headers["Via"].branch
        self.call_id = response.headers["Call-ID"].call_id
        self.remote_c_seq = response.headers["CSeq"].c_seq
        self.response_messages.append(response)

    @property
    def next_local_c_seq(self) -> int:
        return self.local_c_seq + 1

    @property
    def last_request(self) -> RequestMessage | None:
        return self.request_messages[-1] if self.request_messages else None

    @property
    def last_response(self) -> ResponseMessage | None:
        return self.response_messages[-1] if self.response_messages else None


@dataclass
class Dialog:
    transactions: list[Transaction] = field(default_factory=list)


@dataclass
class MultiMediaSession:
    ...


@dataclass
class Context:
    domain: str
    username: str
    password: str
    register_transaction: Transaction = None
    dialogs: list[Dialog] = field(default_factory=list)

    def add_request(self, request: RequestMessage) -> None:
        if request.start_line.method == ClientMethod.REGISTER:
            self.register_transaction.add_request(request)
        else:
            self.dialogs[-1].transactions[-1].add_request(request)

    def add_response(self, response: ResponseMessage) -> None:
        if response.method == ClientMethod.REGISTER:
            self.register_transaction.response_messages.append(response)
        else:
            self.dialogs[-1].transactions[-1].add_response(response)
