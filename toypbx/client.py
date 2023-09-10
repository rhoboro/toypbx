from toypbx.net import send
from toypbx.protocols.sip.message import RegisterMessage, ResponseMessage


def register(
    username: str,
    password: str,
    domain: str,
):
    request = RegisterMessage.create(
        domain=domain,
        username=username,
        password=password,
    )
    response = ResponseMessage.from_raw(send(domain, 5060, request.to_message()))
    if (
        response.start_line.status_code == 401
        and "WWW-Authenticate" in response.headers
        and request.has_password()
    ):
        digest_request = request.digest(response)
        res = ResponseMessage.from_raw(send(domain, 5060, digest_request.to_message()))
        return res

    return response
