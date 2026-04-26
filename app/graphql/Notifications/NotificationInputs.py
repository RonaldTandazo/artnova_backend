import strawberry

@strawberry.input
class UserNotificationsInput:
    page: int

@strawberry.input
class MarkNotificationAsReadInput:
    notificationId: int