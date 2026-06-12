from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.services import analytics_service as svc

router = APIRouter()

@router.get("/genre-distribution")
def genre_distribution(db: Session = Depends(get_db)):
    return svc.genre_distribution(db)

@router.get("/top-keywords")
def top_keywords(db: Session = Depends(get_db)):
    return svc.top_keywords(db)

@router.get("/top-budget")
def top_budget(db: Session = Depends(get_db)):
    return svc.top_budget_movies(db)

@router.get("/runtime-distribution")
def runtime_distribution(db: Session = Depends(get_db)):
    return svc.runtime_distribution(db)

@router.get("/top-companies")
def top_companies(db: Session = Depends(get_db)):
    return svc.top_companies(db)

@router.get("/language-distribution")
def language_distribution(db: Session = Depends(get_db)):
    return svc.language_distribution(db)

@router.get("/budget-vs-rating")
def budget_vs_rating(db: Session = Depends(get_db)):
    return svc.budget_vs_rating(db)

@router.get("/year-vs-rating")
def year_vs_rating(db: Session = Depends(get_db)):
    return svc.year_vs_rating(db)

@router.get("/popularity-vs-rating")
def popularity_vs_rating(db: Session = Depends(get_db)):
    return svc.popularity_vs_rating(db)

@router.get("/company-output-vs-rating")
def company_output_vs_rating(db: Session = Depends(get_db)):
    return svc.company_output_vs_rating(db)

@router.get("/budget-vs-revenue")
def budget_vs_revenue(db: Session = Depends(get_db)):
    return svc.budget_vs_revenue(db)

@router.get("/stats")
def stats(db: Session = Depends(get_db)):
    from sqlalchemy import func
    from app.models.movie import Movie
    total = db.query(func.count(Movie.id)).scalar()
    avg_r = db.query(func.avg(Movie.vote_average)).filter(Movie.vote_count > 10).scalar()
    avg_t = db.query(func.avg(Movie.runtime)).filter(Movie.runtime > 0).scalar()
    min_y = db.query(func.min(Movie.year)).filter(Movie.year > 0).scalar()
    max_y = db.query(func.max(Movie.year)).scalar()
    return {
        "total": total,
        "avg_rating": round(float(avg_r or 0), 2),
        "avg_runtime": round(float(avg_t or 0)),
        "year_min": min_y, "year_max": max_y
    }

@router.get("/rating-distribution")
def rating_distribution(db: Session = Depends(get_db)):
    return svc.rating_distribution(db)

@router.get("/genre-by-decade")
def genre_by_decade(db: Session = Depends(get_db)):
    return svc.genre_by_decade(db)

@router.get("/genre-avg-rating")
def genre_avg_rating(db: Session = Depends(get_db)):
    return svc.genre_avg_rating(db)