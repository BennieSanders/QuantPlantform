from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.strategy import Strategy
from app.schemas.strategy import StrategyCreate, StrategyResponse, StrategyUpdate
from quant_engine.strategies.script import compile_signal_function


DEFAULT_MA_CROSS_CODE = """def generate_signals(klines, params):
    short_window = params.get("short_window", 7)
    long_window = params.get("long_window", 30)
    # Built-in ma_cross currently runs through quant_engine.strategies.ma_cross.
    # Custom strategy execution will be connected in a later milestone.
    return []
"""

DEFAULT_RSI_CODE = """def generate_signals(klines, params):
    period = params.get("period", 14)
    oversold = params.get("oversold", 30)
    overbought = params.get("overbought", 70)
    # Built-in rsi_reversal currently runs through quant_engine.strategies.rsi.
    # Custom strategy execution will be connected in a later milestone.
    return []
"""


BUILTIN_STRATEGIES = [
    {
        "id": "ma-cross-default",
        "name": "均线交叉策略",
        "description": "短均线上穿长均线买入，短均线下穿长均线卖出。",
        "code": DEFAULT_MA_CROSS_CODE,
        "default_params": {"short_window": 7, "long_window": 30},
    },
    {
        "id": "rsi-reversal-default",
        "name": "RSI 反转策略",
        "description": "RSI 跌至超卖阈值买入，升至超买阈值卖出。",
        "code": DEFAULT_RSI_CODE,
        "default_params": {"period": 14, "oversold": 30, "overbought": 70},
    },
]


def seed_builtin_strategies(db: Session) -> None:
    settings = get_settings()
    now = _now()
    changed = False
    for item in BUILTIN_STRATEGIES:
        strategy = db.get(Strategy, item["id"])
        if strategy is None:
            db.add(
                Strategy(
                    id=item["id"],
                    user_id=settings.system_user_id,
                    name=item["name"],
                    description=item["description"],
                    strategy_type="builtin",
                    code=item["code"],
                    default_params=item["default_params"],
                    status="active",
                    created_at=now,
                    updated_at=now,
                )
            )
            changed = True

    if changed:
        db.commit()


def list_strategies(db: Session, user_id: str) -> list[StrategyResponse]:
    strategies = db.scalars(
        select(Strategy)
        .where((Strategy.strategy_type == "builtin") | (Strategy.user_id == user_id))
        .order_by(Strategy.created_at)
    ).all()
    return [_to_response(strategy) for strategy in strategies]


def get_strategy(db: Session, strategy_id: str, user_id: str) -> StrategyResponse | None:
    strategy = db.get(Strategy, strategy_id)
    if strategy is None:
        return None
    if strategy.strategy_type != "builtin" and strategy.user_id != user_id:
        return None
    return _to_response(strategy)


def create_strategy(
    db: Session,
    payload: StrategyCreate,
    user_id: str | None = None,
) -> StrategyResponse:
    _validate_custom_strategy(payload.strategy_type, payload.code)
    owner_id = user_id or get_settings().system_user_id
    now = _now()
    strategy = Strategy(
        id=f"st-{uuid4().hex[:8]}",
        user_id=owner_id,
        created_at=now,
        updated_at=now,
        **payload.model_dump(),
    )
    db.add(strategy)
    db.commit()
    db.refresh(strategy)
    return _to_response(strategy)


def update_strategy(
    db: Session,
    strategy_id: str,
    payload: StrategyUpdate,
    user_id: str | None = None,
) -> StrategyResponse | None:
    strategy = db.get(Strategy, strategy_id)
    if strategy is None:
        return None
    owner_id = user_id or get_settings().system_user_id
    if strategy.strategy_type != "builtin" and strategy.user_id != owner_id:
        return None

    update_data = payload.model_dump(exclude_unset=True)
    if strategy.strategy_type == "builtin":
        update_data.pop("strategy_type", None)
    next_strategy_type = update_data.get("strategy_type", strategy.strategy_type)
    next_code = update_data.get("code", strategy.code)
    _validate_custom_strategy(next_strategy_type, next_code)

    for key, value in update_data.items():
        setattr(strategy, key, value)
    strategy.updated_at = _now()

    db.commit()
    db.refresh(strategy)
    return _to_response(strategy)


def delete_strategy(db: Session, strategy_id: str, user_id: str | None = None) -> bool:
    strategy = db.get(Strategy, strategy_id)
    if strategy is None:
        return False
    owner_id = user_id or get_settings().system_user_id
    if strategy.strategy_type != "builtin" and strategy.user_id != owner_id:
        return False
    if strategy.strategy_type == "builtin":
        raise ValueError("Built-in strategies cannot be deleted")

    db.delete(strategy)
    db.commit()
    return True


def _to_response(strategy: Strategy) -> StrategyResponse:
    return StrategyResponse(
        id=strategy.id,
        user_id=strategy.user_id,
        name=strategy.name,
        description=strategy.description,
        strategy_type=strategy.strategy_type,
        code=strategy.code,
        default_params=strategy.default_params,
        status=strategy.status,
        created_at=strategy.created_at.isoformat(),
        updated_at=strategy.updated_at.isoformat(),
    )


def _now() -> datetime:
    return datetime.now(UTC)


def _validate_custom_strategy(strategy_type: str, code: str) -> None:
    if strategy_type != "custom_code":
        return
    try:
        compile_signal_function(code)
    except Exception as error:
        raise ValueError(f"Invalid custom strategy code: {error}") from error
