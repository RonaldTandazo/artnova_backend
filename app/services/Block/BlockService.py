from app.config.logger import logger
from sqlalchemy import and_, delete
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from app.models.Blocks.Block import Block
from typing import Any

class BlockService:
    def __init__(self, db: AsyncSession):
        self.db = db
        
    async def verifyBlock(self, blockerId: int, blockedId: int):
        try:
            result = await self.db.execute(
                select(Block.block_id)
                .where(and_(
                    Block.status == "A", 
                    Block.blocked_id == blockedId, 
                    Block.blocker_id == blockerId
                ))
                .limit(1)
            )

            block_id = result.scalars().first()

            block_exists = block_id is not None

            response ={"exists": block_exists, "block_id": block_id}

            return {"ok": True, "message": "Block Verified", "code": 200, "data": response}
        except Exception as e:
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
        
    async def setBlock(self, blockerId: int, blockedId: int, ip: str, terminal: Any):
        try:
            block = Block(
                blocker_id=blockerId,
                blocked_id=blockedId,
                ip=ip,
                terminal=terminal 
            )

            self.db.add(block)
            await self.db.flush()

            return {"ok": True, "message": "User Successfully Blocked", "code": 200, "data": block}
        except Exception as e:
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
        
    async def unsetBlock(self, blockId: int):
        try:
            await self.db.execute(
                delete(Block).where(Block.block_id == blockId)
            )
            await self.db.flush()

            return {"ok": True, "message": "User Successfully Unblocked", "code": 200, "data": None}
        except Exception as e:
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