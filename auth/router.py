from fastapi_users import FastAPIUsers
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from auth.auth import auth_backend
from auth.models import User
from auth.manager import get_user_manager
from auth.schemas import GetUser, ListUsers, UserRead
from database import get_async_session

fastapi_users = FastAPIUsers[User, int](
    get_user_manager,
    [auth_backend],
)

current_user = fastapi_users.current_user()

router = APIRouter(
    prefix="/users",
    tags=["user"]
)


@router.get("/protected-route", response_model=GetUser)
def protected_route(user: User = Depends(current_user)):
    print('user = ', user.username)
    return user


@router.get('/db_users')
async def get_users(session: AsyncSession = Depends(get_async_session)):
    query = select(User).where(User.is_superuser == False)
    result = await session.execute(query)
    return result.mappings().all()


@router.get("/users", response_model=list[GetUser])
async def get_users(session: AsyncSession = Depends(get_async_session), limit: int = 5, page: int = 1, search: str = ''):
    skip = (page - 1) * limit
    query = select(User).where(User.is_superuser == False, User.username.contains(search)).limit(limit).offset(skip)
    results = await session.execute(query)
    # второй вариант вывода
    # results = await session.scalars(query)
    # response_results = [GetUser.model_validate(u).model_dump() for u in results.all()]
    # return response_results
    return results.scalars().all()


@router.get("/users/get_current_user/{user_id}", response_model=GetUser)
async def get_user(user: User = Depends(current_user), session: AsyncSession = Depends(get_async_session)):
    user = select(User).where(User.id == user.id)
    result = await session.execute(user)
    if not result:
        raise HTTPException(
            status_code=401,
            detail=f'user with id: {user.id} is not logged'
        )
    return result.scalars().first()
#
#
# @router.put('/users/{user_id}')
# async def update_user(user_id: int, payload: GetUser, session: AsyncSession = Depends(get_async_session)):
#     user = session.query(User).filter(User.id == user_id).fisrt()
#     if not user:
#         raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
#                             detail=f'No user with this id: {user_id} found')
#     update_data = payload.model_dump(exclude_unset=True)
#     user.filter(User.id == user_id).update(update_data)
#     await session.commit()
#     await session.refresh(user)
#     return {"status": "success", "user": user}
#
#
# @router.delete('/users/delete/{user_id}')
# async def delete_user(user_id: int, session: AsyncSession = Depends(get_async_session)):
#     admin = session.select(User).where(User.is_superuser==True).first()
#     if admin:
#         user = session.query(User).filter(User.id == user_id).first()
#         if not user:
#             raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
#                                 detail=f'No user with this id: {user_id} found')
#         user.delete(synchronize_session=False)
#         await session.commit()
#         return Response(status_code=status.HTTP_204_NO_CONTENT)
#     return Response(status_code=status.HTTP_403_FORBIDDEN)
