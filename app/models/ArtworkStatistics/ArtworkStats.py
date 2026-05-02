from pydantic import BaseModel, Field

class ArtworkStats(BaseModel):
    views_amount: int = Field(default=0)
    likes: list[int] = Field(default_factory=list)
    dislikes: list[int] = Field(default_factory=list)
    favorites: list[int] = Field(default_factory=list)
    comments_amount: int = Field(default=0)