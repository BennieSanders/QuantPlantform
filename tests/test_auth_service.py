import os
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory


PROJECT_ROOT = Path(__file__).resolve().parents[1]
BACKEND_ROOT = PROJECT_ROOT / "backend"

sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(BACKEND_ROOT))


def clear_app_modules() -> None:
    for module_name in list(sys.modules):
        if module_name == "app" or module_name.startswith("app."):
            del sys.modules[module_name]


class AuthServiceTest(unittest.TestCase):
    def test_register_login_and_token_user_resolution(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            clear_app_modules()
            os.environ["QUANT_PLATFORM_DATABASE_URL"] = (
                f"sqlite:///{Path(tmp_dir) / 'test.db'}"
            )
            os.environ["QUANT_PLATFORM_AUTH_SECRET"] = "test-secret"

            from app.core.database import SessionLocal, init_db
            from app.core.security import create_access_token, get_current_user, verify_password
            from app.models.user import User
            from app.schemas.auth import UserCreate
            from app.services.user_service import authenticate_user, create_user

            init_db()
            with SessionLocal() as db:
                created = create_user(
                    db,
                    UserCreate(username="alice", password="correct-password"),
                )
                self.assertEqual(created.username, "alice")

                user = db.get(User, created.id)
                self.assertIsNotNone(user)
                assert user is not None
                self.assertTrue(verify_password("correct-password", user.password_hash))

                token = authenticate_user(db, "alice", "correct-password")
                self.assertEqual(token.user.id, created.id)
                self.assertTrue(token.access_token)

                with self.assertRaisesRegex(ValueError, "Username already exists"):
                    create_user(
                        db,
                        UserCreate(username="alice", password="another-password"),
                    )
                with self.assertRaisesRegex(ValueError, "Invalid username or password"):
                    authenticate_user(db, "alice", "wrong-password")

                request = RequestStub({"authorization": f"Bearer {create_access_token(created.id)}"})
                current_user = get_current_user(request, db=db)
                self.assertEqual(current_user.id, created.id)

    def test_auth_required_when_dev_fallback_disabled(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            clear_app_modules()
            os.environ["QUANT_PLATFORM_DATABASE_URL"] = (
                f"sqlite:///{Path(tmp_dir) / 'test.db'}"
            )
            os.environ["QUANT_PLATFORM_ENV"] = "production"
            os.environ["QUANT_PLATFORM_ALLOW_DEV_AUTH_FALLBACK"] = "false"

            from app.core.database import SessionLocal, init_db
            from app.core.security import get_current_user

            init_db()
            with SessionLocal() as db:
                with self.assertRaises(Exception) as context:
                    get_current_user(RequestStub({}), db=db)
                self.assertEqual(context.exception.status_code, 401)


class RequestStub:
    def __init__(self, headers: dict[str, str]) -> None:
        self.headers = headers


if __name__ == "__main__":
    unittest.main()
