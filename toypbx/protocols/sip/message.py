from dataclasses import dataclass
from typing import TYPE_CHECKING, Self, cast

from .headers import *
from .methods import ClientMethod

if TYPE_CHECKING:
    from .context import Transaction


@dataclass(frozen=True)
class RequestStartLine:
    method: ClientMethod
    request_uri: str
    sip_version: str = "SIP/2.0"


@dataclass(frozen=True)
class ResponseStartLine:
    sip_version: str
    status_code: int
    reason_phrase: str


@dataclass()
class ResponseMessage:
    start_line: ResponseStartLine
    headers: Headers
    body: list[str]

    @classmethod
    def from_raw(cls, raw_message: str) -> Self:
        headers = Headers()
        lines = raw_message.splitlines()
        sip_version, status_code, reason_phrase = lines[0].split(" ", 2)
        for line in lines[1:]:
            if not line:
                break

            key, value = line.split(":", 1)
            header = HeaderFactory(key, value.strip())
            headers[header.name] = header

        return ResponseMessage(
            start_line=ResponseStartLine(
                sip_version=sip_version,
                status_code=int(status_code),
                reason_phrase=reason_phrase,
            ),
            headers=headers,
            body=[],
        )

    @property
    def method(self) -> ClientMethod | None:
        try:
            return self.headers["CSeq"].method
        except KeyError:
            return None


@dataclass()
class RequestMessage:
    start_line: RequestStartLine
    headers: Headers
    body: list[str]

    def to_message(self) -> str:
        lines = [
            f"{self.start_line.method} {self.start_line.request_uri} {self.start_line.sip_version}"
        ]
        for value in self.headers.values():
            lines.append(f"{value.name}: {value}")

        lines.append("")
        for body_line in self.body:
            lines.append(body_line)
        return "\n".join(lines)

    def digest(self, username: str, password: str, response: ResponseMessage) -> Self | None:
        www_authenticate = cast(WWWAuthenticate, response.headers.pop(WWWAuthenticate.name))

        headers = Headers(**self.headers)
        headers[CSeq.name] = cast(CSeq, headers[CSeq.name]).next()
        headers[Authorization.name] = Authorization(
            username=username,
            password=password,
            method=response.headers["CSeq"].method,
            request_uri=self.start_line.request_uri,
            realm=www_authenticate.realm,
            nonce=www_authenticate.nonce,
            algorithm=www_authenticate.algorithm,
            opaque=www_authenticate.opaque,
            qop=www_authenticate.qop,
            nc=1,
        )
        req = RequestMessage(start_line=self.start_line, headers=headers, body=[])
        return req


@dataclass()
class RegisterMessage(RequestMessage):
    @classmethod
    def create(
        cls,
        domain: str,
        username: str,
        transaction: "Transaction",
        expires: int = 300,
    ) -> Self:
        call_id_ = CallID(transaction.call_id)
        c_seq = CSeq(method=ClientMethod.REGISTER, c_seq=transaction.next_local_c_seq)
        from_ = From(
            display_name=username,
            from_=f"sip:{username}@{domain}",
            tag=transaction.local_tag,
        )
        if transaction.remote_tag:
            to = To(
                display_name=username,
                to=f"sip:{username}@{domain}",
                tag=transaction.remote_tag,
            )
        else:
            to = To(display_name=username, to=f"sip:{username}@{domain}")
        via = Via("SIP/2.0/UDP 192.168.0.137:60956", branch=transaction.branch)

        request = cls(
            start_line=RequestStartLine(
                method=ClientMethod.REGISTER,
                request_uri=f"sip:{domain}",
            ),
            headers=Headers(
                Max_Forwards=MaxForward(max_forward=70),
                From=from_,
                To=to,
                Call_ID=call_id_,
                CSeq=c_seq,
                Contact=Contact(
                    display_name=username,
                    contact=f"sip:{username}@192.168.0.137:60956;ob",
                ),
                Expires=Expires(expires=expires),
                Content_Length=ContentLength(content_length=0),
                Via=via,
                Allow="PRACK, INVITE, ACK, BYE, CANCEL, UPDATE, INFO, SUBSCRIBE, NOTIFY, REFER, MESSAGE, OPTIONS",
            ),
            body=[],
        )
        return request


@dataclass()
class UnRegisterMessage(RequestMessage):
    @classmethod
    def create(
        cls,
        domain: str,
        username: str,
        transaction: "Transaction",
    ) -> Self:
        return RegisterMessage.create(
            domain=domain, username=username, transaction=transaction, expires=0
        )


@dataclass()
class InviteMessage(RequestMessage):
    @classmethod
    def create(
        cls,
        target: str,
        domain: str,
        username: str,
        transaction: "Transaction",
    ) -> Self:
        call_id = CallID(transaction.call_id)
        c_seq = CSeq(method=ClientMethod.INVITE, c_seq=transaction.next_local_c_seq)
        from_ = From(
            display_name=username,
            from_=f"sip:{username}@{domain}",
            tag=transaction.local_tag,
        )
        if transaction.remote_tag:
            to = To(to=f"sip:{target}@{domain}", tag=transaction.remote_tag)
        else:
            to = To(to=f"sip:{target}@{domain}")
        via = Via("SIP/2.0/UDP 192.168.0.137:60956", branch=transaction.branch)

        request = cls(
            start_line=RequestStartLine(
                method=ClientMethod.INVITE,
                request_uri=f"sip:{target}@{domain}",
            ),
            headers=Headers(
                Max_Forwards=MaxForward(max_forward=70),
                From=from_,
                To=to,
                Call_ID=call_id,
                CSeq=c_seq,
                Contact=Contact(
                    display_name=username,
                    contact=f"sip:{username}@192.168.0.137:60956;ob",
                ),
                Content_Length=ContentLength(content_length=479),
                Via=via,
                Allow="PRACK, INVITE, ACK, BYE, CANCEL, UPDATE, INFO, SUBSCRIBE, NOTIFY, REFER, MESSAGE, OPTIONS",
            ),
            body=[
                "v=0",
                "o=- 3910726507 3910726507 IN IP4 192.168.0.137",
                "s=pjmedia",
                "b=AS:117",
                "t=0 0",
                "a=X-nat:0",
                "m=audio 4000 RTP/AVP 96 9 8 0 101 102",
                "c=IN IP4 192.168.0.137",
                "b=TIAS:96000",
                "a=rtcp:4001 IN IP4 192.168.0.137",
                "a=sendrecv",
                "a=rtpmap:96 opus/48000/2",
                "a=fmtp:96 useinbandfec=1",
                "a=rtpmap:9 G722/8000",
                "a=rtpmap:8 PCMA/8000",
                "a=rtpmap:0 PCMU/8000",
                "a=rtpmap:101 telephone-event/48000",
                "a=fmtp:101 0-16",
                "a=rtpmap:102 telephone-event/8000",
                "a=fmtp:102 0-16",
                "a=ssrc:402436570 cname:7791e39e0af6d766",
            ],
        )
        return request


@dataclass()
class AckMessage(RequestMessage):
    @classmethod
    def create(
        cls,
        target: str,
        domain: str,
        username: str,
        transaction: "Transaction",
    ) -> Self:
        call_id = CallID(transaction.call_id)
        c_seq = CSeq(method=ClientMethod.ACK, c_seq=transaction.next_local_c_seq)
        from_ = From(
            display_name=username,
            from_=f"sip:{username}@{domain}",
            tag=transaction.local_tag,
        )
        if transaction.remote_tag:
            to = To(to=f"sip:{target}@{domain}", tag=transaction.remote_tag)
        else:
            to = To(to=f"sip:{target}@{domain}")
        via = Via("SIP/2.0/UDP 192.168.0.137:60956", branch=transaction.branch)

        request = cls(
            start_line=RequestStartLine(
                method=ClientMethod.ACK,
                request_uri=f"sip:{target}@{domain}",
            ),
            headers=Headers(
                Max_Forwards=MaxForward(max_forward=70),
                From=from_,
                To=to,
                Call_ID=call_id,
                CSeq=c_seq,
                Content_Length=ContentLength(content_length=0),
                Via=via,
            ),
            body=[],
        )
        return request


@dataclass()
class ByeMessage(RequestMessage):
    @classmethod
    def create(
        cls,
        target: str,
        domain: str,
        username: str,
        transaction: "Transaction",
    ) -> Self:
        call_id = CallID(transaction.call_id)
        c_seq = CSeq(method=ClientMethod.BYE, c_seq=transaction.next_local_c_seq)
        from_ = From(
            display_name=username,
            from_=f"sip:{username}@{domain}",
            tag=transaction.local_tag,
        )
        if transaction.remote_tag:
            to = To(to=f"sip:{target}@{domain}", tag=transaction.remote_tag)
        else:
            to = To(to=f"sip:{target}@{domain}")
        via = Via("SIP/2.0/UDP 192.168.0.137:60956", branch=transaction.branch)

        request = cls(
            start_line=RequestStartLine(
                method=ClientMethod.BYE,
                request_uri=f"sip:{target}@{domain}",
            ),
            headers=Headers(
                Max_Forwards=MaxForward(max_forward=70),
                From=from_,
                To=to,
                Call_ID=call_id,
                CSeq=c_seq,
                Content_Length=ContentLength(content_length=0),
                Via=via,
            ),
            body=[],
        )
        return request
