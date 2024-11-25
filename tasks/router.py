from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import insert, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_async_session
from auth.models import User
from auth.router import current_user
from tasks.schemas import UserTask
from app.models import UserTasks, Goods
from tasks.tasks import get_data

router = APIRouter(
    prefix='/tasks',
    tags=['Tasks']
)

time_int = {
       'TEST': 30,
        'HOUR': 3600,
        'TWELVE_H': 3600 * 12,
        'TWENTY_FOUR_H': 3600 * 24
    }


@router.post('/add_task/')
async def add_user_task(new_task: UserTask, user: User = Depends(current_user), session: AsyncSession = Depends(get_async_session)):
    if not current_user:
        raise HTTPException(
            status_code=401,
            detail=f'user with id: {user.id} is not logged'
        )
    stmt = insert(UserTasks).values(**new_task.model_dump(), fk_user=user.id)
    await session.execute(stmt)
    await session.commit()
    return {'status': 'success'}


@router.get('/tasks/')
async def get_user_tasks(user: User = Depends(current_user), session: AsyncSession = Depends(get_async_session)):
    if not current_user:
        raise HTTPException(
            status_code=401,
            detail=f'user with id: {user.id} is not logged'
        )
    query = select(UserTasks).where(UserTasks.fk_user == user.id)
    results = await session.execute(query)
    return results.scalars().all()


@router.put('/close_task/{task_id}')
async def close_user_task(task_id: int, user: User = Depends(current_user), session: AsyncSession = Depends(get_async_session)):
    if not current_user:
        raise HTTPException(
            status_code=401,
            detail=f'user with id: {user.id} is not logged'
        )
    task = select(UserTasks).where(UserTasks.id == task_id, UserTasks.fk_user == user.id)
    res = await session.execute(task)
    if not res.scalar():
        raise HTTPException(
            status_code=404,
            detail=f'task id: {task_id} which belongs to {user.username} does not exist'
        )
    stmt = update(UserTasks).where(UserTasks.id == task_id, UserTasks.fk_user == user.id).values(is_active=False)
    await session.execute(stmt)
    await session.commit()
    return {"status": "success"}


#  отправка задачи с использованием celery
@router.get('/launch_users_tasks/')
async def send_tasks(user: User = Depends(current_user), session: AsyncSession = Depends(get_async_session)):
    users_tasks = select(UserTasks).where(UserTasks.fk_user == user.id, UserTasks.is_active == True)
    result = await session.scalars(users_tasks)
    goods_name = []
    for item in result.all():
        goods = await session.scalars(select(Goods).where(Goods.id == item.fk_goods))
        goods_item = goods.one()
        get_data.apply_async((goods_item.grade, user.id, item.parse_till_date, time_int[item.set_interval]),
                             expires=item.parse_till_date)
        goods_name.append({f'Название: {goods_item.name} арт. {goods_item.grade})'})
    return {'status': 'success', 'launched tasks for goods': goods_name}

