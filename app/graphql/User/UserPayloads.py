from app.graphql.Category.CategoryPayloads import CategoryPayload
from app.graphql.Topic.TopicPayloads import TopicPayload
from app.graphql.Software.SoftwarePayloads import SoftwarePayload
from app.graphql.User.UserInputs import ProfileInput
import strawberry

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

@strawberry.type
class ProfilePayload:
    message: str
    values: ProfileUpdated