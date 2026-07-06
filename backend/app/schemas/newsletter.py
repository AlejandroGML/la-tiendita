from pydantic import BaseModel, EmailStr


class SubscribeRequest(BaseModel):
    email: EmailStr
    lang: str = "es"


class SubscribeResponse(BaseModel):
    message: str
