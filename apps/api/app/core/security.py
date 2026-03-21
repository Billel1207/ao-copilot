"""JWT authentication & password hashing — RS256 (prod) / HS256 (dev) dual mode."""
import hashlib
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto", bcrypt__rounds=12)


def _truncate_for_bcrypt(password: str) -> str:
    """bcrypt limite à 72 bytes — tronquer proprement."""
    return password.encode("utf-8")[:72].decode("utf-8", errors="ignore")


def hash_password(password: str) -> str:
    return pwd_context.hash(_truncate_for_bcrypt(password))


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(_truncate_for_bcrypt(plain), hashed)


def _is_asymmetric() -> bool:
    """Détecte si on utilise RS256 (clés asymétriques) ou HS256 (secret partagé)."""
    return settings.JWT_ALGORITHM == "RS256" and settings.JWT_PRIVATE_KEY


def _signing_key() -> str:
    """Clé pour signer les tokens (private key RS256 ou SECRET_KEY HS256)."""
    if _is_asymmetric():
        return settings.JWT_PRIVATE_KEY
    return settings.SECRET_KEY


def _verification_key() -> str:
    """Clé pour vérifier les tokens (public key RS256 ou SECRET_KEY HS256)."""
    if _is_asymmetric():
        return settings.JWT_PUBLIC_KEY
    return settings.SECRET_KEY


def create_access_token(data: dict[str, Any]) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {**data, "exp": expire, "type": "access"}
    return jwt.encode(payload, _signing_key(), algorithm=settings.JWT_ALGORITHM)


def create_refresh_token(data: dict[str, Any]) -> str:
    expire = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    payload = {**data, "exp": expire, "type": "refresh", "jti": str(uuid.uuid4())}
    return jwt.encode(payload, _signing_key(), algorithm=settings.JWT_ALGORITHM)


def create_email_verify_token(user_id: str, email: str) -> str:
    """Create a JWT for email verification (24h expiry)."""
    expire = datetime.now(timezone.utc) + timedelta(hours=24)
    payload = {"sub": user_id, "email": email, "exp": expire, "type": "email_verify"}
    return jwt.encode(payload, _signing_key(), algorithm=settings.JWT_ALGORITHM)


def decode_token(token: str) -> dict[str, Any]:
    return jwt.decode(token, _verification_key(), algorithms=[settings.JWT_ALGORITHM])


def hash_ip(ip: str) -> str:
    """Hash IP pour logs RGPD — non réversible."""
    salt = settings.SECRET_KEY[:16]
    return hashlib.sha256(f"{salt}{ip}".encode()).hexdigest()
