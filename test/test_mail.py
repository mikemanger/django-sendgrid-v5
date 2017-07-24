import base64
from email.MIMEImage import MIMEImage
import unittest

from django.conf import settings
from django.core.mail import EmailMessage, EmailMultiAlternatives

from sendgrid_backend.mail import SendgridBackend


settings.configure(
    EMAIL_BACKEND="sendgrid_backend.SendgridBackend",
    SENDGRID_API_KEY="DUMMY_API_KEY",
)


class TestMailGeneration(unittest.TestCase):

    def setUp(self):
        self.backend = SendgridBackend()
        self.maxDiff = None

    def test_EmailMessage(self):
        msg = EmailMessage(
            subject="Hello, World!",
            body="Hello, World!",
            from_email="Sam Smith <sam.smith@example.com>",
            to=["John Doe <john.doe@example.com>", "jane.doe@example.com"],
            cc=["Stephanie Smith <stephanie.smith@example.com>"],
            bcc=["Sarah Smith <sarah.smith@example.com>"],
            reply_to=["Sam Smith <sam.smith@example.com>"],
        )

        result = self.backend._build_sg_mail(msg)
        expected = {
            "personalizations": [{
                "to": [{
                    "email": "john.doe@example.com",
                    "name": "John Doe"
                }, {
                    "email": "jane.doe@example.com",
                }],
                "cc": [{
                    "email": "stephanie.smith@example.com",
                    "name": "Stephanie Smith"
                }],
                "bcc": [{
                    "email": "sarah.smith@example.com",
                    "name": "Sarah Smith"
                }],
                "subject": "Hello, World!"
            }],
            "from": {
                "email": "sam.smith@example.com",
                "name": "Sam Smith"
            },
            "reply_to": {
                "email": "sam.smith@example.com",
                "name": "Sam Smith"
            },
            "subject": "Hello, World!",
            "content": [{
                "type": "text/plain",
                "value": "Hello, World!"
            }]
        }

        self.assertDictEqual(result, expected)

    def test_EmailMultiAlternatives(self):
        msg = EmailMultiAlternatives(
            subject="Hello, World!",
            body="",
            from_email="Sam Smith <sam.smith@example.com>",
            to=["John Doe <john.doe@example.com>", "jane.doe@example.com"],
            cc=["Stephanie Smith <stephanie.smith@example.com>"],
            bcc=["Sarah Smith <sarah.smith@example.com>"],
            reply_to=["Sam Smith <sam.smith@example.com>"],
        )

        msg.attach_alternative("<body<div>Hello World!</div></body>", "text/html")
        result = self.backend._build_sg_mail(msg)
        expected = {
            "personalizations": [{
                "to": [{
                    "email": "john.doe@example.com",
                    "name": "John Doe"
                }, {
                    "email": "jane.doe@example.com",
                }],
                "cc": [{
                    "email": "stephanie.smith@example.com",
                    "name": "Stephanie Smith"
                }],
                "bcc": [{
                    "email": "sarah.smith@example.com",
                    "name": "Sarah Smith"
                }],
                "subject": "Hello, World!"
            }],
            "from": {
                "email": "sam.smith@example.com",
                "name": "Sam Smith"
            },
            "reply_to": {
                "email": "sam.smith@example.com",
                "name": "Sam Smith"
            },
            "subject": "Hello, World!",
            "content": [{
                "type": "text/html",
                "value": "<body<div>Hello World!</div></body>"
            }]
        }

        self.assertDictEqual(result, expected)

    def test_headers(self):
        pass

    def test_reply_to(self):
        kwargs = {
            "subject": "Hello, World!",
            "body": "Hello, World!",
            "from_email": "Sam Smith <sam.smith@example.com>",
            "to": ["John Doe <john.doe@example.com>"],
            "reply_to": ["Sam Smith <sam.smith@example.com>"],
            "headers": {"Reply-To": "Stephanie Smith <stephanie.smith@example.com>"}
        }

        # Test different values in Reply-To header and reply_to prop
        msg = EmailMessage(**kwargs)
        with self.assertRaises(ValueError):
            self.backend._build_sg_mail(msg)

        # Test different names (but same email) in Reply-To header and reply_to prop
        kwargs["headers"] = {"Reply-To": "Bad Name <sam.smith@example.com>"}
        msg = EmailMessage(**kwargs)
        with self.assertRaises(ValueError):
            self.backend._build_sg_mail(msg)

        # Test same name/email in both Reply-To header and reply_to prop
        kwargs["headers"] = {"Reply-To": "Sam Smith <sam.smith@example.com>"}
        msg = EmailMessage(**kwargs)
        result = self.backend._build_sg_mail(msg)
        self.assertDictEqual(result["reply_to"], {"email": "sam.smith@example.com", "name": "Sam Smith"})

    def test_mime(self):
        msg = EmailMultiAlternatives(
            subject="Hello, World!",
            body="",
            from_email="Sam Smith <sam.smith@example.com>",
            to=["John Doe <john.doe@example.com>", "jane.doe@example.com"],
        )

        content = '<body><img src="cid:linux_penguin" /></body>'
        msg.attach_alternative(content, "text/html")
        with open("test/linux-penguin.png", "rb") as f:
            img = MIMEImage(f.read())
            img.add_header("Content-ID", "linux_penguin")
            msg.attach(img)

        result = self.backend._build_sg_mail(msg)
        self.assertEqual(len(result["content"]), 1)
        self.assertDictEqual(result["content"][0], {"type": "text/html", "value": content})
        self.assertEqual(len(result["attachments"]), 1)
        with open("test/linux-penguin.png", "rb") as f:
            self.assertEqual(result["attachments"][0]["content"], base64.b64encode(f.read()))
        self.assertEqual(result["attachments"][0]["type"], "image/png")

    """
    todo: Implement these
    def test_attachments(self):
        pass
    """


if __name__ == "__main__":
    unittest.main()