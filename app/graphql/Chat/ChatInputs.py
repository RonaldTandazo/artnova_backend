import strawberry

@strawberry.input
class MessageInput:
    chatId: str | None
    messageId: str | None
    userId: int
    typeMessage: str
    message: str
    createdAt: str
    date: str

@strawberry.input
class SetChatInput:
    chatId: str | None
    artistId: int
    message: MessageInput

@strawberry.input
class DeleteChatInput:
    chatId: str