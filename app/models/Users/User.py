from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from passlib.context import CryptContext
from app.models.base import Base, AuditBase

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class User(AuditBase, Base):
    __tablename__ = "users"

    user_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    first_name = Column(String(50), nullable=False)
    last_name = Column(String(50), nullable=False)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(50), unique=True, index=True, nullable=False)
    password = Column(String(255), nullable=False)
    professional_headline = Column(String(255), nullable=True)
    summary = Column(String(255), nullable=True)
    city = Column(String(50), nullable=True)
    country_id = Column(Integer, ForeignKey("countries.country_id"), nullable=True)
    avatar = Column(String(50), nullable=True)
    cover = Column(String(50), nullable=True)

    country = relationship(
        "Country",
        primaryjoin="and_(User.country_id == Country.country_id, Country.status == 'A')"
    )

    artwork_owner = relationship(
        "ArtworkOwner",
        back_populates="user",
        primaryjoin="and_(User.user_id == ArtworkOwner.user_id, ArtworkOwner.status == 'A')",
        uselist=True
    )

    artwork_user_favorites = relationship(
        "ArtworkUserFavorite",
        back_populates="user",
        primaryjoin="and_(User.user_id == ArtworkUserFavorite.user_id, ArtworkUserFavorite.status == 'A')",
        uselist=True
    )

    @classmethod
    def verifyPassword(cls, plain_password, hashed_password):
        return pwd_context.verify(plain_password, hashed_password)

    @classmethod
    def hashPassword(cls, password):
        return pwd_context.hash(password)
