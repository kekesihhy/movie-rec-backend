from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.sql import func
from app.core.database import Base

class User(Base):
    __tablename__ = "users"

    id               = Column(Integer, primary_key=True, autoincrement=True)
    username         = Column(String(100), unique=True, nullable=False)
    email            = Column(String(200), unique=True, nullable=False)
    password_hash    = Column(String(255), nullable=False)
    avatar_url       = Column(String(500), nullable=True)
    preferred_genres = Column(String(500), nullable=True)  # 逗号分隔，如 "Action,Drama"
    created_at       = Column(DateTime, server_default=func.now())
    updated_at       = Column(DateTime, server_default=func.now(), onupdate=func.now())