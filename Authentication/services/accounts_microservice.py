import httpx

from config.config import get_settings

settings = get_settings()


class Client:
    register_url = settings.ACCOUNT_REGISTER_URL

    login_url = settings.ACCOUNT_LOGIN_URL

    async def register_call(self, payload: dict, request):
        headers = {"unique_id": request.state.unique_id}
        async with httpx.AsyncClient(headers=headers) as client:
            response = await client.post(self.register_url, json=payload)
        # response.raise_for_status()
        return response

    async def login_call(self, payload: dict, request):
        headers = {"unique_id": request.state.unique_id}
        async with httpx.AsyncClient(headers=headers) as client:
            response = await client.post(self.login_url, json=payload)
        # response.raise_for_status()
        return response


account_client = Client()


def get_account_client():
    return account_client
