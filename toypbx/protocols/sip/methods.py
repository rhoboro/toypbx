from enum import StrEnum


class ClientMethod(StrEnum):
    INVITE = "INVITE"
    ACK = "ACK"
    BYE = "BYE"
    CANCEL = "CANCEL"
    REGISTER = "REGISTER"
    OPTIONS = "OPTIONS"

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}.{self.name}"
