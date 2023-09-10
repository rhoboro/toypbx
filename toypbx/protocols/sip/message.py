from dataclasses import dataclass
from typing import Self, cast

from .headers import *
from .methods import ClientMethod


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


@dataclass()
class ResponseMessage:
    start_line: ResponseStartLine
    headers: Headers
    body: list[str]

    @classmethod
    def from_raw(cls, raw_message: str) -> Self:
        headers = Headers()
        lines = raw_message.splitlines()
        sip_version, status_code, reason_phrase = lines[0].split(" ")
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


@dataclass()
class RegisterMessage(RequestMessage):
    username: str
    _password: str

    def has_password(self) -> bool:
        return bool(self._password)

    @classmethod
    def create(
        cls,
        domain: str,
        username: str,
        password: str = "",
    ) -> Self:
        request = RegisterMessage(
            start_line=RequestStartLine(
                method=ClientMethod.REGISTER,
                request_uri=f"sip:{domain}",
            ),
            headers=Headers(
                Max_Forwards=MaxForward(value=70),
                From=From(
                    display_name=username,
                    value=f"sip:{username}@{domain}",
                    tag="JRUu-hLceE3P8h2r0RVQKeJRZuviCTLX",
                ),
                To=To(
                    display_name=username,
                    value=f"sip:{username}@{domain}",
                ),
                Call_ID=CallID(value="6eCTpQmxGa4gAWjUXhufRd-u0D9u.N5F"),
                CSeq=CSeq(method=ClientMethod.REGISTER, value=46544),
                Contact=Contact(
                    display_name=username, value=f"sip:{username}@192.168.0.137:60956;ob"
                ),
                Expires=Expires(value=300),
                Content_Length=ContentLength(value=0),
                Via="SIP/2.0/UDP 192.168.0.137:60956;rport;branch=z9hG4bKPjhRHw98trjD05PopYbBL6bj34Hci6DmTU",
                Allow="PRACK, INVITE, ACK, BYE, CANCEL, UPDATE, INFO, SUBSCRIBE, NOTIFY, REFER, MESSAGE, OPTIONS",
            ),
            body=[],
            username=username,
            _password=password,
        )
        return request

    def digest(self, response: ResponseMessage) -> RequestMessage:
        www_authenticate = cast(WWWAuthenticate, response.headers.pop(WWWAuthenticate.name))

        headers = Headers(**self.headers)
        headers[CSeq.name] = cast(CSeq, headers[CSeq.name]).next()
        headers[Authorization.name] = Authorization(
            username=self.username,
            password=self._password,
            method=ClientMethod.REGISTER,
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
