
from sqlalchemy import insert, select, create_engine

from app.models import UserTrackedGoods, Goods
from config import *


DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

engine = create_engine(DATABASE_URL)


def some_func(user_id: int = 3, grade: int = 157367275):
    with engine.connect() as session:
        query = select(Goods).where(Goods.fk_user == user_id, Goods.grade == grade)
        res = session.execute(query)
        res = res.scalars().one()
        print('res = ', res)
        stmt = insert(UserTrackedGoods).values(fk_goods=res, fk_user=user_id, price=10000,
                                               brand_name='test')
        session.execute(stmt)
        session.commit()
        session.close()


some_func()

