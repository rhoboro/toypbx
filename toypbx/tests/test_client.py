import os
import unittest


@unittest.skipUnless(os.getenv("E2E"), "E2E")
class TestE2E(unittest.TestCase):
    def test_register_no_password(self):
        from toypbx.client import register
        from toypbx.protocols.sip.message import ResponseMessage

        domain = os.getenv("DOMAIN")
        username = os.getenv("USER_NAME")

        actual = register(
            domain=domain,
            username=username,
            password="",
            expire=0,
        )
        expected = ResponseMessage.from_raw(
            f"""SIP/2.0 401 Unauthorized
Via: SIP/2.0/UDP 192.168.0.137:60956;rport=64377;received=172.17.0.1;branch=z9hG4bKPjhRHw98trjD05PopYbBL6bj34Hci6DmTU
Call-ID: 6eCTpQmxGa4gAWjUXhufRd-u0D9u.N5F
From: "{username}" <sip:{username}@{domain}>;tag=JRUu-hLceE3P8h2r0RVQKeJRZuviCTLX
To: "{username}" <sip:{username}@{domain}>;tag=z9hG4bKPjhRHw98trjD05PopYbBL6bj34Hci6DmTU
CSeq: 46544 REGISTER
WWW-Authenticate: Digest realm="asterisk",nonce="1694335639/87ec12ef29efc8eb6bed816924a8a45e",opaque="456759f668e20830",algorithm=MD5,qop="auth"
Server: Asterisk PBX 20.4.0
Content-Length:  0"""
        )

        expected.headers["WWW-Authenticate"] = None
        actual.headers["WWW-Authenticate"] = None
        expected.headers["Via"] = None
        actual.headers["Via"] = None
        self.assertEqual(expected, actual)

    def test_register_digest(self):
        from toypbx.client import register
        from toypbx.protocols.sip.message import ResponseMessage

        domain = os.getenv("DOMAIN")
        username = os.getenv("USER_NAME")
        password = os.getenv("PASSWORD", "")
        expire = 60

        actual = register(
            domain=domain,
            username=username,
            password=password,
            expire=expire,
        )
        expected = ResponseMessage.from_raw(
            f"""SIP/2.0 200 OK
Via: SIP/2.0/UDP 192.168.0.137:60956;rport=51029;received=172.17.0.1;branch=z9hG4bKPjhRHw98trjD05PopYbBL6bj34Hci6DmTU
Call-ID: 6eCTpQmxGa4gAWjUXhufRd-u0D9u.N5F
From: "{username}" <sip:{username}@{domain}>;tag=JRUu-hLceE3P8h2r0RVQKeJRZuviCTLX
To: "{username}" <sip:{username}@{domain}>;tag=z9hG4bKPjhRHw98trjD05PopYbBL6bj34Hci6DmTU
CSeq: 46545 REGISTER
Date: Sun, 10 Sep 2023 11:36:06 GMT
Contact: <sip:{username}@192.168.0.137:60956;ob>;expires={expire - 1}
Expires: {expire}
Server: Asterisk PBX 20.4.0
Content-Length:  0"""
        )

        expected.headers["Date"] = None
        actual.headers["Date"] = None
        expected.headers["Via"] = None
        actual.headers["Via"] = None
        self.assertEqual(expected, actual)
