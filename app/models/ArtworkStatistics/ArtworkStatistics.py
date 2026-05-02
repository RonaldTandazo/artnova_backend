from pydantic import Field
from app.models.mongo_base import MongoBaseModel
from app.models.ArtworkStatistics.ArtworkComment import ArtworkComment
from app.models.ArtworkStatistics.ArtworkStats import ArtworkStats

class ArtworkStatistics(MongoBaseModel):
    artwork_id: int = Field(...)
    owner_id: int = Field(...)
    stats: ArtworkStats = Field(default_factory=ArtworkStats)
    comments: list[ArtworkComment] = Field(default_factory=list)