from toypbx.net import send
from toypbx.protocols.sip.message import RegisterMessage, ResponseMessage


class Client:
    def __init__(self) -> None:
        self.context = {}
        self.local_tag = None
        self.remote_tag = None
        self.branch = None
        self.call_id = None
        self.local_c_seq = None
        self.remote_c_seq = None

    def register(
        self,
        username: str,
        password: str,
        domain: str,
        expire: int = 300,
    ) -> ResponseMessage:
        request = RegisterMessage.create(
            domain=domain,
            username=username,
            password=password,
            expire=expire,
        )
        response = ResponseMessage.from_raw(send(domain, 5060, request.to_message()))
        if (
            response.start_line.status_code == 401
            and "WWW-Authenticate" in response.headers
            and request.has_password()
        ):
            digest_request = request.digest(response)
            response = ResponseMessage.from_raw(send(domain, 5060, digest_request.to_message()))

        if response.start_line.status_code == 200:
            self.local_tag = request.headers["From"].tag
            self.local_c_seq = request.headers["CSeq"].value

            self.remote_tag = response.headers["To"].tag
            self.branch = response.headers["Via"].branch
            self.call_id = response.headers["Call-ID"].value
            self.remote_c_seq = response.headers["CSeq"].value

        return response

    def unregister(
        self,
        username: str,
        password: str,
        domain: str,
    ) -> ResponseMessage:
        request = RegisterMessage.create(
            domain=domain,
            username=username,
            password=password,
            expire=0,
            call_id=self.call_id,
            c_seq=self.local_c_seq + 2,
        )
        response = ResponseMessage.from_raw(send(domain, 5060, request.to_message()))
        if (
            response.start_line.status_code == 401
            and "WWW-Authenticate" in response.headers
            and request.has_password()
        ):
            digest_request = request.digest(response)
            response = ResponseMessage.from_raw(send(domain, 5060, digest_request.to_message()))

        if response.start_line.status_code == 200:
            self.local_tag = request.headers["From"].tag
            self.local_c_seq = request.headers["CSeq"].value

            self.remote_tag = response.headers["To"].tag
            self.branch = response.headers["Via"].branch
            self.call_id = response.headers["Call-ID"].value
            self.remote_c_seq = response.headers["CSeq"].value

        return response
