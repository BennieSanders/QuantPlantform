from fastapi import APIRouter
from fastapi.params import Depends

from app.core.security import get_current_user
from app.models.user import User
from app.schemas.auth import UserResponse
from app.services.user_service import to_user_response


router = APIRouter(prefix="/api/users", tags=["users"])


@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)) -> UserResponse:
    return to_user_response(current_user)
