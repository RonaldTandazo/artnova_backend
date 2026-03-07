from pydantic import Field
from typing import List
from app.models.mongo_base import MongoBaseModel
from app.models.ArtworkStatistics.ArtworkComment import ArtworkComment
from app.models.ArtworkStatistics.ArtworkStats import ArtworkStats

class ArtworkStatistics(MongoBaseModel):
    artwork_id: int = Field(...)
    owner_id: int = Field(...)
    stats: ArtworkStats = Field(default_factory=ArtworkStats)
    comments: List[ArtworkComment] = Field(default_factory=list)