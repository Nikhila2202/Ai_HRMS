
import jwt

from fastapi import Depends, HTTPException, status

from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from sqlalchemy.orm import Session, selectinload

from database import get_db

from app.models.model import (
    User,
    UserRole,
    Role,
    RolePermission
)

from app.auth.security import decode_access_token


bearer_scheme = HTTPBearer(
    auto_error=False
)


# JWT TOKEN VERIFICATION

def verify_token(

    credentials: HTTPAuthorizationCredentials = Depends(
        bearer_scheme
    )

):

    # 1. Check token exists

    if credentials is None:

        raise HTTPException(
            status_code=401,
            detail="Authentication token required",
            headers={"WWW-Authenticate": "Bearer"}
        )


    # 2. Check Bearer scheme

    if credentials.scheme.lower() != "bearer":

        raise HTTPException(
            status_code=401,
            detail="Invalid authentication scheme"
        )


    try:

        # 3. Decode and verify JWT

        payload = decode_access_token(
            credentials.credentials
        )


        # 4. Extract user ID

        user_id = payload.get("sub")


        if user_id is None:

            raise HTTPException(
                status_code=401,
                detail="Invalid token payload"
            )


        return int(user_id)


    except (
        jwt.InvalidTokenError,
        TypeError,
        ValueError
    ):

        raise HTTPException(
            status_code=401,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"}
        )


# CURRENT USER RETRIEVAL

def get_current_user(

    user_id: int = Depends(verify_token),

    db: Session = Depends(get_db)

):

    # 1. Retrieve user from database

    current_user = (

        db.query(User)

        .options(

            selectinload(User.roles)

            .selectinload(UserRole.role)

            .selectinload(Role.permissions)

            .selectinload(RolePermission.permission)

        )

        .filter(
            User.user_id == user_id
        )

        .first()

    )


    # 2. Check user exists

    if current_user is None:

        raise HTTPException(
            status_code=401,
            detail="User not found"
        )


    # 3. Check account active

    if not current_user.is_active:

        raise HTTPException(
            status_code=403,
            detail="User account is inactive"
        )


    return current_user
