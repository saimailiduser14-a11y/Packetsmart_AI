import os
import secrets
import hashlib
import hmac
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
from fastapi import Request, HTTPException, status, Depends
from dotenv import load_dotenv

load_dotenv()

# JWT Configuration
SECRET_KEY = os.getenv("SECRET_KEY", "pocketsmart_ai_super_secret_jwt_key_2026_change_in_production_32bytes_min")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "1440"))

# Try importing jwt (PyJWT) or fallback to python-jose
try:
    import jwt
    HAS_PYJWT = True
except ImportError:
    from jose import jwt
    HAS_PYJWT = False

from database import get_user_by_username, get_user_by_id

def hash_password(password: str) -> str:
    """Hash a password using PBKDF2-HMAC-SHA256 with a unique cryptographic salt."""
    salt = secrets.token_hex(16)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), 100000)
    return f"{salt}${dk.hex()}"

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against the stored salt$hash string."""
    try:
        if "$" in hashed_password:
            salt, dk_hex = hashed_password.split("$", 1)
            test_dk = hashlib.pbkdf2_hmac("sha256", plain_password.encode("utf-8"), salt.encode("utf-8"), 100000)
            return hmac.compare_digest(test_dk.hex(), dk_hex)
        return False
    except Exception:
        return False

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Generate a signed JWT token with an expiration timestamp."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    if isinstance(encoded_jwt, bytes):
        encoded_jwt = encoded_jwt.decode("utf-8")
    return encoded_jwt

def decode_access_token(token: str) -> Optional[dict]:
    """Decode and validate a JWT access token."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except Exception:
        return None

def extract_token_from_request(request: Request) -> Optional[str]:
    """Extract token from HTTP-only cookie or Authorization header."""
    # 1. Check HTTP-only cookie
    token = request.cookies.get("access_token")
    if token:
        if token.startswith("Bearer "):
            token = token[7:]
        return token

    # 2. Check Authorization Header
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        return auth_header[7:].strip()

    return None

def get_current_user_optional(request: Request) -> Optional[Dict[str, Any]]:
    """Retrieve current authenticated user if token exists, or None for guest."""
    token = extract_token_from_request(request)
    if not token:
        return None
    
    payload = decode_access_token(token)
    if not payload:
        return None
    
    username = payload.get("sub")
    if not username:
        return None
        
    user = get_user_by_username(username)
    return user

def get_current_user(request: Request) -> Dict[str, Any]:
    """Dependency that enforces authentication, raising 401 if missing/invalid."""
    user = get_current_user_optional(request)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication credentials were not provided or have expired.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user
