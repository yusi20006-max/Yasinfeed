import unittest
import os
import shutil
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock

from yasinfeed.engine import YasinFeedEngine
from yasinfeed.auth import AuthModule, hash_password, verify_password
from yasinfeed.models import User, Session, Article


class TestAuthModule(unittest.TestCase):

    def setUp(self):
        # Setup temporary DB path for testing
        self.test_dir = "tests/temp_auth_test"
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
        os.makedirs(self.test_dir, exist_ok=True)
        self.db_path = os.path.join(self.test_dir, "test_auth.db")

        # Setup engine with testing configurations
        self.engine = YasinFeedEngine()
        self.engine.config = {
            "storage": {
                "type": "sqlite",
                "path": self.db_path
            },
            "auth": {
                "token_expiry_hours": 1,
                "min_password_length": 6,
                "pbkdf2_iterations": 1000  # Lower count for fast testing
            },
            "api": {
                "host": "127.0.0.1",
                "port": 8000
            }
        }

        # Initialize engine and modules
        from yasinfeed.storage import StorageModule
        from yasinfeed.models import ModelsModule
        from yasinfeed.auth import AuthModule
        from yasinfeed.api import ApiModule

        self.engine.register_module(StorageModule)
        self.engine.register_module(ModelsModule)
        self.engine.register_module(AuthModule)
        self.engine.register_module(ApiModule)

        # Instantiate modules manually since initialize is customized
        for m_cls in self.engine.module_classes:
            name = m_cls.get_module_name()
            self.engine.modules[name] = m_cls(self.engine)

        for name, module in self.engine.modules.items():
            self.assertTrue(module.initialize())

        self.auth_module = self.engine.modules["auth"]
        self.storage_module = self.engine.modules["storage"]
        self.api_module = self.engine.modules["api"]

    def tearDown(self):
        # Close connection and cleanup
        self.engine.stop()
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_pbkdf2_password_hashing(self):
        password = "securePassword123"
        pw_hash, salt_hex = hash_password(password, iterations=1000)

        self.assertIsNotNone(pw_hash)
        self.assertIsNotNone(salt_hex)
        self.assertNotEqual(password, pw_hash)

        # Verify correct verification
        self.assertTrue(verify_password(password, pw_hash, salt_hex, iterations=1000))

        # Verify invalid password fails verification
        self.assertFalse(verify_password("wrongPassword", pw_hash, salt_hex, iterations=1000))

        # Check random unique salts
        _, salt_hex_2 = hash_password(password, iterations=1000)
        self.assertNotEqual(salt_hex, salt_hex_2)

    def test_register_user_success(self):
        username = "jules_test"
        password = "testSecretPassword"
        user = self.auth_module.register_user(username, password)

        self.assertEqual(user.username, username)
        self.assertNotEqual(user.password_hash, password)

        # Verify saved correctly in storage
        retrieved = self.storage_module.get_user(user.id)
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.username, username)

        retrieved_by_uname = self.storage_module.get_user_by_username(username)
        self.assertIsNotNone(retrieved_by_uname)
        self.assertEqual(retrieved_by_uname.id, user.id)

    def test_register_user_duplicates_and_validation(self):
        username = "duplicate_user"
        password = "strongPassword"
        self.auth_module.register_user(username, password)

        # Register duplicate should raise ValueError
        with self.assertRaises(ValueError) as ctx:
            self.auth_module.register_user(username, "anotherPassword")
        self.assertIn("already registered", str(ctx.exception))

        # Empty username check
        with self.assertRaises(ValueError) as ctx:
            self.auth_module.register_user("  ", "password")
        self.assertIn("Username cannot be empty", str(ctx.exception))

        # Short password check
        with self.assertRaises(ValueError) as ctx:
            self.auth_module.register_user("valid_uname", "short")
        self.assertIn("Password must be at least", str(ctx.exception))

    def test_login_success(self):
        username = "login_test"
        password = "validPassword"
        self.auth_module.register_user(username, password)

        # Authenticate
        session = self.auth_module.login(username, password)
        self.assertIsNotNone(session)
        self.assertIsNotNone(session.token)

        # Verify session is persisted
        stored_session = self.storage_module.get_session(session.token)
        self.assertIsNotNone(stored_session)
        self.assertEqual(stored_session.user_id, session.user_id)

    def test_login_failures(self):
        username = "failure_test"
        password = "correctPassword"
        self.auth_module.register_user(username, password)

        # Login with wrong password
        session = self.auth_module.login(username, "wrongPassword")
        self.assertIsNone(session)

        # Login non-existent user
        session = self.auth_module.login("non_existent", "somePassword")
        self.assertIsNone(session)

    def test_logout_session_invalidation(self):
        username = "logout_test"
        password = "secretPassword"
        self.auth_module.register_user(username, password)
        session = self.auth_module.login(username, password)

        token = session.token
        self.assertIsNotNone(self.storage_module.get_session(token))

        # Logout
        success = self.auth_module.logout(token)
        self.assertTrue(success)

        # Verify invalidated
        self.assertIsNone(self.storage_module.get_session(token))

        # Logout again with same token should fail
        self.assertFalse(self.auth_module.logout(token))

    def test_session_token_authentication_and_expiration(self):
        username = "expiry_test"
        password = "expiryPassword"
        user = self.auth_module.register_user(username, password)
        session = self.auth_module.login(username, password)

        # Authenticate active token
        authed_user = self.auth_module.authenticate_token(session.token)
        self.assertIsNotNone(authed_user)
        self.assertEqual(authed_user.username, username)

        # Authenticate invalid token
        self.assertIsNone(self.auth_module.authenticate_token("invalid_token"))

        # Authenticate expired token
        expired_session = Session(
            token="expired_token",
            user_id=user.id,
            expires_at=datetime.now(timezone.utc) - timedelta(seconds=1),
            created_at=datetime.now(timezone.utc) - timedelta(hours=2)
        )
        self.storage_module.save_session(expired_session)

        authed_user_expired = self.auth_module.authenticate_token("expired_token")
        self.assertIsNone(authed_user_expired)

        # Expired session should have been removed from storage
        self.assertIsNone(self.storage_module.get_session("expired_token"))

    def test_api_handlers_simulation(self):
        # 1. Test POST /api/auth/register simulator
        reg_payload = {"username": "api_user", "password": "secure_password"}
        res, code = self.api_module.handle_register(reg_payload)
        self.assertEqual(code, 201)
        self.assertEqual(res["status"], "success")

        # Test duplicate register
        res, code = self.api_module.handle_register(reg_payload)
        self.assertEqual(code, 400)
        self.assertEqual(res["status"], "error")

        # 2. Test POST /api/auth/login simulator
        login_payload = {"username": "api_user", "password": "secure_password"}
        res, code = self.api_module.handle_login(login_payload)
        self.assertEqual(code, 200)
        self.assertEqual(res["status"], "success")
        token = res["data"]["token"]
        self.assertIsNotNone(token)

        # Test login failure
        res, code = self.api_module.handle_login({"username": "api_user", "password": "wrong"})
        self.assertEqual(code, 401)

        # 3. Test GET /api/feed simulator (protected route)
        # Store mock article first
        art = Article(
            id="art-api-test",
            source_id="src-api-test",
            title="API Security",
            content="Secure authorization integrations",
            original_url="https://example.com/api",
            published_at=datetime.now()
        )
        self.storage_module.save_article(art)

        # Unauthorized request
        headers = {}
        res, code = self.api_module.handle_get_articles(headers)
        self.assertEqual(code, 401)

        # Authorized request with Bearer token
        headers = {"Authorization": f"Bearer {token}"}
        res, code = self.api_module.handle_get_articles(headers)
        self.assertEqual(code, 200)
        self.assertEqual(res["status"], "success")
        self.assertEqual(res["user"], "api_user")
        self.assertTrue(len(res["data"]) >= 1)
        self.assertEqual(res["data"][0]["id"], "art-api-test")


if __name__ == "__main__":
    unittest.main()
