import json
import time

from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy.orm import Session
from sqlalchemy.future import select
from database import *
import models, schemas
from sqlalchemy.exc import SQLAlchemyError
from utils import *
from sqlalchemy import delete
app = FastAPI()

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)  # Ensure tables are created

@app.on_event("startup")
async def startup_event():
    await init_db()

async def get_async_db():
    async with async_session() as session:
        yield session
        await session.close()


@app.get("/ping")
def pong():
    return {"ping": "pong!"}

@app.post("/users/", response_model=schemas.User)
async def create_user(user: schemas.UserCreate, db: AsyncSession = Depends(get_async_db)):
    # db_user = models.User(**user.dict())
        db_user = models.User(
            name = user.name,
            email = user.email,
            age = user.age,
            gender = user.gender,
            city = user.city,
            interests = json.dumps(user.interests),
            version = 1
        )
        db.add(db_user)
        await db.commit()
        await db.refresh(db_user)
        db_user.interests = json.loads(db_user.interests)
        return db_user

@app.get("/users/", response_model=list[schemas.User])
async def read_users(skip: int = 0, limit: int = 10, db: AsyncSession = Depends(get_async_db)):
    result = await db.execute(select(models.User).offset(skip).limit(limit))
    users = result.scalars().all()
    for user in users:
        user.interests = json.loads(user.interests)
    return users

@app.get("/users/{user_id}", response_model=schemas.User)
async def read_user(user_id: int, db: AsyncSession = Depends(get_async_db)):
    result = await db.execute(select(models.User).filter(models.User.id == user_id))
    user = result.scalars().first()
    if user is None:
        raise HTTPException(status_code=404, detail=f"User with id: {user_id} found")
    user.interests = json.loads(user.interests)
    return user

@app.patch("/users/{user_id}", response_model=schemas.User)
async def update_user(user_id: int, updated_user: schemas.UserUpdate, db: AsyncSession = Depends(get_async_db)):
    result = await db.execute(select(models.User).filter(models.User.id == user_id))
    db_user = result.scalars().first()

    if db_user is None:
        raise HTTPException(status_code=404, detail=f"User with id: {user_id} found")

    update_data = updated_user.dict(exclude_unset=True)

    if "interests" in update_data:
        update_data["interests"] = json.dumps(update_data["interests"])

    # checking for the same version to ensure stale data is not updated

    await db.execute(
        models.User.__table__.update()
        .where(models.User.id == user_id)
        .where(models.User.version == db_user.version)
        .values(**update_data, version=db_user.version + 1)
    )

    await db.commit()
    await db.refresh(db_user)
    db_user.interests = json.loads(db_user.interests)
    return db_user

@app.delete("/users/{user_id}")
async def delete_user(user_id: int, db: AsyncSession = Depends(get_async_db)):
    result = await db.execute(select(models.User).filter(models.User.id == user_id))
    db_user = result.scalars().first()
    if db_user is None:
        raise HTTPException(status_code=404, detail=f"User with id: {user_id} found")
    delete_query = delete(models.User).where(
        models.User.id == user_id
    ).where(
        models.User.version == db_user.version
    )

    delete_result = await db.execute(delete_query)

    # check if the deletion query was executed and throw an error if not

    if delete_result.rowcount == 0:
        raise HTTPException(status_code=500, detail="Delete failed: User was modified by another request")

    await db.commit()

    return {"message": f"User with id {user_id} deleted successfully"}


@app.get("/users/{user_id}/matches", response_model=list[schemas.User])
async def find_matches(user_id: int, db: AsyncSession = Depends(get_async_db)):
    potential_matches = await find_potential_matches(user_id, db)
    return potential_matches
