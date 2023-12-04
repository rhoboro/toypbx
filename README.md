# ToyPBX

```bash
$ black -l 100 toypbx
$ isort --profile black toypbx
$ python3 -m unittest
```

```bash
# This e2e test is entirely for myself
$ E2E=true DOMAIN=un100 USER_NAME=6001 PASSWORD=unsecurepassword python3 -m unittest toypbx.tests.test_client.TestE2E.test_register_no_password
$ E2E=true DOMAIN=un100 USER_NAME=6001 PASSWORD=unsecurepassword python3 -m unittest toypbx.tests.test_client.TestE2E.test_register_digest
```

```bash
# REGISTER -> sleep -> UNREGISTER
$ python3 -m toypbx client register --password unsecurepassword
```

## How to use

```python
from toypbx.client import Client

client = Client(domain=..., username=..., password=...)
with client.register(expire=60):  # REGISTER
    with client.invite() as dialog:  # INVITE
        ...
        # BYE
    # UNREGISTER
```