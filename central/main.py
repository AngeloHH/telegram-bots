import os

import uvicorn

from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy.orm import Session
from starlette.responses import FileResponse

from central import crud, models, schemas
from central.crud import mega_download, zippy_download, split_zip
from central.database import session_local, engine

models.base.metadata.create_all(bind=engine)

app = FastAPI()


# Dependency
def get_db():
    db = session_local()
    try:
        yield db
    finally:
        db.close()


@app.post("/users/", response_model=schemas.Profile)
def create_user(user: schemas.Profile, db: Session = Depends(get_db)):
    return crud.create_user(db=db, user=user)


@app.get("/users/")
def read_users(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    users = crud.get_users(db, skip=skip, limit=limit)
    return users


@app.get("/users/{user_id}")
def read_user(user_id: int, db: Session = Depends(get_db)):
    db_user = crud.get_user(db, user_id=user_id)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user


@app.post("/bot/{bot_id}/stickers", response_model=schemas.Sticker)
def add_sticker(bot_id: int, sticker: schemas.Sticker, db: Session = Depends(get_db)):
    sticker = {**vars(sticker), 'bot_id': bot_id}
    return crud.add_sticker(db, sticker)


@app.get("/bot/{bot_id}/stickers")
def get_stickers(bot_id: int, db: Session = Depends(get_db)):
    return crud.get_stickers(db, bot_id)


@app.get("/bot/{bot_id}/stickers/{name}")
def get_sticker(bot_id: int, name: str, db: Session = Depends(get_db)):
    return crud.get_sticker(db, bot_id, name)


@app.post("/bot/{bot_id}/lang/{lang}/add")
def add_text(bot_id: int, lang: str, text: schemas.NewLanguage, db: Session = Depends(get_db)):
    return crud.add_text(db, {**vars(text), 'bot_id': bot_id, 'language': lang})


@app.get("/bot/{bot_id}/lang/{lang}/get")
def get_text(bot_id: int, lang: str, key: str, db: Session = Depends(get_db)):
    return crud.get_text(db, bot_id, key, lang)


@app.get("/tokens/generate")
def add_token(db: Session = Depends(get_db)):
    return {'token': crud.add_token(db)}


@app.post("/tokens/consume")
def rem_token(token: str, user_id: int, db: Session = Depends(get_db)):
    token = crud.get_token(db, token)
    if token is None:
        raise HTTPException(status_code=404, detail="Token not exist")
    db.delete(token)
    db.commit()
    if not crud.get_user(db, user_id).is_admin:
        crud.toggle_admin(db, user_id)
    return {'token': None}


@app.get("/media/download/{server}")
def download_file(server: str, url: str, max_size: int = 50, db: Session = Depends(get_db)):
    server_list = {'mega': mega_download, 'zippyshare': zippy_download}
    can_download = server not in server_list
    if can_download: raise HTTPException(404, detail="Server not found")
    file_name = server_list[server](url)
    file_size = os.stat(file_name).st_size / (1024 * 1024)
    file_url = ['/media/get/' + file_name.split(os.sep)[-1]]
    too_long = file_size >= max_size or max_size != 0
    return file_url if not too_long else split_zip(file_name)


@app.get("/media/delete/{filename}")
def delete_media(filename: str, db: Session = Depends(get_db)):
    error = HTTPException(403, 'Parameter not allowed')
    if '/' in filename or '\\' in filename: raise error
    if os.path.exists('temp' + os.sep + filename):
        return os.remove('temp' + os.sep + filename)
    raise HTTPException(404, detail="File not found")


@app.get("/media/get/{filename}")
def get_media(filename: str, db: Session = Depends(get_db)):
    error = HTTPException(403, 'Parameter not allowed')
    if '/' in filename or '\\' in filename: raise error
    path = 'temp' + os.sep + filename
    if os.path.exists(path): return FileResponse(path)
    raise HTTPException(404, detail="File not found")


if __name__ == '__main__':
    host = {'host': '0.0.0.0', 'port': 8000}
    uvicorn.run("__main__:app", **host, reload=True)
