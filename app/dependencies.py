from fastapi import Header, HTTPException
import jwt
from app.config import settings


async def get_current_user(
    authorization: str | None = Header(None),
    x_user_id: str | None = Header(None),
    x_user_email: str | None = Header(None),
) -> dict:
    """
    Validate JWT Bearer token from Authorization header.
    Falls back to X-User-* gateway-injected headers.
    """
    if authorization and authorization.startswith("Bearer "):
        token = authorization.split(" ", 1)[1]
        try:
            payload = jwt.decode(
                token,
                settings.jwt_secret,
                algorithms=[settings.jwt_algorithm]
            )
            return {
                "user_id": payload.get("sub"),
                "email": payload.get("email"),
                "employee_id": payload.get("employee_id"),
            }
        except jwt.ExpiredSignatureError:
            raise HTTPException(status_code=401, detail="Token expired — please login again")
        except jwt.InvalidTokenError:
            raise HTTPException(status_code=401, detail="Invalid authentication token")

    # Fallback: header injection (future gateway OIDC proxy)
    if x_user_id:
        return {"user_id": x_user_id, "email": x_user_email, "employee_id": None}

    raise HTTPException(status_code=401, detail="Authentication required")
