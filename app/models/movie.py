from sqlalchemy import Column, Integer, String, Text, Date, SmallInteger, BigInteger, Float, TIMESTAMP, ForeignKey, Table
from sqlalchemy.orm import relationship
from app.core.database import Base

# 关联表（纯中间表，不需要 ORM 类）
movie_genres_table = Table(
    'movie_genres', Base.metadata,
    Column('movie_id', Integer, ForeignKey('movies.id')),
    Column('genre_id', Integer, ForeignKey('genres.id'))
)

movie_keywords_table = Table(
    'movie_keywords', Base.metadata,
    Column('movie_id', Integer, ForeignKey('movies.id')),
    Column('keyword_id', Integer, ForeignKey('keywords.id'))
)

movie_companies_table = Table(
    'movie_companies', Base.metadata,
    Column('movie_id', Integer, ForeignKey('movies.id')),
    Column('company_id', Integer, ForeignKey('companies.id'))
)

class Genre(Base):
    __tablename__ = "genres"
    id   = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)

class Keyword(Base):
    __tablename__ = "keywords"
    id   = Column(Integer, primary_key=True)
    name = Column(String(300), nullable=False)

class Company(Base):
    __tablename__ = "companies"
    id   = Column(Integer, primary_key=True)
    name = Column(String(300), nullable=False)

class Movie(Base):
    __tablename__ = "movies"

    id                = Column(Integer, primary_key=True)
    title             = Column(String(255), nullable=False)
    original_title    = Column(String(255))
    overview          = Column(Text)
    tagline           = Column(String(1000))
    release_date      = Column(Date)
    year              = Column(SmallInteger)
    runtime           = Column(SmallInteger)
    budget            = Column(BigInteger)
    revenue           = Column(BigInteger)
    popularity        = Column(Float)
    vote_average      = Column(Float)
    vote_count        = Column(Integer)
    status            = Column(String(50))
    original_language = Column(String(10))
    homepage          = Column(String(1000))
    poster_url        = Column(String(500))
    created_at        = Column(TIMESTAMP)

    genres    = relationship("Genre",   secondary=movie_genres_table)
    keywords  = relationship("Keyword", secondary=movie_keywords_table)
    companies = relationship("Company", secondary=movie_companies_table)