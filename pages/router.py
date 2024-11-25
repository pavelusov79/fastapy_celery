import datetime
import httpx

from fastapi import APIRouter, Depends, Request, status, Form, HTTPException
from fastapi.templating import Jinja2Templates
from sqlalchemy import select, insert
from fastapi.responses import RedirectResponse

from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Goods, UserTasks, UserTrackedGoods
from app.router import get_goods
from database import get_async_session
from auth.router import current_user, fastapi_users
from auth.models import User
from tasks.router import get_user_tasks
from tasks.tasks import get_data

from fastapi_users.password import PasswordHash, BcryptHasher, Argon2Hasher

hashed_password = PasswordHash((Argon2Hasher(), BcryptHasher()))

router = APIRouter(
    prefix='',
    tags=['Pages']
)

templates = Jinja2Templates(directory='templates')

user_option = fastapi_users.current_user(optional=True)

# @router.get('/')
# def get_login(request: Request):
#     return templates.TemplateResponse('login.html', {
#         'request': request,
#     })


@router.get('/')
@router.post('/')
async def login(request: Request, session: AsyncSession = Depends(get_async_session), user: User = Depends(user_option)):
    form_req = await request.form()
    if form_req:
        query = select(User).where(User.email == form_req.get('email'))
        res = await session.execute(query)
        user = res.scalars().one_or_none()
        if user:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    url=f'{request.base_url}auth/jwt/login',
                    headers={
                        'accept': 'application/json',
                        'Content-Type': 'application/x-www-form-urlencoded',
                    },
                    data={
                        'username': form_req.get('email'),
                        'password': form_req.get('password')
                    },
                )
                if response.status_code == 400:
                    raise HTTPException(
                        status_code=400,
                        detail=f'Введенный пароль не соответствует паролю в базе данных.'
                    )

            redirect = RedirectResponse(url=f'{request.base_url}cabinet/{user.id}', status_code=status.HTTP_302_FOUND)
            redirect.set_cookie(key='fastapiusersauth', value=response.cookies.get('fastapiusersauth'), httponly=True)
            return redirect
        else:
            raise HTTPException(
                status_code=400,
                detail=f'Пользователь с почтовым ящиком {form_req.get("email")} не найден в базе.'
            )
    return templates.TemplateResponse('login.html', {
        'request': request,
        'user': user
    })


@router.get('/cabinet/{user_id}')
def user_cabinet(request: Request, goods=Depends(get_goods), user: User = Depends(current_user)):
    return templates.TemplateResponse('cabinet.html', {
        'request': request,
        'user': user,
        'goods': goods
    })


@router.get('/cabinet/{user_id}/tasks')
async def user_tasks(request: Request, tasks=Depends(get_user_tasks), user: User = Depends(current_user),
                     session: AsyncSession = Depends(get_async_session)):
    for task in tasks:
        if task.parse_till_date < datetime.datetime.now():
            task.is_active = False
            await session.commit()
    return templates.TemplateResponse('tasks.html', {
        'request': request,
        'user': user,
        'tasks': tasks
    })


@router.get('/cabinet/{user_id}/add_task')
async def add_task(request: Request, user: User = Depends(current_user), session: AsyncSession = Depends(get_async_session)):
    goods = select(Goods).where(Goods.fk_user == user.id)
    result = await session.scalars(goods)
    res_goods = result.all()
    return templates.TemplateResponse('add_task.html', {
        'request': request,
        'goods': res_goods,
        'user': user
    })


time_int = {
       'TEST': 30,
        'HOUR': 3600,
        'TWELVE_H': 3600 * 12,
        'TWENTY_FOUR_H': 3600 * 24
    }


@router.post('/cabinet/{user_id}/add_task')
async def add_task(request: Request, user: User = Depends(current_user), session: AsyncSession = Depends(get_async_session)):
    form = await request.form()
    date = datetime.datetime.strptime(form.get('parse_till_date'), '%Y-%m-%dT%H:%M')
    stmt = insert(UserTasks).values(fk_goods=int(form.get('goods')), set_interval=form.get('interval'),
                                    parse_till_date=date, fk_user=user.id)
    await session.execute(stmt)
    await session.commit()
    goods = await session.scalars(select(Goods).where(Goods.id == int(form.get('goods'))))
    goods_item = goods.one()
    get_data.apply_async((goods_item.grade, user.id, date, time_int[form.get('interval')]), expires=date)
    return RedirectResponse(url=f'{request.base_url}cabinet/{user.id}/tasks', status_code=status.HTTP_302_FOUND)


@router.get('/cabinet/{user_id}/{task_id}/delete_task')
async def delete_task(request: Request, task_id: int, user: User = Depends(current_user), session: AsyncSession = Depends(get_async_session)):
    task = await session.scalars(select(UserTasks).where(UserTasks.fk_user == user.id, UserTasks.id == task_id))
    res = task.one()
    await session.delete(res)
    await session.commit()
    return RedirectResponse(url=f'{request.base_url}cabinet/{user.id}/tasks', status_code=status.HTTP_302_FOUND)


@router.get('/cabinet/{user_id}/{task_id}/edit_task')
async def edit_task(request: Request, task_id: int, user: User = Depends(current_user), session: AsyncSession = Depends(get_async_session)):
    task = await session.scalars(select(UserTasks).where(UserTasks.fk_user == user.id, UserTasks.id == task_id))
    task = task.one()
    goods = select(Goods).where(Goods.fk_user == user.id)
    result = await session.scalars(goods)
    res_goods = result.all()
    return templates.TemplateResponse('edit_task.html', {
        'request': request,
        'user': user,
        'task': task,
        'goods': res_goods
    })


@router.post('/cabinet/{user_id}/{task_id}/update_task')
async def update_task(request: Request, task_id: int, goods: str = Form(...), interval: str = Form(...),
                      start_date: str = Form(...), parse_till_date: str = Form(...),
                      user: User = Depends(current_user), session: AsyncSession = Depends(get_async_session)):
    task = await session.scalars(select(UserTasks).where(UserTasks.fk_user == user.id, UserTasks.id == task_id))
    task = task.one()
    task.fk_goods = int(goods)
    task.set_interval = interval
    task.start_date = datetime.datetime.strptime(start_date, '%Y-%m-%dT%H:%M')
    task.parse_till_date = datetime.datetime.strptime(parse_till_date, '%Y-%m-%dT%H:%M')
    form = await request.form()
    if form.get('is_active') and datetime.datetime.strptime(parse_till_date,
                                                             '%Y-%m-%dT%H:%M') > datetime.datetime.now():
        task.is_active = True
    else:
        task.is_active = False
    # task.is_active = True if form.get('is_active') else False
    await session.commit()
    if task.is_active:
        goods = await session.scalars(select(Goods).where(Goods.id == task.fk_goods))
        goods_item = goods.one()
        get_data.apply_async((goods_item.grade, user.id, task.parse_till_date, time_int[interval]),
                             expires=task.parse_till_date)
    return RedirectResponse(url=f'{request.base_url}cabinet/{user.id}/tasks', status_code=status.HTTP_302_FOUND)


@router.get('/cabinet/{user_id}/tracked_goods')
async def user_tracked_goods(request: Request, user: User = Depends(current_user), session: AsyncSession = Depends(get_async_session)):
    query = select(UserTrackedGoods).where(UserTrackedGoods.fk_user == user.id).order_by(UserTrackedGoods.date_field)
    res = await session.execute(query)
    goods = res.scalars().all()
    return templates.TemplateResponse('tracked_goods.html', {
        'request': request,
        'user': user,
        'tracked_goods': goods
    })


@router.post('/logout')
@router.get('/logout')
async def logout(request: Request):
    async with httpx.AsyncClient() as client:
        await client.post(
            url=f'{request.base_url}auth/jwt/logout',
            headers={
                'accept': 'application/json',
            },
            cookies={'fastapiusersauth': request.cookies.get('fastapiusersauth')}
        )

    redirect_response = RedirectResponse(url=f'{request.base_url}', status_code=status.HTTP_302_FOUND)
    redirect_response.delete_cookie('fastapiusersauth')
    return redirect_response


@router.get('/register')
@router.post('/register')
async def register_user(request: Request, session: AsyncSession = Depends(get_async_session)):
    form_req = await request.form()
    if form_req:
        stmt = insert(User).values(username=form_req.get('username'), email=form_req.get('email'),
                                   hashed_password=hashed_password.hash(password=form_req.get('password')))
        await session.execute(stmt)
        await session.commit()
        return RedirectResponse(url=request.base_url, status_code=status.HTTP_302_FOUND)
    return templates.TemplateResponse('register.html', {
        'request': request,
    })


@router.get('/cabinet/{user_id}/new_goods')
@router.post('/cabinet/{user_id}/new_goods')
async def new_goods(request: Request, session: AsyncSession = Depends(get_async_session), user: User = Depends(current_user)):
    form_req = await request.form()
    if form_req:
        stmt = insert(Goods).values(name=form_req.get('name'), grade=int(form_req.get('grade')), fk_user=user.id)
        await session.execute(stmt)
        await session.commit()
        return RedirectResponse(url=f'{request.base_url}cabinet/{user.id}', status_code=status.HTTP_302_FOUND)
    return templates.TemplateResponse('add_goods.html', {
        'request': request,
    })
