from pydantic import Field
from app.models.mongo_base import MongoBaseModel
from app.models.ArtworkModel.ArtworkModelSettings import ArtworkModelSettings

class ArtworkModel(MongoBaseModel):
    artwork_id: int = Field(...)
    owner_id: int = Field(...)
    main_file: str = Field(...)
    resources: list[str] = Field(default_factory=list)
    settings: ArtworkModelSettings = Field(default_factory=ArtworkModelSettings)