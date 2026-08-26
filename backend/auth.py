import jwt
import datetime
import hashlib
import os
from fastapi import HTTPException, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

SECRET_KEY = os.environ.get("JWT_SECRET", "superduper_secret_key_123456_bizfiz")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 # 24 hours

security = HTTPBearer(auto_error=False)

def hash_password(password: str) -> str:
    """Hash password using SHA-256 with a secure salt."""
    salt = b"bizfiz_salt_key_987654"
    key = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 100000)
    return key.hex()

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password by comparing hashed outputs."""
    return hash_password(plain_password) == hashed_password

def create_access_token(data: dict) -> str:
    """Generate JWT access token with role and user identifiers."""
    to_encode = data.copy()
    expire = datetime.datetime.utcnow() + datetime.timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def decode_access_token(token: str) -> dict:
    """Decode JWT token, validate expiration and signature."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired. Please login again.")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid authorization token.")

def get_current_user(credentials: HTTPAuthorizationCredentials = Security(security)) -> dict:
    """FastAPI dependency to extract current authenticated user."""
    if not credentials:
        raise HTTPException(status_code=401, detail="Authentication credentials required.")
    token = credentials.credentials
    payload = decode_access_token(token)
    return payload

def get_admin_user(credentials: HTTPAuthorizationCredentials = Security(security)) -> dict:
    """FastAPI dependency enforcing Bank Admin authorization."""
    payload = get_current_user(credentials)
    if payload.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Forbidden: Bank Admin access required.")
    return payload

def get_client_user(credentials: HTTPAuthorizationCredentials = Security(security)) -> dict:
    """FastAPI dependency enforcing Client / Borrower authorization."""
    payload = get_current_user(credentials)
    if payload.get("role") != "client":
        raise HTTPException(status_code=403, detail="Forbidden: Client access required.")
    return payload
