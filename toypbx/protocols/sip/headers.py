import uuid
from dataclasses import dataclass, field
from hashlib import md5
from random import randint
from typing import Self

from .methods import ClientMethod

__all__ = [
    "Authorization",
    "CSeq",
    "CallID",
    "Contact",
    "ContentLength",
    "Expires",
    "From",
    "General",
    "Header",
    "Headers",
    "HeaderFactory",
    "MaxForward",
    "To",
    "Via",
    "WWWAuthenticate",
]


class Header:
    name: str

    @classmethod
    def parse(cls, raw, name: str | None = None) -> Self:
        raise NotImplementedError()


class Headers(dict[str, Header]):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__()
        for key, value in kwargs.items():
            if isinstance(value, Header):
                self[value.name] = value
            else:
                header = HeaderFactory(key, str(value).strip())
                self[header.name] = header


@dataclass(frozen=True)
class MaxForward(Header):
    max_forward: int = 70
    name: str = "Max-Forwards"
    lower_name: str = "max_forwards"

    def __str__(self) -> str:
        return f"{self.max_forward}"

    @classmethod
    def parse(cls, raw, name: str | None = None) -> Self:
        return cls(max_forward=int(raw))


@dataclass(frozen=True)
class ContentLength(Header):
    content_length: int = 0
    name: str = "Content-Length"
    lower_name: str = "content_length"

    def __str__(self) -> str:
        return f"{self.content_length}"

    @classmethod
    def parse(cls, raw, name: str | None = None) -> Self:
        return cls(content_length=int(raw))


@dataclass(frozen=True)
class From(Header):
    from_: str
    tag: str = field(default_factory=lambda: str(uuid.uuid4()))
    display_name: str | None = None
    name: str = "From"
    lower_name: str = "from"

    def __str__(self) -> str:
        if self.display_name:
            return f'"{self.display_name}" <{self.from_}>;tag={self.tag}'
        else:
            return f"<{self.from_}>;tag={self.tag}"

    @classmethod
    def parse(cls, raw, name: str | None = None) -> Self:
        if " " in raw:
            raw_display_name, raw = raw.split(" ", 1)
            display_name = raw_display_name.replace("'", "").replace('"', "")
        else:
            display_name = None
        value, tag = raw.split(";", 1)
        return cls(
            display_name=display_name,
            from_=value.replace("<", "").replace(">", ""),
            tag=tag.replace("tag=", ""),
        )

    @classmethod
    def gen_tag(cls) -> str:
        return str(uuid.uuid4())


@dataclass(frozen=True)
class To(Header):
    to: str
    tag: str = ""
    display_name: str | None = None
    name: str = "To"
    lower_name: str = "to"

    def __str__(self) -> str:
        if self.display_name:
            v = f'"{self.display_name}" <{self.to}>'
        else:
            v = f"<{self.to}>"
        if self.tag:
            return f"{v};tag={self.tag}"
        else:
            return v

    @classmethod
    def parse(cls, raw, name: str | None = None) -> Self:
        if " " in raw:
            raw_display_name, raw = raw.split(" ", 1)
            display_name = raw_display_name.replace("'", "").replace('"', "")
        else:
            display_name = None
        if ";" in raw:
            to, tag = raw.split(";", 1)
        else:
            to, tag = raw, None
        return cls(
            display_name=display_name,
            to=to.replace("<", "").replace(">", ""),
            tag=tag.replace("tag=", "") if tag else None,
        )


@dataclass(frozen=True)
class Contact(Header):
    contact: str
    display_name: str | None = None
    name: str = "Contact"
    lower_name: str = "contact"

    def __str__(self) -> str:
        if self.display_name:
            return f'"{self.display_name}" <{self.contact}>'
        else:
            return f"<{self.contact}>"

    @classmethod
    def parse(cls, raw, name: str | None = None) -> Self:
        if " " in raw:
            raw_display_name, raw = raw.split(" ", 1)
            display_name = raw_display_name.replace("'", "").replace('"', "")
        else:
            display_name = None
        value = raw
        return cls(
            display_name=display_name,
            contact=value.replace("<", "").replace(">", ""),
        )


@dataclass(frozen=True)
class CallID(Header):
    call_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = "Call-ID"
    lower_name: str = "call_id"

    def __str__(self) -> str:
        return self.call_id

    @classmethod
    def parse(cls, raw, name: str | None = None) -> Self:
        return cls(call_id=raw)

    @classmethod
    def gen_call_id(cls) -> str:
        return str(uuid.uuid4())


@dataclass(frozen=True)
class CSeq(Header):
    method: ClientMethod
    c_seq: int = field(default_factory=lambda: randint(1, 2 ^ 31 - 1))
    name: str = "CSeq"
    lower_name: str = "cseq"

    def __str__(self) -> str:
        return f"{self.c_seq} {self.method}"

    def next(self) -> Self:
        return CSeq(
            method=self.method,
            c_seq=self.c_seq + 1,
        )

    @classmethod
    def parse(cls, raw, name: str | None = None) -> Self:
        value, method = raw.split(" ")
        return cls(c_seq=int(value), method=ClientMethod[method])

    @classmethod
    def gen_c_seq(cls) -> int:
        return randint(1, 2 ^ 31 - 1)


@dataclass(frozen=True)
class Via(Header):
    via: str
    branch: str = field(default_factory=lambda: "z9hG4bK" + uuid.uuid4().hex)
    rport: str | None = None
    name: str = "Via"
    lower_name: str = "via"

    def __str__(self) -> str:
        if self.rport:
            return f"{self.via};rport={self.rport};branch={self.branch}"
        else:
            return f"{self.via};rport;branch={self.branch}"

    @classmethod
    def parse(cls, raw, name: str | None = None) -> Self:
        branch = ""
        rport = None
        for p in raw.split(";"):
            if p.startswith("branch="):
                _, branch = p.split("=", 1)
            if p.startswith("rport="):
                _, rport = p.split("=", 1)
        if not branch.startswith("z9hG4bK"):
            raise ValueError("branch must starts with z9hG4bKPj")
        value = raw.split(";")[0]
        return cls(via=value, rport=rport, branch=branch)

    @classmethod
    def gen_branch(cls) -> str:
        return "z9hG4bK" + uuid.uuid4().hex


@dataclass(frozen=True)
class WWWAuthenticate(Header):
    realm: str
    nonce: str
    opaque: str
    algorithm: str
    qop: str
    name: str = "WWW-Authenticate"
    lower_name: str = "www_authenticate"

    def __str__(self) -> str:
        return f'Digest realm="{self.realm}",nonce="{self.nonce}",opaque="{self.opaque}",algorithm={self.algorithm},qop="{self.qop}"'

    @classmethod
    def parse(cls, raw, name: str | None = None) -> Self:
        params = {}
        _, values = raw.split(" ", 1)
        for kv in values.split(","):
            key, value = kv.split("=", 1)
            params[key] = value.replace('"', "")
        return cls(**params)


@dataclass(frozen=True)
class Authorization(Header):
    username: str
    password: str
    method: ClientMethod
    request_uri: str
    realm: str
    nonce: str
    algorithm: str
    opaque: str
    qop: str
    cnonce: str = field(default_factory=lambda: "4uKBAw6V0O358p0K1Kf0UnMJGuppcwLd")
    nc: int = 1
    name: str = "Authorization"
    lower_name: str = "authorization"

    def __str__(self) -> str:
        return f'Digest username="{self.username}",realm="{self.realm}",nonce="{self.nonce}",uri="{self.request_uri}",response="{self._response}",algorithm={self.algorithm},cnonce="{self.cnonce}",opaque="{self.opaque}",qop={self.qop},nc={self.nc:08}'

    @classmethod
    def parse(cls, raw, name: str | None = None) -> Self:
        params = {}
        _, values = raw.split(" ", 1)
        for kv in values.split(","):
            key, value = kv.split("=", 1)
            params[key] = value.replace('"', "")
        return cls(**params)

    @property
    def _response(self) -> str:
        return self.digest_response(
            self.username,
            self.password,
            self.realm,
            self.method,
            self.request_uri,
            self.nonce,
            self.cnonce,
            self.nc,
            self.qop,
        )

    @classmethod
    def digest_response(
        cls,
        username: str,
        password: str,
        realm: str,
        method: str,
        request_uri: str,
        nonce: str,
        cnonce: str,
        nc: int,
        qop: str,
    ) -> str:
        def md5hex(a: str):
            return md5(a.encode("utf-8")).hexdigest()

        a1 = f"{username}:{realm}:{password}"
        a2 = f"{method}:{request_uri}"
        a3 = f"{md5hex(a1)}:{nonce}:{nc:08}:{cnonce}:{qop}:{md5hex(a2)}"
        return md5hex(a3)


@dataclass(frozen=True)
class Expires(Header):
    expires: int
    name: str = "Expires"
    lower_name: str = "expires"

    def __str__(self) -> str:
        return f"{self.expires}"

    @classmethod
    def parse(cls, raw, name: str | None = None) -> Self:
        return cls(expires=int(raw))


@dataclass(frozen=True)
class General(Header):
    value: str
    name: str

    def __str__(self) -> str:
        return f"{self.value}"

    @classmethod
    def parse(cls, raw: str, name: str | None = None) -> Self:
        if not name:
            raise RuntimeError("name")

        return cls(value=raw, name=name)


def _header_factory(key, raw) -> Header:
    match key.replace("-", "_").lower():
        case Expires.lower_name:
            return Expires.parse(raw)
        case From.lower_name:
            return From.parse(raw)
        case To.lower_name:
            return To.parse(raw)
        case Contact.lower_name:
            return Contact.parse(raw)
        case MaxForward.lower_name:
            return MaxForward.parse(raw)
        case CallID.lower_name:
            return CallID.parse(raw)
        case CSeq.lower_name:
            return CSeq.parse(raw)
        case Via.lower_name:
            return Via.parse(raw)
        case WWWAuthenticate.lower_name:
            return WWWAuthenticate.parse(raw)
        case Authorization.lower_name:
            return Authorization.parse(raw)
        case ContentLength.lower_name:
            return ContentLength.parse(raw)
        case _:
            return General.parse(raw, name=key)


HeaderFactory = _header_factory
