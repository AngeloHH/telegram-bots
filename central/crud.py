import os

from cryptography.fernet import Fernet

from sqlalchemy.orm import Session

from central import models, schemas


def media(*args):
    path = f'..{os.sep}temp'
    if len(args) != 0: path = path + os.sep
    if not os.path.exists(path): os.makedirs(path)
    return path + os.sep.join(arg for arg in args)


def get_user(db: Session, user_id: int):
    query = db.query(models.Profile)
    filters = models.Profile.id == user_id
    return query.filter(filters).first()


def toggle_admin(db: Session, user_id: int):
    filters = models.Profile.id == user_id
    user = db.query(models.Profile)
    user = user.filter(filters).first()
    user.is_admin = not user.is_admin
    db.commit()
    return user


def get_users(db: Session, skip: int = 0, limit: int = 100):
    query = db.query(models.Profile)
    query = query.offset(skip)
    return query.limit(limit).all()


def create_user(db: Session, user: schemas.Profile):
    db_user = models.Profile(**vars(user))
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return vars(user)


def get_sticker(db: Session, bot_id: int, sticker_name: str):
    query = db.query(models.Sticker)
    filters = models.Sticker.bot_id == bot_id
    query = query.filter(filters)
    filters = models.Sticker.name == sticker_name
    query = query.filter(filters)
    return query.first()


def get_stickers(db: Session, bot_id: int):
    query = db.query(models.Sticker)
    filters = models.Sticker.bot_id == bot_id
    return query.filter(filters).all()


def add_sticker(db: Session, sticker: dict):
    new_sticker = models.Sticker(**sticker)
    db.add(new_sticker)
    db.commit()
    db.refresh(new_sticker)
    return sticker


def get_text(db: Session, bot_id: int, key: str, lang: str):
    query = db.query(models.Language).filter(models.Language.bot_id == bot_id)
    query = query.filter(models.Language.language == lang)
    return query.filter(models.Language.name == key).all()


def add_text(db: Session, text: dict):
    new_text = models.Language(**text)
    db.add(new_text)
    db.commit()
    db.refresh(new_text)
    return text


def add_token(db: Session):
        key = Fernet.generate_key()
        key = key.decode('utf-8')
        new_token = models.Token(id=key)
        db.add(new_token)
        db.commit()
        db.refresh(new_token)
        return key


def get_token(db: Session, token: str):
    query = db.query(models.Token)
    filters = models.Token.id == token
    query = query.filter(filters)
    return query.first()


def create_chat(db: Session, chat: schemas.Chat, bot_id: int):
    db_chat = models.Chat(**vars(chat), bot_id=bot_id)
    db.add(db_chat)
    db.commit()
    db.refresh(db_chat)
    return vars(chat)
