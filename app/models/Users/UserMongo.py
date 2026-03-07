from pydantic import Field
from app.models.mongo_base import MongoBaseModel

class UserMongo(MongoBaseModel):
    user_id: int = Field(...)
    username: str = Field(...)
    avatar: str | None = Field(default=None)