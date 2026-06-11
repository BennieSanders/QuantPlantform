from typing import Literal

from pydantic import BaseModel, Field


StrategyType = Literal["builtin", "custom_code"]
StrategyStatus = Literal["draft", "active", "archived"]


class StrategyBase(BaseModel):
    name: str = Field(min_length=1, max_length=80)
    description: str = ""
    strategy_type: StrategyType = "custom_code"
    code: str = ""
    default_params: dict[str, int | float | str] = Field(default_factory=dict)
    status: StrategyStatus = "draft"


class StrategyCreate(StrategyBase):
    pass


class StrategyUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=80)
    description: str | None = None
    strategy_type: StrategyType | None = None
    code: str | None = None
    default_params: dict[str, int | float | str] | None = None
    status: StrategyStatus | None = None


class StrategyResponse(StrategyBase):
    id: str
    user_id: str
    created_at: str
    updated_at: str
