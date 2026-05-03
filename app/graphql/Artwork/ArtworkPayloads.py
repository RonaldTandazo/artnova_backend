from app.graphql.Category.CategoryPayloads import CategoryPayload
from app.graphql.Topic.TopicPayloads import TopicPayload
from app.graphql.Software.SoftwarePayloads import SoftwarePayload
from app.graphql.Publishing.PublishingPayloads import PublishingPayload
from app.graphql.Standard.StandardPayloads import StandardPayload
from app.graphql.ArtworkStatistics.ArtworkStatisticsPayloads import ArtworkStatsPayload
from typing import Optional
from datetime import datetime
import strawberry

@strawberry.type
class ModelSettings:
    environment: list[str]
    contactShadow: bool
    intensity: list[float]
    exposure: list[float]
    modelColor: str
    backgroundColor: str
    autoRotate: bool
    lightPosition: list[float]
    lockCameraReset: bool
    lockInteraction: bool

@strawberry.type
class ArtworkPayload:
    artworkId: int
    title: str
    thumbnail: Optional[str | None] = None
    publishingId: int
    hasImages: bool = False
    hasVideos: bool = False
    has3DFile: bool = False
    owner: str
    avatar: Optional[str | None] = None
    createdAt: str

@strawberry.type
class ArtworkItemPayload:
    artworkId: int
    title: str
    thumbnail: Optional[str | None] = None
    publishingId: int
    scheduleAt: Optional[datetime] = None
    stats: ArtworkStatsPayload

@strawberry.type
class ArtworkOwnerPayload:
    userId: int
    username: str
    avatar: str | None

@strawberry.type
class ArtworkDetailsPayload:
    artworkId: int
    title: str
    description: Optional[str | None] = None
    matureContent: bool
    categories: list[StandardPayload]
    topics: list[StandardPayload]
    softwares: list[StandardPayload]
    publishingId: int
    thumbnail: str | None
    hasImages: bool
    images: list[str]
    hasVideos: bool
    videos: list[str]
    has3DFile: bool
    owner: ArtworkOwnerPayload
    createdAt: str

@strawberry.type
class ArtworkFormData:
    categories: list[CategoryPayload]
    topics: list[TopicPayload]
    softwares: list[SoftwarePayload]
    publishing: list[PublishingPayload]

@strawberry.type
class ArtworkModelPayload:
    mainFile: str
    resources: list[str]
    settings: ModelSettings