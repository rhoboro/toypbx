import argparse
import time
from pprint import pprint

from toypbx.client import Client


def register(domain: str, username: str, password: str, expire: int, **kwargs) -> None:
    client = Client()
    response = client.register(
        domain=domain,
        username=username,
        password=password,
        expire=expire,
    )
    pprint(response)

    time.sleep(2)

    response = client.unregister(
        domain=domain,
        username=username,
        password=password,
    )
    pprint(response)


def unregister(domain: str, username: str, password: str, expire: int, **kwargs) -> None:
    response = Client().unregister(
        domain=domain,
        username=username,
        password=password,
    )
    pprint(response)


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
        default=60,
    )

    # UNREGISTER
    unregister_parser = client_subparsers.add_parser("unregister")
    unregister_parser.set_defaults(handler=unregister)
    unregister_parser.add_argument(
        "--domain",
        type=str,
        default="un100",
    )
    unregister_parser.add_argument(
        "--username",
        type=str,
        default="6001",
    )
    unregister_parser.add_argument(
        "--password",
        type=str,
        default="",
    )
    unregister_parser.add_argument(
        "--expire",
        type=int,
        default=60,
    )

    # SERVER
    server_parser = subparsers.add_parser("server")
    server_parser.set_defaults(handler=command_server)

    # parser.add_argument(
    #     "--domain",
    #     type=str,
    #     default="un100",
    #     help="スペース区切りのリスト",
    # )
    known, unknown = parser.parse_known_args()
    if handler := getattr(known, "handler", None):
        handler(**vars(known))


if __name__ == "__main__":
    main()
