import strawberry

@strawberry.type
class ArtworkStatisticsPayload:
    stats: 'ArtworkStatsPayload'
    comments: list['ArtworkCommentPayload']

@strawberry.type
class ArtworkStatsPayload:
    viewsAmount: int
    likes: list[int]
    dislikes: list[int]
    favorites: list[int]
    commentsAmount: int

@strawberry.type
class ArtworkCommentPayload:
    commentId: str
    userId: int
    username: str
    avatar: str | None = None
    comment: str
    likes: list[int]
    dislikes: list[int]
    replies: list['ArtworkCommentPayload']
    createdAt: str