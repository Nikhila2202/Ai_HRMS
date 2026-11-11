
import os
import jwt

from pathlib import Path
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv

from argon2 import PasswordHasher
from argon2.exceptions import (
    VerifyMismatchError,
    VerificationError,
    InvalidHashError
)


# --------------------------------------------------
# LOAD ENVIRONMENT VARIABLES
# --------------------------------------------------

# Project structure:
# AI_HRMS/
#   .env
#   app/
#     auth/
#       security.py

PROJECT_ROOT = Path(__file__).resolve().parents[2]

ENV_FILE = PROJECT_ROOT / ".env"

load_dotenv(dotenv_path=ENV_FILE)


# --------------------------------------------------
# PASSWORD HASHING CONFIGURATION
# --------------------------------------------------

password_hasher = PasswordHasher()


def hash_password(password: str) -> str:
    """
    Hash a plain-text password using Argon2.
    """

    return password_hasher.hash(password)


def verify_password(
    plain_password: str,
    hashed_password: str
) -> bool:
    """
    Verify a plain-text password against
    its Argon2 hash.
    """

    try:
        return password_hasher.verify(
            hashed_password,
            plain_password
        )

    except (
        VerifyMismatchError,
        VerificationError,
        InvalidHashError
    ):
        return False


# --------------------------------------------------
# JWT CONFIGURATION
# --------------------------------------------------

SECRET_KEY = os.getenv("SECRET_KEY")

ALGORITHM = os.getenv(
    "ALGORITHM",
    "HS256"
)

ACCESS_TOKEN_EXPIRE_MINUTES = int(
    os.getenv(
        "ACCESS_TOKEN_EXPIRE_MINUTES",
        "30"
    )
)

if not SECRET_KEY:
    raise RuntimeError(
        "SECRET_KEY is missing from .env file"
    )


# --------------------------------------------------
# CREATE JWT ACCESS TOKEN
# --------------------------------------------------

def create_access_token(user_id: int) -> str:
    """
    Generate JWT access token for authenticated user.
    """

    now = datetime.now(timezone.utc)

    expire = now + timedelta(
        minutes=ACCESS_TOKEN_EXPIRE_MINUTES
    )

    payload = {
        "sub": str(user_id),
        "iat": now,
        "exp": expire,
        "type": "access"
    }

    token = jwt.encode(
        payload,
        SECRET_KEY,
        algorithm=ALGORITHM
    )

    return token


# --------------------------------------------------
# DECODE AND VERIFY JWT ACCESS TOKEN
# --------------------------------------------------

def decode_access_token(token: str) -> dict:
    """
    Decode JWT and validate its signature,
    expiration and required claims.
    """

    payload = jwt.decode(
        token,
        SECRET_KEY,
        algorithms=[ALGORITHM],
        options={
            "require": [
                "sub",
                "iat",
                "exp",
                "type"
            ]
        }
    )

    # Validate token type

    if payload.get("type") != "access":
        raise jwt.InvalidTokenError(
            "Invalid token type"
        )

    return payload


