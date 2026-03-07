import strawberry

@strawberry.type
class UserSoftwarePayload:
    userId: int
    softwareId: int
    name: str

@strawberry.type
class UserCategoryPayload:
    userId: int
    categoryId: int
    name: str

@strawberry.type
class UserTopicPayload:
    userId: int
    topicId: int
    name: str

@strawberry.type
class UserSkillsPayload:
    userTopics: list[UserTopicPayload]
    userSoftwares: list[UserSoftwarePayload]
    userCategories: list[UserCategoryPayload]