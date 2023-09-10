import unittest


class TestRequestMessage(unittest.TestCase):
    def test_to_message(self):
        from toypbx.protocols.sip.message import (
            ClientMethod,
            Headers,
            RequestMessage,
            RequestStartLine,
        )

        actual = RequestMessage(
            start_line=RequestStartLine(
                method=ClientMethod.REGISTER,
                request_uri=f"sip:un100",
                sip_version="SIP/2.0",
            ),
            headers=Headers(
                Via="SIP/2.0/UDP 192.168.0.137:60956;rport;branch=z9hG4bKPjhRHw98trjD05PopYbBL6bj34Hci6DmTU",
                Max_Forwards=70,
                From="'6001' <sip:6001@un100>;tag=JRUu-hLceE3P8h2r0RVQKeJRZuviCTLX",
                To="'6001' <sip:6001@un100>",
                Call_ID="6eCTpQmxGa4gAWjUXhufRd-u0D9u.N5F",
                CSeq="46544 REGISTER",
                Contact="'6001' <sip:6001@192.168.0.137:60956;ob>",
                Expires=300,
                Allow="PRACK, INVITE, ACK, BYE, CANCEL, UPDATE, INFO, SUBSCRIBE, NOTIFY, REFER, MESSAGE, OPTIONS",
                Content_Length=0,
            ),
            body=[],
        )
        expected = """REGISTER sip:un100 SIP/2.0
Via: SIP/2.0/UDP 192.168.0.137:60956;rport;branch=z9hG4bKPjhRHw98trjD05PopYbBL6bj34Hci6DmTU
Max-Forwards: 70
From: "6001" <sip:6001@un100>;tag=JRUu-hLceE3P8h2r0RVQKeJRZuviCTLX
To: "6001" <sip:6001@un100>
Call-ID: 6eCTpQmxGa4gAWjUXhufRd-u0D9u.N5F
CSeq: 46544 REGISTER
Contact: "6001" <sip:6001@192.168.0.137:60956;ob>
Expires: 300
Allow: PRACK, INVITE, ACK, BYE, CANCEL, UPDATE, INFO, SUBSCRIBE, NOTIFY, REFER, MESSAGE, OPTIONS
Content-Length: 0
"""
        self.assertEqual(expected, actual.to_message())


class TestResponseMessage(unittest.TestCase):
    def test_from_raw(self):
        from toypbx.protocols.sip.message import (
            Headers,
            ResponseMessage,
            ResponseStartLine,
        )

        raw = """SIP/2.0 401 Unauthorized
Via: SIP/2.0/UDP 192.168.0.137:60956;rport=64377;received=172.17.0.1;branch=z9hG4bKPjhRHw98trjD05PopYbBL6bj34Hci6DmTU
Call-ID: 6eCTpQmxGa4gAWjUXhufRd-u0D9u.N5F
From: "6001" <sip:6001@un100>;tag=JRUu-hLceE3P8h2r0RVQKeJRZuviCTLX
To: "6001" <sip:6001@un100>;tag=z9hG4bKPjhRHw98trjD05PopYbBL6bj34Hci6DmTU
CSeq: 46544 REGISTER
WWW-Authenticate: Digest realm="asterisk",nonce="1694335639/87ec12ef29efc8eb6bed816924a8a45e",opaque="456759f668e20830",algorithm=MD5,qop="auth"
Server: Asterisk PBX 20.4.0
Content-Length:  0
"""

        actual = ResponseMessage.from_raw(raw)
        expected = ResponseMessage(
            start_line=ResponseStartLine(
                sip_version="SIP/2.0",
                status_code=401,
                reason_phrase="Unauthorized",
            ),
            headers=Headers(
                Via="SIP/2.0/UDP 192.168.0.137:60956;rport=64377;received=172.17.0.1;branch=z9hG4bKPjhRHw98trjD05PopYbBL6bj34Hci6DmTU",
                Call_ID="6eCTpQmxGa4gAWjUXhufRd-u0D9u.N5F",
                From='"6001" <sip:6001@un100>;tag=JRUu-hLceE3P8h2r0RVQKeJRZuviCTLX',
                To='"6001" <sip:6001@un100>;tag=z9hG4bKPjhRHw98trjD05PopYbBL6bj34Hci6DmTU',
                CSeq="46544 REGISTER",
                WWW_Authenticate='Digest realm="asterisk",nonce="1694335639/87ec12ef29efc8eb6bed816924a8a45e",opaque="456759f668e20830",algorithm=MD5,qop="auth"',
                Server="Asterisk PBX 20.4.0",
                Content_Length="0",
            ),
            body=[],
        )
        self.assertEqual(expected, actual)


class TestAuthorization(unittest.TestCase):
    def test_digest_response(self):
        from toypbx.protocols.sip.message import Authorization

        actual = Authorization.digest_response(
            "6001",
            "unsecurepassword",
            "asterisk",
            "REGISTER",
            "sip:un100",
            "1694340480/be2dcee2681e965161a7fdb1e3ca0d6c",
            "4uKBAw6V0O358p0K1Kf0UnMJGuppcwLd",
            1,
            "auth",
        )
        expected = "9566381df29daae0299427f6deae7b98"
        self.assertEqual(expected, actual)
