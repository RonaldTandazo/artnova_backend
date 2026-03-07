from pydantic import Field
from app.models.mongo_base import MongoBaseModel

class ArtworkViews(MongoBaseModel):
    artwork_id: int = Field(...)
    user_id: int | None = Field(default=None)