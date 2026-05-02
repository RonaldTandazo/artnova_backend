import strawberry
from typing import Optional
from strawberry.file_uploads import Upload
from datetime import datetime

@strawberry.input
class ModelSettingsInput:
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

@strawberry.input
class StoreArtworkInput:
    title: Optional[str] = None
    description: Optional[str] = None
    matureContent: Optional[bool] = None
    categories: Optional[list[int]] = None
    topics: Optional[list[int]] = None
    softwares: Optional[list[int]] = None
    images: Optional[list[Upload]] = None
    videos: Optional[list[Upload]] = None
    modelMainFile: Optional[Upload] = None
    modelResources: Optional[list[Upload]] = None
    modelSettings: Optional[ModelSettingsInput] = None
    thumbnail: Optional[Upload] = None
    publishing: Optional[int] = None
    schedule: Optional[bool] = None
    publishingTargetStatus: Optional[int] = None
    scheduleAt: Optional[datetime] = None

@strawberry.input
class DeleteUserArtworkInput:
    artworkIds: list[int]