from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models.movie import (Movie, Genre, Keyword, Company,
                               movie_genres_table, movie_keywords_table,
                               movie_companies_table)

def genre_distribution(db: Session):
    rows = (db.query(Genre.name, func.count(movie_genres_table.c.movie_id).label('n'))
            .join(movie_genres_table, Genre.id == movie_genres_table.c.genre_id)
            .group_by(Genre.id, Genre.name)
            .order_by(func.count(movie_genres_table.c.movie_id).desc()).all())
    return [{"name": r.name, "value": r.n} for r in rows]

def top_keywords(db: Session, n: int = 100):
    rows = (db.query(Keyword.name, func.count(movie_keywords_table.c.movie_id).label('n'))
            .join(movie_keywords_table, Keyword.id == movie_keywords_table.c.keyword_id)
            .group_by(Keyword.id, Keyword.name)
            .order_by(func.count(movie_keywords_table.c.movie_id).desc())
            .limit(n).all())
    return [{"name": r.name, "value": r.n} for r in rows]

def top_budget_movies(db: Session, n: int = 10):
    rows = (db.query(Movie.title, Movie.budget, Movie.year)
            .filter(Movie.budget.isnot(None), Movie.budget > 0)
            .order_by(Movie.budget.desc()).limit(n).all())
    return [{"title": r.title, "budget": round(r.budget / 1e6, 1), "year": r.year} for r in rows]

def runtime_distribution(db: Session):
    rows = db.query(Movie.runtime).filter(Movie.runtime > 0, Movie.runtime < 300).all()
    buckets = [("< 90", 0, 90), ("90-120", 90, 120),
               ("120-150", 120, 150), ("150-180", 150, 180), ("> 180", 180, 999)]
    rts = [r.runtime for r in rows]
    return [{"range": label, "count": sum(1 for x in rts if lo <= x < hi)}
            for label, lo, hi in buckets]

def top_companies(db: Session, n: int = 10):
    rows = (db.query(Company.name, func.count(movie_companies_table.c.movie_id).label('n'))
            .join(movie_companies_table, Company.id == movie_companies_table.c.company_id)
            .group_by(Company.id, Company.name)
            .order_by(func.count(movie_companies_table.c.movie_id).desc())
            .limit(n).all())
    return [{"name": r.name, "count": r.n} for r in rows]

def language_distribution(db: Session, n: int = 10):
    rows = (db.query(Movie.original_language, func.count(Movie.id).label('n'))
            .filter(Movie.original_language.isnot(None))
            .group_by(Movie.original_language)
            .order_by(func.count(Movie.id).desc()).limit(n).all())
    return [{"language": r.original_language, "count": r.n} for r in rows]

def budget_vs_rating(db: Session):
    rows = (db.query(Movie.title, Movie.budget, Movie.vote_average)
            .filter(Movie.budget.isnot(None), Movie.budget > 0, Movie.vote_average > 0)
            .limit(500).all())
    return [{"title": r.title, "x": round(r.budget / 1e6, 1), "y": r.vote_average} for r in rows]

def year_vs_rating(db: Session):
    rows = (db.query(Movie.year,
                     func.avg(Movie.vote_average).label('avg'),
                     func.count(Movie.id).label('n'))
            .filter(Movie.year > 1950, Movie.year <= 2016, Movie.vote_count > 10)
            .group_by(Movie.year).order_by(Movie.year).all())
    return [{"year": r.year, "avg_rating": round(float(r.avg), 2), "count": r.n} for r in rows]

def popularity_vs_rating(db: Session):
    rows = (db.query(Movie.title, Movie.popularity, Movie.vote_average)
            .filter(Movie.popularity > 0, Movie.vote_average > 0, Movie.vote_count > 100)
            .order_by(Movie.popularity.desc()).limit(300).all())
    return [{"title": r.title, "x": round(r.popularity, 2), "y": r.vote_average} for r in rows]

def company_output_vs_rating(db: Session):
    rows = (db.query(Company.name,
                     func.count(movie_companies_table.c.movie_id).label('cnt'),
                     func.avg(Movie.vote_average).label('avg'))
            .join(movie_companies_table, Company.id == movie_companies_table.c.company_id)
            .join(Movie, Movie.id == movie_companies_table.c.movie_id)
            .group_by(Company.id, Company.name)
            .having(func.count(movie_companies_table.c.movie_id) >= 5).all())
    return [{"name": r.name, "x": r.cnt, "y": round(float(r.avg), 2)} for r in rows]

def budget_vs_revenue(db: Session):
    rows = (db.query(Movie.title, Movie.budget, Movie.revenue, Movie.vote_average)
            .filter(Movie.budget.isnot(None), Movie.revenue.isnot(None),
                    Movie.budget > 0, Movie.revenue > 0).limit(400).all())
    return [{"title": r.title,
             "x": round(r.budget / 1e6, 1),
             "y": round(r.revenue / 1e6, 1),
             "score": r.vote_average} for r in rows]

def rating_distribution(db: Session):
    rows = db.query(Movie.vote_average).filter(Movie.vote_count > 10, Movie.vote_average > 0).all()
    buckets = [(f"{i/2}-{(i+1)/2}", i/2, (i+1)/2) for i in range(0, 20)]
    scores = [r.vote_average for r in rows]
    return [{"range": label, "count": sum(1 for s in scores if lo <= s < hi)}
            for label, lo, hi in buckets if sum(1 for s in scores if lo <= s < hi) > 0]

def genre_by_decade(db: Session):
    TOP_GENRES = ['Drama','Comedy','Action','Thriller','Romance','Adventure','Crime','Science Fiction']
    rows = (db.query(Movie.year, Genre.name)
            .join(movie_genres_table, Movie.id == movie_genres_table.c.movie_id)
            .join(Genre, Genre.id == movie_genres_table.c.genre_id)
            .filter(Movie.year >= 1960, Movie.year <= 2016, Genre.name.in_(TOP_GENRES))
            .all())
    decades = sorted(set((r.year // 10) * 10 for r in rows))
    data = {g: {d: 0 for d in decades} for g in TOP_GENRES}
    for r in rows:
        d = (r.year // 10) * 10
        data[r.name][d] += 1
    return {
        "decades": [f"{d}s" for d in decades],
        "series": [{"name": g, "data": [data[g][d] for d in decades]} for g in TOP_GENRES]
    }

def genre_avg_rating(db: Session):
    rows = (db.query(Genre.name,
                     func.avg(Movie.vote_average).label('avg'),
                     func.count(Movie.id).label('cnt'))
            .join(movie_genres_table, Genre.id == movie_genres_table.c.genre_id)
            .join(Movie, Movie.id == movie_genres_table.c.movie_id)
            .filter(Movie.vote_count > 50)
            .group_by(Genre.id, Genre.name)
            .having(func.count(Movie.id) >= 20)
            .order_by(func.avg(Movie.vote_average).desc()).all())
    return [{"name": r.name, "avg": round(float(r.avg), 2), "count": r.cnt} for r in rows]