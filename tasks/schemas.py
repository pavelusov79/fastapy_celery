from pydantic import BaseModel, ConfigDict
from datetime import datetime

from app.models import TimeChoice


class UserTask(BaseModel):
    fk_goods: int
    set_interval: TimeChoice
    start_date: datetime
    parse_till_date: datetime

    model_config = ConfigDict(from_attributes=True)


class TaskUserClose(BaseModel):
    id: int
    is_active: bool

    model_config = ConfigDict(from_attributes=True)

