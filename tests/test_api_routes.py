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


class ApiRoutesTest(unittest.TestCase):
    def test_strategy_routes_filter_by_current_user(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            clear_app_modules()
            os.environ["QUANT_PLATFORM_DATABASE_URL"] = (
                f"sqlite:///{Path(tmp_dir) / 'test.db'}"
            )

            from app.api.strategies import (
                create_strategy_item,
                get_strategy_item,
                list_strategy_items,
            )
            from app.core.database import SessionLocal, init_db
            from app.schemas.strategy import StrategyCreate
            from app.services.strategy_service import seed_builtin_strategies
            from app.services.user_service import ensure_system_user

            init_db()
            with SessionLocal() as db:
                ensure_system_user(db)
                seed_builtin_strategies(db)
                custom = create_strategy_item(
                    StrategyCreate(
                        name="路由层策略",
                        strategy_type="custom_code",
                        code="def generate_signals(klines, params):\n    return []\n",
                        default_params={},
                        status="active",
                    ),
                    db=db,
                    user_id="dev-user",
                )

                visible = list_strategy_items(db=db, user_id="dev-user")
                other_visible = list_strategy_items(db=db, user_id="other-user")

                self.assertIn("ma-cross-default", [item.id for item in visible])
                self.assertIn(custom.id, [item.id for item in visible])
                self.assertIn("ma-cross-default", [item.id for item in other_visible])
                self.assertNotIn(custom.id, [item.id for item in other_visible])
                with self.assertRaises(Exception) as context:
                    get_strategy_item(custom.id, db=db, user_id="other-user")
                self.assertEqual(context.exception.status_code, 404)


if __name__ == "__main__":
    unittest.main()
