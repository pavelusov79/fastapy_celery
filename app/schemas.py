from typing import List

from pydantic import BaseModel, ConfigDict
from datetime import datetime


class Goods(BaseModel):
    name: str
    grade: int

    model_config = ConfigDict(from_attributes=True)
    # class Config:
    #     from_attributes = True


class ListGoods(BaseModel):
    status: str
    results: int
    goods: List[Goods]

    class Config:
        from_attributes = True


class TrackedGoods(BaseModel):
    id: int
    brand_name: str
    price: float
    date_field: datetime

