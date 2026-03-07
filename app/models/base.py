import datetime
from sqlalchemy import Column, String, DateTime
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.declarative import declarative_base, declared_attr


Base = declarative_base()

class AuditBase:
    __abstract__ = True

    @declared_attr
    def status(cls):
        return Column(String(3), default="A", nullable=False)

    @declared_attr
    def ip(cls):
        return Column(String(20), nullable=False)
    
    @declared_attr
    def terminal(cls):
        return Column(JSONB, nullable=False)

    @declared_attr
    def created_at(cls):
        return Column(DateTime, default=datetime.datetime.now, nullable=False)
    
    @declared_attr
    def updated_at(cls):
        return Column(DateTime, onupdate=datetime.datetime.now, nullable=True)