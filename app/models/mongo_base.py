from pydantic import BaseModel, Field
from typing import Optional, Any
from datetime import datetime

class MongoBaseModel(BaseModel):
    id: Optional[str] = Field(alias="_id", default=None) 
    status: str = Field(default="A", max_length=1)
    ip: str = Field(..., max_length=20)
    terminal: Any = Field(...)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: Optional[datetime] = Field(default=None)

    class Config:
        populate_by_name = True
        json_encoders = {
            datetime: lambda dt: dt.isoformat(),
        }