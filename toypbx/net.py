import socket


def send(domain: str, port: int, message: str) -> str:
    target_host = domain
    target_port = port

    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as client:
        client.sendto(message.encode(), (target_host, target_port))
        data, addr = client.recvfrom(4096)

    response = data.decode("utf-8")
    return response
