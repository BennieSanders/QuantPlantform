from fastapi import APIRouter, HTTPException, status
from fastapi.params import Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user_id
from app.schemas.strategy import StrategyCreate, StrategyResponse, StrategyUpdate
from app.services.strategy_service import (
    create_strategy,
    delete_strategy,
    get_strategy,
    list_strategies,
    update_strategy,
)


router = APIRouter(prefix="/api/strategies", tags=["strategies"])


@router.get("", response_model=list[StrategyResponse])
def list_strategy_items(
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
) -> list[StrategyResponse]:
    return list_strategies(db, user_id=user_id)


@router.post("", response_model=StrategyResponse, status_code=status.HTTP_201_CREATED)
def create_strategy_item(
    payload: StrategyCreate,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
) -> StrategyResponse:
    try:
        return create_strategy(db, payload, user_id=user_id)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error


@router.get("/{strategy_id}", response_model=StrategyResponse)
def get_strategy_item(
    strategy_id: str,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
) -> StrategyResponse:
    strategy = get_strategy(db, strategy_id, user_id=user_id)
    if strategy is None:
        raise HTTPException(status_code=404, detail="Strategy not found")
    return strategy


@router.put("/{strategy_id}", response_model=StrategyResponse)
def update_strategy_item(
    strategy_id: str,
    payload: StrategyUpdate,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
) -> StrategyResponse:
    try:
        strategy = update_strategy(db, strategy_id, payload, user_id=user_id)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    if strategy is None:
        raise HTTPException(status_code=404, detail="Strategy not found")
    return strategy


@router.delete("/{strategy_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_strategy_item(
    strategy_id: str,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
) -> None:
    try:
        deleted = delete_strategy(db, strategy_id, user_id=user_id)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error

    if not deleted:
        raise HTTPException(status_code=404, detail="Strategy not found")
