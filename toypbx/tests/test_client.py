import os
import unittest


@unittest.skipUnless(os.getenv("E2E"), "E2E")
class TestE2E(unittest.TestCase):
    def test_register_no_password(self):
        from toypbx.client import Client
        from toypbx.protocols.sip.message import ResponseMessage

        domain = os.getenv("DOMAIN")
        username = os.getenv("USER_NAME")

        actual = Client().register(
            domain=domain,
            username=username,
            password="",
            expire=0,
        )
        branch = actual.headers["Via"].branch
        call_id = actual.headers["Call-ID"].value
        local_tag = actual.headers["From"].tag
        remote_tag = actual.headers["To"].tag
        c_seq = actual.headers["CSeq"].value

        expected = ResponseMessage.from_raw(
            f"""SIP/2.0 401 Unauthorized
Via: SIP/2.0/UDP 192.168.0.137:60956;rport=64377;received=172.17.0.1;branch={branch}
Call-ID: {call_id}
From: "{username}" <sip:{username}@{domain}>;tag={local_tag}
To: "{username}" <sip:{username}@{domain}>;tag={remote_tag}
CSeq: {c_seq} REGISTER
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
        from toypbx.client import Client
        from toypbx.protocols.sip.message import ResponseMessage

        domain = os.getenv("DOMAIN")
        username = os.getenv("USER_NAME")
        password = os.getenv("PASSWORD", "")
        expire = 60

        actual = Client().register(
            domain=domain,
            username=username,
            password=password,
            expire=expire,
        )
        branch = actual.headers["Via"].branch
        call_id = actual.headers["Call-ID"].value
        local_tag = actual.headers["From"].tag
        remote_tag = actual.headers["To"].tag
        c_seq = actual.headers["CSeq"].value

        expected = ResponseMessage.from_raw(
            f"""SIP/2.0 200 OK
Via: SIP/2.0/UDP 192.168.0.137:60956;rport=51029;received=172.17.0.1;branch={branch}
Call-ID: {call_id}
From: "{username}" <sip:{username}@{domain}>;tag={local_tag}
To: "{username}" <sip:{username}@{domain}>;tag={remote_tag}
CSeq: {c_seq} REGISTER
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
