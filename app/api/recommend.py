from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session, selectinload

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.movie import Movie
from app.schemas.movie import MovieCard
from app.services.recommend_service import content_recommend, hybrid_recommend

router = APIRouter()

def _fetch_movies(ids: list[int], db: Session) -> list[MovieCard]:
    if not ids:
        return []
    movies = (db.query(Movie)
              .options(selectinload(Movie.genres))
              .filter(Movie.id.in_(ids))
              .all())
    # 保持推荐顺序
    order = {mid: i for i, mid in enumerate(ids)}
    return sorted(movies, key=lambda m: order.get(m.id, 999))

# 相似电影（详情页调用，不需要登录）
@router.get("/similar/{movie_id}", response_model=list[MovieCard])
def similar_movies(
    movie_id: int,
    n: int = Query(10, le=30),
    db: Session = Depends(get_db)
):
    ids = content_recommend(movie_id, n=n)
    return _fetch_movies(ids, db)

# 个性化推荐（需要登录）
@router.get("/for-me", response_model=list[MovieCard])
def recommend_for_me(
    n: int = Query(20, le=50),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    ids = hybrid_recommend(current_user.id, db, n=n)
    return _fetch_movies(ids, db)