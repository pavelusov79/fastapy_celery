import datetime
import enum

from sqlalchemy import DateTime, String, Integer, Column, ForeignKey, Boolean, Float, BigInteger, Enum
from sqlalchemy.orm import relationship

from auth.models import Base


class Goods(Base):
    __tablename__ = 'goods'

    id = Column(BigInteger, primary_key=True)
    name = Column('полное наименование товара', String(128))
    grade = Column('введите артикул товара с сайта wildberries', Integer)
    fk_user = Column(Integer, ForeignKey("user.id"))

    def __repr__(self):
        return self.name


class UserTrackedGoods(Base):
    __tablename__ = 'user_tracked_goods'

    id = Column(BigInteger, primary_key=True)
    fk_user = Column(Integer, ForeignKey("user.id"))
    user = relationship("User", backref="tracked_goods", passive_deletes=True)
    fk_goods = Column(Integer, ForeignKey("goods.id"))
    t_goods = relationship("Goods", backref="tracked_goods", passive_deletes=True, lazy='joined')
    brand_name = Column('брэнд', String(32))
    price = Column('цена товара', Float)
    date_field = Column("дата время", DateTime)

    def __repr__(self):
        return f'{self.user} {self.fk_goods}'


class TimeChoice(enum.Enum):
    HOUR = 3600
    TWELVE_H = 3600 * 12
    TWENTY_FOUR_H = 3600 * 24
    TEST = 30


class UserTasks(Base):
    __tablename__ = 'tasks'

    id = Column(BigInteger, primary_key=True)
    fk_user = Column(Integer, ForeignKey("user.id"))
    user = relationship("User", backref="user_tasks", passive_deletes=True)
    fk_goods = Column('выберите товар для отслеживания', Integer, ForeignKey('goods.id'))
    goods = relationship("Goods", backref='task_goods', passive_deletes=True, lazy='joined')
    set_interval = Column('выберите интервал отслеживания', Enum(TimeChoice, name='time_choice', create_type=False))
    start_date = Column('дата начала отслеживания', DateTime, default=datetime.datetime.now())
    parse_till_date = Column('введите дату окончания отслеживания', DateTime)
    is_active = Column('Задача запущена', Boolean, default=True)

    def __repr__(self):
        return f'{self.user} {self.fk_goods}'
