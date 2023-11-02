import json
from typing import Any
import jwt

from fastapi import Request, HTTPException, status, Body
from fastapi.security import HTTPBearer

from db.redisdb import get_redis
from utils.token_utils import decode_token

redis = get_redis()


class RefreshJWTAuth(HTTPBearer):
    def __init__(self, auto_error: bool = True):
        super(RefreshJWTAuth, self).__init__(auto_error=auto_error)

    async def __call__(self, request: Request):
        data = await request.json()
        refresh_token = data["refresh_token"]

        if not refresh_token:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No refresh token was found.")
        try:
            payload = await decode_token(refresh_token)
        except jwt.ExpiredSignatureError:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Expired refresh token")
        except Exception:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invalid refresh token.")
        result = await self.validate_jti_token(payload)
        if not result:
            HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid refresh token.")

        return payload

    @staticmethod
    async def validate_jti_token(payload: dict) -> Any:
        jti = payload.get('jti')
        user_id = payload.get('user_id')
        return await redis.keys(f"user_{user_id} || {jti}")


refresh_jwt_auth = RefreshJWTAuth()


def get_refresh_jwt_aut():
    return refresh_jwt_auth
