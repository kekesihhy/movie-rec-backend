import math
from typing import Optional
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session, selectinload
from sqlalchemy import or_

from app.core.database import get_db
from app.models.movie import Movie, Genre
from app.schemas.movie import MovieCard, MovieDetail, MovieListResponse, GenreOut

router = APIRouter()

# ⚠️ 注意：/popular /top-rated /search /genres 必须在 /{movie_id} 之前，否则会被当成 id

@router.get("/popular", response_model=list[MovieCard])
def get_popular(
    limit: int = Query(20, le=100),
    db: Session = Depends(get_db)
):
    movies = (db.query(Movie)
              .options(selectinload(Movie.genres))
              .filter(Movie.vote_count > 100)
              .order_by(Movie.popularity.desc())
              .limit(limit).all())
    return movies

@router.get("/top-rated", response_model=list[MovieCard])
def get_top_rated(
    limit: int = Query(20, le=100),
    db: Session = Depends(get_db)
):
    movies = (db.query(Movie)
              .options(selectinload(Movie.genres))
              .filter(Movie.vote_count > 100)
              .order_by(Movie.vote_average.desc())
              .limit(limit).all())
    return movies

@router.get("/search", response_model=MovieListResponse)
def search_movies(
    q: str = Query(..., min_length=1),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    kw = f"%{q}%"
    query = (db.query(Movie)
             .options(selectinload(Movie.genres))
             .filter(or_(
                 Movie.title.ilike(kw),
                 Movie.original_title.ilike(kw),
                 Movie.overview.ilike(kw)
             )))
    total = query.count()
    items = (query.order_by(Movie.popularity.desc())
             .offset((page - 1) * size).limit(size).all())
    return MovieListResponse(
        total=total, page=page, size=size,
        pages=math.ceil(total / size) if total else 0,
        items=items
    )

@router.get("/genres", response_model=list[GenreOut])
def get_all_genres(db: Session = Depends(get_db)):
    return db.query(Genre).order_by(Genre.name).all()

@router.get("", response_model=MovieListResponse)
def list_movies(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    genre: Optional[str] = None,
    year: Optional[int] = None,
    min_rating: Optional[float] = None,
    max_rating: Optional[float] = None,
    language: Optional[str] = None,
    sort_by: str = Query("popularity"),
    db: Session = Depends(get_db)
):
    query = db.query(Movie).options(selectinload(Movie.genres))

    if genre:
        query = query.join(Movie.genres).filter(Genre.name == genre)
    if year:
        query = query.filter(Movie.year == year)
    if min_rating is not None:
        query = query.filter(Movie.vote_average >= min_rating)
    if max_rating is not None:
        query = query.filter(Movie.vote_average <= max_rating)
    if language:
        query = query.filter(Movie.original_language == language)

    # 排序
    order_col = {
        "vote_average": Movie.vote_average,
        "year":         Movie.year,
        "vote_count":   Movie.vote_count,
    }.get(sort_by, Movie.popularity)
    query = query.order_by(order_col.desc())

    total = query.count()
    items = query.offset((page - 1) * size).limit(size).all()
    return MovieListResponse(
        total=total, page=page, size=size,
        pages=math.ceil(total / size) if total else 0,
        items=items
    )

@router.get("/{movie_id}", response_model=MovieDetail)
def get_movie(movie_id: int, db: Session = Depends(get_db)):
    movie = (db.query(Movie)
             .options(selectinload(Movie.genres), selectinload(Movie.companies))
             .filter(Movie.id == movie_id)
             .first())
    if not movie:
        raise HTTPException(status_code=404, detail="电影不存在")
    return movie