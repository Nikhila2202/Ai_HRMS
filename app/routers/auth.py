from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from app.models.model import User
from app.schemas.auth_schema import LoginRequest, RefreshTokenRequest
from app.auth.security import (
    decode_refresh_token,
    verify_password,
    create_access_token,
    create_refresh_token
)

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
    refresh_token = create_refresh_token(user_id=user.user_id)

    return {
    "access_token": access_token,
    "refresh_token": refresh_token,
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

#refesh token endpoint

    # Your refresh token logic
    pass

@router.post("/refresh")
def refresh_access_token(
    data: RefreshTokenRequest,
    db: Session = Depends(get_db)
):
    # 1. Validate the refresh token
    payload = decode_refresh_token(data.refresh_token)

    if payload is None:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired refresh token"
        )

    # 2. Get the user ID from the token
    try:
        user_id = int(payload["sub"])
    except (KeyError, TypeError, ValueError):
        raise HTTPException(
            status_code=401,
            detail="Invalid refresh token"
        )

    # 3. Find the user in the database
    user = db.query(User).filter(
        User.user_id == user_id
    ).first()

    if user is None:
        raise HTTPException(
            status_code=401,
            detail="User account not found"
        )

    # 4. Check whether the account is active
    if not user.is_active:
        raise HTTPException(
            status_code=403,
            detail="User account is inactive"
        )

    # 5. Generate a new access token
    new_access_token = create_access_token(
        user_id=user.user_id
    )

    # 6. Return the new access token
    return {
        "message": "Access token refreshed successfully",
        "access_token": new_access_token,
        "token_type": "bearer"
    }
