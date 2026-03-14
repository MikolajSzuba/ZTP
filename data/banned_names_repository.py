from sqlalchemy.orm import Session
from sqlalchemy import select

from model.banned_names_orm import BannedNamesORM



def get_banned_names_phrases(db:Session):
    query= select(BannedNamesORM)   
    result=db.execute(query)
    return [row.name for row in result.scalars().all()]