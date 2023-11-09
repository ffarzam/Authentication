from fastapi import APIRouter, Depends, status, Request, Response

from config.config import settings
from services.accounts_microservice import Client, get_account_client
from config.jwt_authentication import get_refresh_jwt_aut
from db.redisdb import get_redis
from schemas.user import UserSignUp, UserSignIn
from services.notification_microservice import get_notification_client
from utils.token_utils import set_token

routers = APIRouter(prefix="/v1")


@routers.post("/register")
async def register_user(request: Request, user: UserSignUp, response: Response,
                        account_client: Client = Depends(get_account_client),
                        notification_client=Depends(get_notification_client)):

    user = user.model_dump()
    account_microservice_response = await account_client.register_call(user, request)
    response.status_code = account_microservice_response.status_code
    if response.status_code == 201:
        notification_microservice_response = await notification_client.code_call(
            {"email": user["email"], "action": "verify account"}, request)
        return {"message": "A code was sent to your email", "data": account_microservice_response.json()}
    return account_microservice_response.json()


@routers.post("/login", status_code=status.HTTP_200_OK)
async def login(request: Request, user: UserSignIn, response: Response,
                httpx_client: Client = Depends(get_account_client), redis=Depends(get_redis),
                notification_client=Depends(get_notification_client)):

    user = user.model_dump()

    account_microservice_response = await httpx_client.login_call(user, request)

    if account_microservice_response.status_code == 200:
        access_token, refresh_token, key, value = await set_token(request, account_microservice_response.json())
        await redis.set(key, value, ex=settings.REFRESH_TOKEN_TTL)
        return {"access": access_token, "refresh": refresh_token}
    if account_microservice_response.status_code == 455:
        await notification_client.code_call({"email": user["email"], "action": "verify account"}, request)

    response.status_code = account_microservice_response.status_code
    return account_microservice_response.json()


@routers.post("/refresh")
async def refresh(request: Request, payload: dict = Depends(get_refresh_jwt_aut()), redis=Depends(get_redis)):

    user_id = payload["id"]
    user_email = payload["email"]
    jti = payload["jti"]
    await redis.delete(f'user_{user_id} || {jti}')

    access_token, refresh_token, key, value = await set_token(request, {"id": user_id, "email": user_email})
    await redis.set(key, value, ex=settings.REFRESH_TOKEN_TTL)

    return {"access": access_token, "refresh": refresh_token}


@routers.post("/logout", status_code=status.HTTP_200_OK)
async def logout(payload: dict = Depends(get_refresh_jwt_aut()), redis=Depends(get_redis)):

    await redis.delete(f'user_{payload["id"]} || {payload["jti"]}')
    return {"Logged out successfully"}


@routers.post("/logout_all", status_code=status.HTTP_200_OK)
async def logout_all(payload: dict = Depends(get_refresh_jwt_aut()), redis=Depends(get_redis)):

    await redis.delete(*(await redis.keys(f'user_{payload["id"]} || *')))
    return {"Logged out successfully"}
