import unittest

from demo_service.auth import ExpiredTokenError, login, validate_token


class AuthenticationTests(unittest.TestCase):
    def test_valid_credential_returns_200(self):
        self.assertEqual(login("demo-user:2000", 1000), {"status": 200, "user": "demo-user"})

    def test_expired_credential_returns_401(self):
        self.assertEqual(login("demo-user:900", 1000)["status"], 401)

    def test_expiry_boundary_returns_401(self):
        self.assertEqual(login("demo-user:1000", 1000)["status"], 401)

    def test_invalid_credential_returns_401(self):
        self.assertEqual(login("invalid-demo-input", 1000)["status"], 401)

    def test_empty_username_returns_401(self):
        self.assertEqual(login(":2000", 1000)["status"], 401)

    def test_validator_reports_expiration(self):
        with self.assertRaises(ExpiredTokenError):
            validate_token("demo-user:900", 1000)
