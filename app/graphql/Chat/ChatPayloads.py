import strawberry

@strawberry.type
class ChatMessagePayload:
    chatId: str
    messageId: str
    userId: int
    typeMessage: str
    message: str
    createdAt: str
    date: str

@strawberry.type
class SingleChatPayload:
    messages: list[ChatMessagePayload]
    hasMore: bool

@strawberry.type
class SetChatPayload:
    chatId: str

@strawberry.type
class LastMessagePayload:
    userId: int
    message: str
    date: str
    time: str

@strawberry.type
class ArtistPayload:
    artistId: int
    username: str
    avatar: str | None

@strawberry.type
class ChatsPayload:
    chatId: str
    artist: ArtistPayload
    lastMessage: LastMessagePayload
    isFollowing: bool
    isBlocked: bool
    hasBlockedMe: bool