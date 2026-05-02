from pydantic import Field
from app.models.mongo_base import MongoBaseModel
from bson import ObjectId

class ArtworkComment(MongoBaseModel):
    id: str = Field(
        default_factory=lambda: str(ObjectId()),
    )
    user_id: int = Field(...)
    username: str = Field(...)
    avatar: str | None = Field(default=None)
    comment: str = Field(..., min_length=1)
    likes: list[int] = Field(default_factory=list)
    dislikes: list[int] = Field(default_factory=list)
    replies: list['ArtworkComment'] = Field(default_factory=list)