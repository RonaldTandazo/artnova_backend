import strawberry

@strawberry.type
class NotificationPayload:
    notificationId: int
    type: str
    entityId: int
    title: str
    description: str
    isRead: bool
    image: str | None

@strawberry.type
class UserNotifications:
    notifications: list[NotificationPayload]
    unreadNotifications: int
    hasMore: bool