import strawberry

@strawberry.type
class FollowStatePayload:
    isFollowed: bool