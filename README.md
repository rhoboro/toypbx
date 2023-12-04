```bash
$ black -l 100 toypbx
$ isort --profile black toypbx
$ python3 -m unittest
```

```bash
# This e2e test is entirely for myself
$ E2E=true DOMAIN=un100 USER_NAME=6001 PASSWORD=unsecurepassword python3 -m unittest toypbx.tests.test_client.TestE2E.test_register_no_password
# The expire is 60 sec. If the register remains, re-test is failed.
$ E2E=true DOMAIN=un100 USER_NAME=6001 PASSWORD=unsecurepassword python3 -m unittest toypbx.tests.test_client.TestE2E.test_register_digest
```
