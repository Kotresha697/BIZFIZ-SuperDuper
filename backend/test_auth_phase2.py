import unittest

from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials

from backend import auth


class Phase2AuthenticationTests(unittest.TestCase):
    def test_client_token_has_client_role(self):
        token = auth.create_access_token({"sub": "client-1", "role": "client"})
        self.assertEqual(auth.decode_access_token(token)["role"], "client")

    def test_admin_token_has_admin_role(self):
        token = auth.create_access_token({"sub": "admin", "role": "admin"})
        self.assertEqual(auth.decode_access_token(token)["role"], "admin")

    def test_client_cannot_use_admin_dependency(self):
        token = auth.create_access_token({"sub": "client-1", "role": "client"})
        with self.assertRaises(HTTPException) as context:
            auth.get_admin_user(HTTPAuthorizationCredentials(
                scheme="Bearer", credentials=token
            ))

        self.assertEqual(context.exception.status_code, 403)

    def test_admin_cannot_use_client_dependency(self):
        token = auth.create_access_token({"sub": "admin", "role": "admin"})
        with self.assertRaises(HTTPException) as context:
            auth.get_client_user(HTTPAuthorizationCredentials(
                scheme="Bearer", credentials=token
            ))

        self.assertEqual(context.exception.status_code, 403)


if __name__ == "__main__":
    unittest.main()