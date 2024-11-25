from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy import select, insert

from sqlalchemy.ext.asyncio import AsyncSession

from database import get_async_session
from app.models import Goods, UserTrackedGoods
from app.schemas import Goods as SchGoods
from app.schemas import TrackedGoods
from auth.router import current_user
from auth.models import User

router = APIRouter(
    prefix='/app',
    tags=['Goods']
)


@router.get("/goods/", response_model=List[SchGoods])
async def get_goods(user: User = Depends(current_user), session: AsyncSession = Depends(get_async_session)):
    # skip = (page - 1) * limit
    # query = select(Goods).where(Goods.fk_user == user.id).limit(10)
    # result = await session.execute(query)
    results = await session.scalars(select(Goods).where(Goods.fk_user == user.id).limit(10))
    response_data = [
        SchGoods.model_validate(u).model_dump() for u in results.all()
    ]
    return response_data


@router.post("/new_goods/")
async def create_goods(new_goods: SchGoods, user: User = Depends(current_user),
                       session: AsyncSession = Depends(get_async_session)):
    stmt = insert(Goods).values(**new_goods.model_dump(), fk_user=user.id)
    await session.execute(stmt)
    await session.commit()
    return {'status': 'success'}


@router.get('/tracked_goods', response_model=list[TrackedGoods])
async def tracked_goods(user: User = Depends(current_user), session: AsyncSession = Depends(get_async_session),
                        limit: int = 10, page: int = 1, search: str = ''):
    skip = (page - 1) * limit
    query = select(UserTrackedGoods).where(UserTrackedGoods.fk_user == user.id,
                                           Goods.name.contains(search)).limit(limit).offset(skip)
    results = await session.execute(query)
    return results.scalars().all()
