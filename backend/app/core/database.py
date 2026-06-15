from collections.abc import Generator

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import get_settings

settings = get_settings()

engine = create_engine(
    settings.database_url,
    connect_args={"check_same_thread": False} if settings.is_sqlite else {},
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    import app.models.ai_analysis  # noqa: F401
    import app.models.backtest_job  # noqa: F401
    import app.models.backtest_record  # noqa: F401
    import app.models.market_kline  # noqa: F401
    import app.models.strategy  # noqa: F401
    import app.models.user  # noqa: F401

    Base.metadata.create_all(bind=engine)
    _upgrade_sqlite_development_schema()


def _upgrade_sqlite_development_schema() -> None:
    if not settings.is_sqlite:
        return

    inspector = inspect(engine)
    table_names = set(inspector.get_table_names())
    owner_default = settings.system_user_id.replace("'", "''")

    with engine.begin() as connection:
        if "strategies" in table_names:
            columns = {column["name"] for column in inspector.get_columns("strategies")}
            if "user_id" not in columns:
                connection.execute(
                    text(
                        "ALTER TABLE strategies "
                        f"ADD COLUMN user_id VARCHAR(64) NOT NULL DEFAULT '{owner_default}'"
                    )
                )
                connection.execute(
                    text("CREATE INDEX IF NOT EXISTS ix_strategies_user_id ON strategies (user_id)")
                )

        if "backtest_records" in table_names:
            columns = {column["name"] for column in inspector.get_columns("backtest_records")}
            if "user_id" not in columns:
                connection.execute(
                    text(
                        "ALTER TABLE backtest_records "
                        f"ADD COLUMN user_id VARCHAR(64) NOT NULL DEFAULT '{owner_default}'"
                    )
                )
                connection.execute(
                    text(
                        "CREATE INDEX IF NOT EXISTS "
                        "ix_backtest_records_user_id ON backtest_records (user_id)"
                    )
                )

        if "backtest_jobs" in table_names:
            columns = {column["name"] for column in inspector.get_columns("backtest_jobs")}
            if "retry_of_job_id" not in columns:
                connection.execute(
                    text("ALTER TABLE backtest_jobs ADD COLUMN retry_of_job_id VARCHAR(64)")
                )
                connection.execute(
                    text(
                        "CREATE INDEX IF NOT EXISTS "
                        "ix_backtest_jobs_retry_of_job_id ON backtest_jobs (retry_of_job_id)"
                    )
                )
            if "attempt" not in columns:
                connection.execute(
                    text("ALTER TABLE backtest_jobs ADD COLUMN attempt INTEGER NOT NULL DEFAULT 1")
                )
            if "cancel_requested" not in columns:
                connection.execute(
                    text(
                        "ALTER TABLE backtest_jobs "
                        "ADD COLUMN cancel_requested BOOLEAN NOT NULL DEFAULT 0"
                    )
                )
            if "error_message" not in columns:
                connection.execute(
                    text(
                        "ALTER TABLE backtest_jobs "
                        "ADD COLUMN error_message VARCHAR(1000) NOT NULL DEFAULT ''"
                    )
                )

        if "ai_analyses" in table_names:
            columns = {column["name"] for column in inspector.get_columns("ai_analyses")}
            if "analysis_type" not in columns:
                connection.execute(
                    text("ALTER TABLE ai_analyses ADD COLUMN analysis_type VARCHAR(32) NOT NULL DEFAULT ''")
                )
            if "readiness" not in columns:
                connection.execute(
                    text("ALTER TABLE ai_analyses ADD COLUMN readiness VARCHAR(32) NOT NULL DEFAULT ''")
                )
            if "score" not in columns:
                connection.execute(
                    text("ALTER TABLE ai_analyses ADD COLUMN score FLOAT NOT NULL DEFAULT 0")
                )
            if "confidence" not in columns:
                connection.execute(
                    text("ALTER TABLE ai_analyses ADD COLUMN confidence FLOAT NOT NULL DEFAULT 0")
                )
            if "fit_profile" not in columns:
                connection.execute(
                    text("ALTER TABLE ai_analyses ADD COLUMN fit_profile JSON NOT NULL DEFAULT '[]'")
                )
            if "avoid_profile" not in columns:
                connection.execute(
                    text("ALTER TABLE ai_analyses ADD COLUMN avoid_profile JSON NOT NULL DEFAULT '[]'")
                )
            if "execution_plan" not in columns:
                connection.execute(
                    text("ALTER TABLE ai_analyses ADD COLUMN execution_plan JSON NOT NULL DEFAULT '[]'")
                )
