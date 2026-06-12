from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from app.schemas.movie import MovieCard

class RatingCreate(BaseModel):
    rating: float = Field(..., ge=1.0, le=5.0)

class RatingOut(BaseModel):
    user_id:  int
    movie_id: int
    rating:   float
    rated_at: Optional[datetime] = None
    model_config = {"from_attributes": True}

class RatingWithMovie(BaseModel):
    movie_id: int
    rating:   float
    rated_at: Optional[datetime] = None
    movie:    Optional[MovieCard] = None
    model_config = {"from_attributes": True}

class FavoriteOut(BaseModel):
    user_id:    int
    movie_id:   int
    created_at: Optional[datetime] = None
    model_config = {"from_attributes": True}

class FavoriteWithMovie(BaseModel):
    movie_id:   int
    created_at: Optional[datetime] = None
    movie:      Optional[MovieCard] = None
    model_config = {"from_attributes": True}

class MovieRatingSummary(BaseModel):
    movie_id:   int
    avg_rating: float
    count:      int