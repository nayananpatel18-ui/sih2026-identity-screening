"""Firebase Admin authentication boundary for protected API operations."""

from dataclasses import dataclass
from fastapi import Header, HTTPException, status
from app.services.firebase_service import verify_id_token


@dataclass(frozen=True)
class AuthenticatedPrincipal:
    uid: str
    email: str | None = None


async def require_authenticated_principal(authorization: str | None = Header(default=None)) -> AuthenticatedPrincipal:
    if not authorization:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing Bearer token.")
    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token.strip():
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authorization must be a Bearer token.")
    try:
        claims = verify_id_token(token.strip())
    except RuntimeError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid Firebase ID token.") from exc
    uid = claims.get("uid") or claims.get("sub")
    if not isinstance(uid, str) or not uid:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Firebase token has no UID.")
    return AuthenticatedPrincipal(uid=uid, email=claims.get("email"))
