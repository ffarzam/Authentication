from typing import Tuple
from uuid import uuid4

from fastapi import Request
import jwt
from redis import Redis

from config.config import get_settings

from schemas.tokens import AccessTokens, RefreshTokens

settings = get_settings()


def create_token(token: RefreshTokens | AccessTokens) -> str:
    payload = token.model_dump()
    token = jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    return token


async def decode_token(token: str) -> dict:
    payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
    return payload


async def set_token(request: Request, user_info: dict) -> Tuple[str, ...]:
    user_id = user_info["id"]
    jti = uuid4().hex
    access_token_obj = AccessTokens(**user_info, jti=jti)
    refresh_token_obj = RefreshTokens(**user_info, jti=jti)
    access_token = create_token(access_token_obj)
    refresh_token = create_token(refresh_token_obj)

    key = cache_key_setter(user_id, jti)
    value = cache_value_setter(request)

    return access_token, refresh_token, key, value


def cache_key_parser(arg):
    return arg.split(" || ")


def cache_key_setter(user_id, jti) -> str:
    return f"user_{user_id} || {jti}"


def cache_value_setter(request) -> str:
    return request.headers.get('User-Agent', 'UNKNOWN')
