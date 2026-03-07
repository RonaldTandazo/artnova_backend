import strawberry

@strawberry.input
class PostCommentInput:
    artworkId: int
    avatar: str | None
    comment: str

@strawberry.input
class DeleteCommentInput:
    artworkId: int
    commentIds: list[str]

@strawberry.input
class UpdateArtworkLikesInput:
    artworkId: int
    likes: list[int]

@strawberry.input
class UpdateArtworkDisLikesInput:
    artworkId: int
    dislikes: list[int]

@strawberry.input
class UpdateArtworkFavoritesInput:
    artworkId: int
    favorites: list[int]
    
@strawberry.input
class UpdateCommentLikesInput:
    artworkId: int
    commentId: str
    likes: list[int]

@strawberry.input
class UpdateCommentDisLikesInput:
    artworkId: int
    commentId: str
    dislikes: list[int]
