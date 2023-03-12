from datetime import datetime

from pydantic import BaseModel


class Profile(BaseModel):
    id: int
    username: str = None
    first_name: str = None
    last_name: str = None
    is_bot: bool = False
    is_locked: bool = False
    is_admin: bool = False
    phone: str = None


class Sticker(BaseModel):
    sticker_id: str
    name: str
    emoji: str


class NewLanguage(BaseModel):
    name: str
    text: str


class Language(NewLanguage):
    id: int
    bot_id: int
    language: str


class Token(BaseModel):
    id: int
    expiration: datetime = datetime.now()


class Chat(BaseModel):
    id: int
    title: str = None
    description: str = None
    invite_link: str = None
    type: str
