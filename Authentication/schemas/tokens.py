from datetime import datetime, timedelta

from pydantic import BaseModel, EmailStr

from config.config import get_settings

settings = get_settings()


class Token(BaseModel):
    id: str
    email: EmailStr
    iat: datetime = datetime.utcnow()
    jti: str


class AccessTokens(Token):
    exp: datetime = datetime.utcnow() + timedelta(seconds=settings.ACCESS_TOKEN_TTL)
    token_type: str = "access token"


class RefreshTokens(Token):
    exp: datetime = datetime.utcnow() + timedelta(seconds=settings.REFRESH_TOKEN_TTL)
    token_type: str = "refresh token"

