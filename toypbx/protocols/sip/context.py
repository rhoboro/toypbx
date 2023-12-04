from dataclasses import dataclass, field

from .headers import *
from .message import RequestMessage, ResponseMessage


@dataclass
class Context:
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
        self.local_c_seq = request.headers["CSeq"].value
        self.request_messages.append(request)

    def add_response(self, response: ResponseMessage) -> None:
        self.remote_tag = response.headers["To"].tag
        self.branch = response.headers["Via"].branch
        self.call_id = response.headers["Call-ID"].value
        self.remote_c_seq = response.headers["CSeq"].value
        self.response_messages.append(response)

    @property
    def next_local_c_seq(self) -> int:
        return self.local_c_seq + 1
