import json

import httpx


class Client:
    register_url = "http://127.0.0.1:8001/accounts/v1/register"
    login_url = "http://127.0.0.1:8001/accounts/v1/login"

    async def register_call(self, payload: dict):
        async with httpx.AsyncClient() as client:
            response = await client.post(self.register_url, json=payload)
        # response.raise_for_status()
        return response

    async def login_call(self, payload: dict):
        async with httpx.AsyncClient() as client:
            response = await client.post(self.login_url, json=payload)
        # response.raise_for_status()
        return response


account_client = Client()


def get_account_client():
    return account_client
