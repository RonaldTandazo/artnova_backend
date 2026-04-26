import strawberry
from typing import Optional

@strawberry.input
class FollowStateInput:
    followedId: int
    simple: Optional[bool] = True