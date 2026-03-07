import strawberry
from typing import Optional
from strawberry.file_uploads import Upload
from datetime import date, time

@strawberry.input
class StoreArtworkInput:
    title: Optional[str] = None
    description: Optional[str] = None
    matureContent: Optional[bool] = None
    categories: Optional[list[int]] = None
    topics: Optional[list[int]] = None
    softwares: Optional[list[int]] = None
    images: Optional[list[Upload]] = None,
    videos: Optional[list[Upload]] = None,
    file3d: Optional[str] = None,
    thumbnail: Optional[Upload] = None
    publishing: Optional[int] = None
    schedule: Optional[bool] = None
    publishingTargetStatus: Optional[int] = None
    scheduleDate: Optional[date] = None
    scheduleTime: Optional[time] = None

@strawberry.input
class DeleteUserArtworkInput:
    artworkIds: list[int]