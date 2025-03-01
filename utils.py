import json
import os

from sqlalchemy.orm import Session
from models import User
from fastapi import HTTPException
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession

MATCH_LIMIT = int(os.getenv("MATCH_LIMIT", 3))  # Default to 3
AGE_LIMIT = int(os.getenv("AGE_LIMIT", 10))  # Default to 10


async def find_potential_matches(user_id: int, db: AsyncSession):
    result = await db.execute(select(User).filter(User.id == user_id))
    db_user = result.scalars().first()
    if db_user is None:
        raise HTTPException(status_code=404, detail=f"User with id: {user_id} found")
    user_interests = json.loads(db_user.interests)

    result = await db.execute(
        select(User).filter(
            User.id != user_id,
            User.city == db_user.city,
            User.age.between(db_user.age - AGE_LIMIT, db_user.age + AGE_LIMIT)
        )
    )
    potential_matches = result.scalars().all()


    if not potential_matches:
        result = await db.execute(select(User).filter(User.id != user_id))
        matches = result.scalars().all()[:MATCH_LIMIT]
        for match in matches:
            match.interests = json.loads(match.interests)

        return matches

    def match_score(other_user):
        other_interests = json.loads(other_user.interests)
        return len(set(user_interests) & set(other_interests))  # Count common interests

    sorted_matches = sorted(potential_matches, key=match_score, reverse=True)

    if not sorted_matches:
        return potential_matches[:MATCH_LIMIT]

    sorted_matches = sorted_matches[:3]

    for match in sorted_matches:
        match.interests = json.loads(match.interests)

    return sorted_matches



