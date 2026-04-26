from app.graphql.Category.CategoryPayloads import CategoryPayload
from app.graphql.Topic.TopicPayloads import TopicPayload
from app.graphql.Software.SoftwarePayloads import SoftwarePayload
import strawberry
from typing import Optional

@strawberry.type
class SkillsData:
    categories: list[CategoryPayload]
    topics: list[TopicPayload]
    softwares: list[SoftwarePayload]

@strawberry.type
class ProfileUpdated:
    firstName: str
    lastName: str
    professionalHeadline: str
    summary: str
    countryId: int
    city: str

@strawberry.type
class UserGeneralDataPayload:
    userId: int
    firstName: str
    lastName: str
    username: str
    professionalHeadline: str | None
    summary: str | None
    location: str | None
    city: str | None
    avatar: str | None
    since: str
    chatId: str | None
    cover: Optional[str | None] = None

@strawberry.type
class ProfilePayload:
    message: str
    values: ProfileUpdated

@strawberry.type
class ArtistPayload:
    artistId: int
    username: str
    avatar: str | None
    cover: Optional[str | None] = None

@strawberry.type
class UserStatsPayload:
    followersCount: int
    followingCount: int