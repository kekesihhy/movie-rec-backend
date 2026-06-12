from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, selectinload
from sqlalchemy import func

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.rating import UserRating, UserFavorite
from app.models.movie import Movie
from app.schemas.rating import (
    RatingCreate, RatingOut, RatingWithMovie,
    FavoriteOut, FavoriteWithMovie, MovieRatingSummary
)

router = APIRouter()

# ── 评分 ──────────────────────────────────────────

@router.post("/movies/{movie_id}", response_model=RatingOut)
def rate_movie(
    movie_id: int,
    data: RatingCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if not db.query(Movie).filter(Movie.id == movie_id).first():
        raise HTTPException(status_code=404, detail="电影不存在")

    existing = db.query(UserRating).filter_by(
        user_id=current_user.id, movie_id=movie_id
    ).first()

    if existing:
        existing.rating = data.rating
        db.commit(); db.refresh(existing)
        return existing
    else:
        rating = UserRating(user_id=current_user.id, movie_id=movie_id, rating=data.rating)
        db.add(rating); db.commit(); db.refresh(rating)
        return rating

@router.delete("/movies/{movie_id}")
def delete_rating(
    movie_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    rating = db.query(UserRating).filter_by(
        user_id=current_user.id, movie_id=movie_id
    ).first()
    if not rating:
        raise HTTPException(status_code=404, detail="评分不存在")
    db.delete(rating); db.commit()
    return {"message": "已删除"}

@router.get("/movies/{movie_id}/mine", response_model=RatingOut)
def get_my_rating(
    movie_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    rating = db.query(UserRating).filter_by(
        user_id=current_user.id, movie_id=movie_id
    ).first()
    if not rating:
        raise HTTPException(status_code=404, detail="未评分")
    return rating

@router.get("/movies/{movie_id}/summary", response_model=MovieRatingSummary)
def get_movie_rating_summary(movie_id: int, db: Session = Depends(get_db)):
    result = db.query(
        func.avg(UserRating.rating).label("avg_rating"),
        func.count(UserRating.rating).label("count")
    ).filter(UserRating.movie_id == movie_id).first()

    return MovieRatingSummary(
        movie_id=movie_id,
        avg_rating=round(float(result.avg_rating or 0), 2),
        count=result.count or 0
    )

@router.get("/me", response_model=list[RatingWithMovie])
def get_my_ratings(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return (db.query(UserRating)
            .options(selectinload(UserRating.movie))
            .filter(UserRating.user_id == current_user.id)
            .order_by(UserRating.rated_at.desc())
            .all())

# ── 收藏 ──────────────────────────────────────────

@router.post("/favorites/{movie_id}", response_model=FavoriteOut)
def add_favorite(
    movie_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if not db.query(Movie).filter(Movie.id == movie_id).first():
        raise HTTPException(status_code=404, detail="电影不存在")

    existing = db.query(UserFavorite).filter_by(
        user_id=current_user.id, movie_id=movie_id
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="已收藏")

    fav = UserFavorite(user_id=current_user.id, movie_id=movie_id)
    db.add(fav); db.commit(); db.refresh(fav)
    return fav

@router.delete("/favorites/{movie_id}")
def remove_favorite(
    movie_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    fav = db.query(UserFavorite).filter_by(
        user_id=current_user.id, movie_id=movie_id
    ).first()
    if not fav:
        raise HTTPException(status_code=404, detail="未收藏")
    db.delete(fav); db.commit()
    return {"message": "已取消收藏"}

@router.get("/favorites/me", response_model=list[FavoriteWithMovie])
def get_my_favorites(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return (db.query(UserFavorite)
            .options(selectinload(UserFavorite.movie))
            .filter(UserFavorite.user_id == current_user.id)
            .order_by(UserFavorite.created_at.desc())
            .all())

@router.get("/favorites/{movie_id}/check")
def check_favorite(
    movie_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    exists = db.query(UserFavorite).filter_by(
        user_id=current_user.id, movie_id=movie_id
    ).first()
    return {"is_favorite": bool(exists)}