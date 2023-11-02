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
async def register_user(user: UserSignUp, response: Response, account_client: Client = Depends(get_account_client),
                        notification_client=Depends(get_notification_client)):

    """
    The register_user function is used to register a new user.
        It takes in the following parameters:
            - user: A UserSignUp object containing the information of the new user.
            - response: The response object that will be returned by this function. This is passed as an argument so that
                we can set its status code to whatever value we want, depending on what happens during execution of this
                function (e.g., if there was an error, then we would set it to 400).

    :param user: UserSignUp: Get the data from the request body
    :param response: Response: Set the status code of the response
    :param account_client: Client: Make a call to the account microservice
    :param notification_client: Call the notification microservice
    :return: A dictionary with the message and data keys
    """
    user = user.model_dump()
    account_microservice_response = await account_client.register_call(user)

    response.status_code = account_microservice_response.status_code

    if response.status_code == 201:

        notification_microservice_response = await notification_client.code_call(
            {"email": user["email"], "action": "verify account"})

        return {"message": "A code was sent to your email", "data": account_microservice_response.json()}

    return account_microservice_response.json()


@routers.post("/login", status_code=status.HTTP_200_OK)
async def login(request: Request, user: UserSignIn, response: Response,
                httpx_client: Client = Depends(get_account_client), redis=Depends(get_redis)):

    """
    The login function is used to authenticate a user.
        It takes in the following parameters:
            - request: The HTTP Request object.
            - user: A UserSignIn object containing the username and password of the user attempting to log in.
                    This is validated by pydantic, so it will be valid if it reaches this function.
                    If not, an error will be returned before reaching this function (see schemas/user_signin).

    :param request: Request: Get the request object
    :param user: UserSignIn: Validate the request body
    :param response: Response: Set the status code of the response
    :param httpx_client: Client: Call the login_call function in the account microservice
    :param redis: Store the refresh token in redis
    :return: The access and refresh token
    """
    user = user.model_dump()
    account_microservice_response = await httpx_client.login_call(user)

    if account_microservice_response.status_code == 200:
        access_token, refresh_token, key, value = await set_token(request, account_microservice_response.json())
        await redis.set(key, value, ex=settings.REFRESH_TOKEN_TTL)

        return {"access": access_token, "refresh": refresh_token}

    response.status_code = account_microservice_response.status_code
    return account_microservice_response.json()


@routers.post("/refresh")
async def refresh(request: Request, payload: dict = Depends(get_refresh_jwt_aut()), redis=Depends(get_redis)):

    """
    The refresh function is used to refresh the access token.
        The function takes in a request object and payload, which contains the user's id and email.
        It also takes in redis as a dependency, which is used to delete the old jti from redis.

    :param request: Request: Get the current request object
    :param payload: dict: Get the payload from the refresh token
    :param redis: Store the refresh token in redis
    :return: The access token and the refresh token
    """
    user_id = payload["id"]
    user_email = payload["email"]
    jti = payload["jti"]
    await redis.delete(f'user_{user_id} || {jti}')

    access_token, refresh_token, key, value = await set_token(request, {"id": user_id, "email": user_email})
    await redis.set(key, value, ex=settings.REFRESH_TOKEN_TTL)

    return {"access": access_token, "refresh": refresh_token}


@routers.post("/logout", status_code=status.HTTP_200_OK)
async def logout(payload: dict = Depends(get_refresh_jwt_aut()), redis=Depends(get_redis)):

    """
    The logout function is used to logout a user.
    It takes in the payload of the refresh token and uses it to delete that token from redis.
    The function returns a message saying that the user has been logged out successfully.

    :param payload: dict: Get the payload from the token
    :param redis: Get the redis connection
    :return: A message that the user has been logged out
    """
    await redis.delete(f'user_{payload["id"]} || {payload["jti"]}')
    return {"Logged out successfully"}


@routers.post("/logout_all", status_code=status.HTTP_200_OK)
async def logout_all(payload: dict = Depends(get_refresh_jwt_aut()), redis=Depends(get_redis)):

    """
    The logout_all function is used to logout all the devices of a user.
    It takes in a payload which contains the id of the user and uses it to delete all keys from redis that start with 'user_id ||'


    :param payload: dict: Get the payload from the refresh token,
    :param redis: Access the redis database
    :return: A dictionary with the key logged out successfully
    :doc-author: Trelent
    """
    # keys = [*(await redis.keys(f'user_{payload["id"]} || *'))]
    # print("1"*100)
    # print(keys)
    # print(type(keys))
    await redis.delete(*(await redis.keys(f'user_{payload["id"]} || *')))
    return {"Logged out successfully"}
