from sqlalchemy import Boolean, Column, Integer, String, DateTime
from sqlalchemy.sql import func

from central.database import base


class Profile(base):
    __tablename__ = "profiles"

    id = Column(Integer, primary_key=True)
    username = Column(String)
    first_name = Column(String)
    last_name = Column(String)
    is_bot = Column(Boolean, default=False)
    is_locked = Column(Boolean, default=False)
    is_admin = Column(Boolean, default=False)
    phone = Column(String)


class Sticker(base):
    __tablename__ = "stickers"

    id = Column(Integer, autoincrement=True, primary_key=True, index=True)
    sticker_id = Column(String)
    name = Column(String)
    emoji = Column(String)
    bot_id = Column(Integer)


class Language(base):
    __tablename__ = "languages"

    id = Column(Integer, autoincrement=True, primary_key=True, index=True)
    name = Column(String)
    bot_id = Column(Integer)
    text = Column(String)
    language = Column(String)


class Token(base):
    __tablename__ = "tokens"

    id = Column(String, primary_key=True)
    expiration = Column(DateTime(timezone=True), onupdate=func.now())

