import argparse
import time

from toypbx.client import Client


def register(domain: str, username: str, password: str, expire: int, **kwargs) -> None:
    client = Client(
        domain=domain,
        username=username,
        password=password,
    )
    with client.register(expire=expire):
        time.sleep(expire - 1)


def invite(domain: str, username: str, password: str, expire: int, **kwargs) -> None:
    client = Client(
        domain=domain,
        username=username,
        password=password,
    )
    with client.register(expire=expire):
        with client.invite() as dialog:
            time.sleep(expire - 1)


def command_server(*args, **kwargs):
    print(locals())


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--debug",
        "-d",
        action="store_true",
        default=False,
    )

    subparsers = parser.add_subparsers()
    client_parser = subparsers.add_parser("client")
    client_subparsers = client_parser.add_subparsers()

    # REGISTER
    register_parser = client_subparsers.add_parser("register")
    register_parser.set_defaults(handler=register)
    register_parser.add_argument(
        "--domain",
        type=str,
        default="un100",
    )
    register_parser.add_argument(
        "--username",
        type=str,
        default="6001",
    )
    register_parser.add_argument(
        "--password",
        type=str,
        default="",
    )
    register_parser.add_argument(
        "--expire",
        type=int,
        default=5,
    )

    # INVITE
    invite_parser = client_subparsers.add_parser("invite")
    invite_parser.set_defaults(handler=invite)
    invite_parser.add_argument(
        "--domain",
        type=str,
        default="un100",
    )
    invite_parser.add_argument(
        "--username",
        type=str,
        default="6001",
    )
    invite_parser.add_argument(
        "--password",
        type=str,
        default="",
    )
    invite_parser.add_argument(
        "--expire",
        type=int,
        default=5,
    )

    # SERVER
    server_parser = subparsers.add_parser("server")
    server_parser.set_defaults(handler=command_server)

    known, unknown = parser.parse_known_args()
    if handler := getattr(known, "handler", None):
        handler(**vars(known))


if __name__ == "__main__":
    main()
