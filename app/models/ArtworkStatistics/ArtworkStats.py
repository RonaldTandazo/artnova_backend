from pydantic import BaseModel, Field
from typing import List

class ArtworkStats(BaseModel):
    views_amount: int = Field(default=0)
    likes: List[int] = Field(default_factory=list)
    dislikes: List[int] = Field(default_factory=list)
    favorites: List[int] = Field(default_factory=list)
    comments_amount: int = Field(default=0)