from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from app.models.model import User
from app.schemas.auth_schema import LoginRequest
from app.auth.security import verify_password, create_access_token

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"]
)


@router.post("/login")
def login(
    data: LoginRequest,
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(
        User.email == data.email
    ).first()

    if not user:
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password"
        )

    if not user.is_active:
        raise HTTPException(
            status_code=403,
            detail="Account is inactive"
        )

    if not verify_password(data.password, user.password_hash):
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password"
        )

    access_token = create_access_token(
    user_id=user.user_id
)

    return {
    "access_token": access_token,
    "token_type": "bearer"
}

from app.auth.security import (
    create_access_token,
    decode_access_token
)

@router.get("/test-token")
def test_token():

    token = create_access_token(user_id=1)

    try:
        payload = decode_access_token(token)

        return {
            "message": "JWT generation and decoding successful",
            "payload": payload
        }

    except Exception as e:
        return {
            "message": "JWT verification failed",
            "error": str(e)
        }
