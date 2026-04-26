from app.config.logger import logger
from sqlalchemy import insert, and_, asc, func, desc, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from app.models.Notifications.Notifications import Notification
from typing import Any
from sqlalchemy.future import select
from app.graphql.Notifications.NotificationPayloads import NotificationPayload

class NotificationService:
    def __init__(self, db: AsyncSession):
        self.db = db
        
    async def store(self, emitterId: int, receipterId: int, type: str, entity: str, entityId: int, title: str, description: str, image: str | None, ip: str, terminal: Any):
        try:
            notification = Notification(
                emitter_id=emitterId,
                receipter_id=receipterId,
                type=type,
                entity=entity,
                entity_id=entityId,
                title=title,
                description=description,
                image=image,
                ip=ip,
                terminal=terminal 
            )

            self.db.add(notification)
            await self.db.flush()

            return {"ok": True, "message": "Notification Saved Successfully", "code": 201, "data": notification}

        except Exception as e:
            logger.error(e)
            error_mapping = {
                IntegrityError: (400, "Database integrity error"),
                SQLAlchemyError: (500, "Database error"),
                ValueError: (400, "Invalid input data"),
                PermissionError: (401, "Unauthorized access"),
                FileNotFoundError: (404, "Resource not found"),
                ConnectionError: (429, "Too many requests"),
            }

            error_code, error_message = error_mapping.get(type(e), (500, "Internal server error"))
            return {"ok": False, "error": error_message, "code": error_code}
    
    async def bulk_store(self, notifications: list):
        try:
            stmt = (
                insert(Notification)
                .returning(
                    Notification.notification_id,
                    Notification.receipter_id
                )
            )

            result = await self.db.execute(stmt, notifications)
            rows = result.fetchall()

            data = [
                {
                    "notification_id": row.notification_id,
                    "receipter_id": row.receipter_id
                }
                for row in rows
            ]

            return {"ok": True, "message": "Bulk Notifications Created", "code": 201, "data": data}

        except Exception as e:
            logger.error(e)
            error_mapping = {
                IntegrityError: (400, "Database integrity error"),
                SQLAlchemyError: (500, "Database error"),
                ValueError: (400, "Invalid input data"),
                PermissionError: (401, "Unauthorized access"),
                FileNotFoundError: (404, "Resource not found"),
                ConnectionError: (429, "Too many requests"),
            }

            error_code, error_message = error_mapping.get(type(e), (500, "Internal server error"))
            return {"ok": False, "error": error_message, "code": error_code}
        
    async def getUserNotifications(self, userId: int, page: int = 1, size: int = 10):
        try:
            skip = (page - 1) * size

            count_query = await self.db.execute(
                select(func.count(Notification.notification_id))
                .where(and_(Notification.status == "A", Notification.receipter_id == userId))
            )
            total_count = count_query.scalar()

            result = await self.db.execute(
                select(
                    Notification.notification_id,
                    Notification.type,
                    Notification.entity_id,
                    Notification.title,
                    Notification.description,
                    Notification.is_read,
                    Notification.image
                )
                .select_from(Notification)
                .where(and_(Notification.status == "A", Notification.receipter_id == userId))
                .order_by(asc(Notification.is_read), desc(Notification.notification_id))
                .limit(size)
                .offset(skip)
            )

            rows = result.mappings().all()

            has_more = total_count > (page * size)

            notifications = [
                NotificationPayload(
                    notificationId=notification['notification_id'],
                    type=notification['type'],
                    entityId=notification['entity_id'],
                    title=notification['title'],
                    description=notification['description'],
                    isRead=notification['is_read'],
                    image=notification['image'],
                ) for notification in rows
            ]

            data = {
                "notifications": notifications,
                "hasMore": has_more,
                "totalCount": total_count
            }

            return {"ok": True, "message": "User Notifications Got", "code": 201, "data": data}
        except Exception as e:
            logger.error(e)
            error_mapping = {
                IntegrityError: (400, "Database integrity error"),
                SQLAlchemyError: (500, "Database error"),
                ValueError: (400, "Invalid input data"),
                PermissionError: (401, "Unauthorized access"),
                FileNotFoundError: (404, "Resource not found"),
                ConnectionError: (429, "Too many requests"),
            }

            error_code, error_message = error_mapping.get(type(e), (500, "Internal server error"))
            return {"ok": False, "error": error_message, "code": error_code}
        
    async def getUserUnreadNotifications(self, userId: int):
        try:
            result = await self.db.execute(
                select(func.count(Notification.notification_id))
                .where(
                    and_(
                        Notification.status == "A", 
                        Notification.receipter_id == userId, 
                        Notification.is_read == False
                    )
                )
            )

            unread_count = result.scalar() or 0

            return {"ok": True, "message": "User Unread Notifications Got", "code": 201, "data": unread_count}
        except Exception as e:
            logger.error(e)
            error_mapping = {
                IntegrityError: (400, "Database integrity error"),
                SQLAlchemyError: (500, "Database error"),
                ValueError: (400, "Invalid input data"),
                PermissionError: (401, "Unauthorized access"),
                FileNotFoundError: (404, "Resource not found"),
                ConnectionError: (429, "Too many requests"),
            }

            error_code, error_message = error_mapping.get(type(e), (500, "Internal server error"))
            return {"ok": False, "error": error_message, "code": error_code}
        
    async def markAllAsRead(self, userId: int):
        try:
            await self.db.execute(
                update(Notification)
                .where(and_(Notification.receipter_id == userId, Notification.status == 'A'))
                .values(is_read=True)
            )

            await self.db.flush()

            return {"ok": True, "message": "All User Notifications Mark as Read", "code": 201, "data": None}
        except Exception as e:
            logger.error(e)
            error_mapping = {
                IntegrityError: (400, "Database integrity error"),
                SQLAlchemyError: (500, "Database error"),
                ValueError: (400, "Invalid input data"),
                PermissionError: (401, "Unauthorized access"),
                FileNotFoundError: (404, "Resource not found"),
                ConnectionError: (429, "Too many requests"),
            }

            error_code, error_message = error_mapping.get(type(e), (500, "Internal server error"))
            return {"ok": False, "error": error_message, "code": error_code}
        
    async def markNotificationAsRead(self, notificationId: int, userId = int):
        try:
            await self.db.execute(
                update(Notification)
                .where(and_(Notification.notification_id == notificationId, Notification.receipter_id == userId, Notification.status == 'A'))
                .values(is_read=True)
            )

            await self.db.flush()

            return {"ok": True, "message": "Notification Mark as Read", "code": 201, "data": None}
        except Exception as e:
            logger.error(e)
            error_mapping = {
                IntegrityError: (400, "Database integrity error"),
                SQLAlchemyError: (500, "Database error"),
                ValueError: (400, "Invalid input data"),
                PermissionError: (401, "Unauthorized access"),
                FileNotFoundError: (404, "Resource not found"),
                ConnectionError: (429, "Too many requests"),
            }

            error_code, error_message = error_mapping.get(type(e), (500, "Internal server error"))
            return {"ok": False, "error": error_message, "code": error_code}
        
    async def updateNotificationImage(self, entityId: int, entity: str, image: str):
        try:
            await self.db.execute(
                update(Notification)
                .where(and_(Notification.entity_id == entityId, Notification.entity == entity, Notification.status == 'A'))
                .values(image=image)
            )

            await self.db.flush()

            return {"ok": True, "message": "Notification Image Updated", "code": 201, "data": None}
        except Exception as e:
            logger.error(e)
            error_mapping = {
                IntegrityError: (400, "Database integrity error"),
                SQLAlchemyError: (500, "Database error"),
                ValueError: (400, "Invalid input data"),
                PermissionError: (401, "Unauthorized access"),
                FileNotFoundError: (404, "Resource not found"),
                ConnectionError: (429, "Too many requests"),
            }

            error_code, error_message = error_mapping.get(type(e), (500, "Internal server error"))
            return {"ok": False, "error": error_message, "code": error_code}