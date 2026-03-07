from pydantic import Field, BeforeValidator, ConfigDict
from app.models.mongo_base import MongoBaseModel
from bson.objectid import ObjectId
from typing import Any, Annotated

def validate_objectid(v: Any) -> ObjectId:
    if isinstance(v, ObjectId):
        return v
    if isinstance(v, str) and ObjectId.is_valid(v):
        return ObjectId(v)
    raise ValueError('Invalid ObjectId or string')

PyObjectId = Annotated[
    ObjectId, 
    BeforeValidator(validate_objectid)
]

class ChatMessage(MongoBaseModel):
    chat_id: PyObjectId = Field(...)
    user_id: int = Field(...)
    type_message: str = Field(...)
    message: str = Field(...)
    model_config = ConfigDict(arbitrary_types_allowed=True, json_encoders={ObjectId: str})
