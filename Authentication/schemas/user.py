from typing import Type

from pydantic import BaseModel, EmailStr, model_validator, field_validator
import re

from fastapi import status, HTTPException


class BaseUser(BaseModel):
    email: EmailStr
    password: str


class UserSignIn(BaseUser):
    pass


class UserSignUp(BaseUser):
    confirmed_password: str

    @model_validator(mode='after')
    def check_passwords_match(self) -> "UserSignUp":
        password = self.password
        confirmed_password = self.confirmed_password
        if password is not None and password != confirmed_password:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Passwords don't match")
        return self

    @field_validator("password", mode="before")
    def validate_password(cls, value: str) -> str:
        PASSWORD_PATTERN = "^(?=.*?[A-Z])(?=.*?[a-z])(?=.*?[0-9])(?=.*?[#?!@$%^&*-_]).{8,}$"
        if re.match(PASSWORD_PATTERN, value):
            return value
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail='Passwords must be at least 8 characters in length, '
                                   'and it must include at least one capital letter (or uppercase), '
                                   'one lowercase, one number and one special character')
