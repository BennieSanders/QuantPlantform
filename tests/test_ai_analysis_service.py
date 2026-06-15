import os
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

import httpx


PROJECT_ROOT = Path(__file__).resolve().parents[1]
BACKEND_ROOT = PROJECT_ROOT / "backend"
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(BACKEND_ROOT))


def clear_app_modules() -> None:
    for module_name in list(sys.modules):
        if module_name == "app" or module_name.startswith("app."):
            del sys.modules[module_name]


class AiAnalysisServiceTest(unittest.TestCase):
    def test_analysis_mode_switch_uses_requested_provider(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            clear_app_modules()
            os.environ["QUANT_PLATFORM_DATABASE_URL"] = (
                f"sqlite:///{Path(tmp_dir) / 'test.db'}"
            )
            previous_openai_key = os.environ.get("QUANT_PLATFORM_OPENAI_API_KEY")
            previous_gemini_key = os.environ.get("QUANT_PLATFORM_GEMINI_API_KEY")
            os.environ["QUANT_PLATFORM_OPENAI_API_KEY"] = "test-key"
            os.environ["QUANT_PLATFORM_GEMINI_API_KEY"] = "test-key"

            from app.core.database import SessionLocal, init_db
            from app.schemas.backtest import BacktestRequest
            from app.services import ai_analysis_service
            from app.services.backtest_service import run_backtest
            from app.services.strategy_service import seed_builtin_strategies
            from app.services.user_service import ensure_system_user

            init_db()
            with SessionLocal() as db:
                ensure_system_user(db)
                seed_builtin_strategies(db)
                backtest = run_backtest(
                    BacktestRequest(
                        symbol="BTCUSDT",
                        timeframe="1d",
                        strategy_id="ma-cross-default",
                        start_date="2024-01-01",
                        end_date="2024-12-31",
                        initial_cash=10000,
                        params={"short_window": 7, "long_window": 30},
                    ),
                    db,
                    user_id="dev-user",
                )

                local = ai_analysis_service.analyze_backtest(backtest.backtest_id, db, "dev-user", mode="local")
                self.assertIsNotNone(local)
                assert local is not None
                self.assertEqual(local.provider, "local-quant-recommender-v2")

                original = ai_analysis_service._build_openai_analysis
                original_gemini = ai_analysis_service._build_gemini_analysis
                try:
                    ai_analysis_service._build_gemini_analysis = lambda record, settings: ai_analysis_service.AnalysisDraft(
                        provider=f"gemini:{settings.gemini_model}",
                        summary="gemini summary",
                        risk_level="low",
                        analysis_type="trend_following",
                        readiness="paper",
                        score=90,
                        confidence=0.93,
                        strengths=["gemini strength"],
                        warnings=["gemini warning"],
                        recommendations=["gemini recommendation"],
                        fit_profile=["gemini fit"],
                        avoid_profile=["gemini avoid"],
                        execution_plan=["gemini plan"],
                        suggested_params={"short_window": 6, "long_window": 24},
                    )
                    gemini = ai_analysis_service.analyze_backtest(
                        backtest.backtest_id, db, "dev-user", mode="gemini"
                    )
                    self.assertIsNotNone(gemini)
                    assert gemini is not None
                    self.assertTrue(gemini.provider.startswith("gemini:"))
                    self.assertEqual(gemini.summary, "gemini summary")

                    ai_analysis_service._build_openai_analysis = lambda record, settings: ai_analysis_service.AnalysisDraft(
                        provider=f"openai:{settings.openai_model}",
                        summary="openai summary",
                        risk_level="low",
                        analysis_type="trend_following",
                        readiness="paper",
                        score=88,
                        confidence=0.91,
                        strengths=["openai strength"],
                        warnings=["openai warning"],
                        recommendations=["openai recommendation"],
                        fit_profile=["openai fit"],
                        avoid_profile=["openai avoid"],
                        execution_plan=["openai plan"],
                        suggested_params={"short_window": 5, "long_window": 20},
                    )
                    openai = ai_analysis_service.analyze_backtest(backtest.backtest_id, db, "dev-user", mode="openai")
                    self.assertIsNotNone(openai)
                    assert openai is not None
                    self.assertTrue(openai.provider.startswith("openai:"))
                    self.assertEqual(openai.summary, "openai summary")

                    def raise_quota_error(record, settings):
                        request = httpx.Request("POST", "https://api.openai.com/v1/responses")
                        response = httpx.Response(
                            429,
                            request=request,
                            json={"error": {"type": "insufficient_quota", "code": "insufficient_quota"}},
                        )
                        raise httpx.HTTPStatusError("quota exceeded", request=request, response=response)

                    ai_analysis_service._build_openai_analysis = raise_quota_error
                    fallback = ai_analysis_service.analyze_backtest(
                        backtest.backtest_id, db, "dev-user", mode="openai"
                    )
                    self.assertIsNotNone(fallback)
                    assert fallback is not None
                    self.assertEqual(fallback.provider, "local-quant-recommender-v2")
                    self.assertIn("额度不足", fallback.recommendations[0])
                finally:
                    ai_analysis_service._build_openai_analysis = original
                    ai_analysis_service._build_gemini_analysis = original_gemini
                    if previous_openai_key is None:
                        os.environ.pop("QUANT_PLATFORM_OPENAI_API_KEY", None)
                    else:
                        os.environ["QUANT_PLATFORM_OPENAI_API_KEY"] = previous_openai_key
                    if previous_gemini_key is None:
                        os.environ.pop("QUANT_PLATFORM_GEMINI_API_KEY", None)
                    else:
                        os.environ["QUANT_PLATFORM_GEMINI_API_KEY"] = previous_gemini_key

    def test_analysis_is_persisted_and_user_scoped(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            clear_app_modules()
            os.environ["QUANT_PLATFORM_DATABASE_URL"] = (
                f"sqlite:///{Path(tmp_dir) / 'test.db'}"
            )

            from app.core.database import SessionLocal, init_db
            from app.schemas.backtest import BacktestRequest
            from app.services.ai_analysis_service import analyze_backtest, list_backtest_analyses
            from app.services.backtest_service import run_backtest
            from app.services.strategy_service import seed_builtin_strategies
            from app.services.user_service import ensure_system_user

            init_db()
            with SessionLocal() as db:
                ensure_system_user(db)
                seed_builtin_strategies(db)
                backtest = run_backtest(
                    BacktestRequest(
                        symbol="BTCUSDT",
                        timeframe="1d",
                        strategy_id="ma-cross-default",
                        start_date="2024-01-01",
                        end_date="2024-12-31",
                        initial_cash=10000,
                        params={"short_window": 7, "long_window": 30},
                    ),
                    db,
                    user_id="dev-user",
                )

                analysis = analyze_backtest(backtest.backtest_id, db, "dev-user")
                self.assertIsNotNone(analysis)
                assert analysis is not None
                self.assertEqual(analysis.provider, "local-quant-recommender-v2")
                self.assertIn(analysis.risk_level, {"low", "medium", "high"})
                self.assertIn(analysis.analysis_type, {"trend_following", "mean_reversion", "hybrid_candidate"})
                self.assertIn(analysis.readiness, {"research", "paper", "limited_live"})
                self.assertGreaterEqual(analysis.score, 0)
                self.assertLessEqual(analysis.score, 100)
                self.assertGreaterEqual(analysis.confidence, 0)
                self.assertLessEqual(analysis.confidence, 1)
                self.assertTrue(analysis.strengths)
                self.assertIn("short_window", analysis.suggested_params)
                self.assertTrue(analysis.fit_profile)
                self.assertTrue(analysis.execution_plan)

                history = list_backtest_analyses(backtest.backtest_id, db, "dev-user")
                self.assertEqual(len(history or []), 1)
                self.assertIsNone(analyze_backtest(backtest.backtest_id, db, "other-user"))
                self.assertIsNone(list_backtest_analyses(backtest.backtest_id, db, "other-user"))


if __name__ == "__main__":
    unittest.main()
