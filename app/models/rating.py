from sqlalchemy import Column, Integer, Float, TIMESTAMP, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base

class UserRating(Base):
    __tablename__ = "user_ratings"

    user_id  = Column(Integer, ForeignKey("users.id"),  primary_key=True)
    movie_id = Column(Integer, ForeignKey("movies.id"), primary_key=True)
    rating   = Column(Float, nullable=False)
    rated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())

    user  = relationship("User",  backref="ratings")
    movie = relationship("Movie", backref="user_ratings")


class UserFavorite(Base):
    __tablename__ = "user_favorites"

    user_id    = Column(Integer, ForeignKey("users.id"),  primary_key=True)
    movie_id   = Column(Integer, ForeignKey("movies.id"), primary_key=True)
    created_at = Column(TIMESTAMP, server_default=func.now())

    user  = relationship("User",  backref="favorites")
    movie = relationship("Movie", backref="favorited_by")