from pydantic import BaseModel
from typing import Optional, List
from datetime import date

class GenreOut(BaseModel):
    id:   int
    name: str
    model_config = {"from_attributes": True}

class CompanyOut(BaseModel):
    id:   int
    name: str
    model_config = {"from_attributes": True}

# 列表页用的精简卡片
class MovieCard(BaseModel):
    id:            int
    title:         str
    original_title: Optional[str] = None
    year:          Optional[int]  = None
    vote_average:  Optional[float] = None
    vote_count:    Optional[int]   = None
    popularity:    Optional[float] = None
    poster_url:    Optional[str]   = None
    original_language: Optional[str] = None
    genres:        List[GenreOut]  = []
    model_config = {"from_attributes": True}

# 详情页用的完整数据
class MovieDetail(BaseModel):
    id:               int
    title:            str
    original_title:   Optional[str]   = None
    overview:         Optional[str]   = None
    tagline:          Optional[str]   = None
    release_date:     Optional[date]  = None
    year:             Optional[int]   = None
    runtime:          Optional[int]   = None
    budget:           Optional[int]   = None
    revenue:          Optional[int]   = None
    popularity:       Optional[float] = None
    vote_average:     Optional[float] = None
    vote_count:       Optional[int]   = None
    original_language: Optional[str]  = None
    homepage:         Optional[str]   = None
    poster_url:       Optional[str]   = None
    genres:           List[GenreOut]  = []
    companies:        List[CompanyOut] = []
    model_config = {"from_attributes": True}

# 分页列表响应
class MovieListResponse(BaseModel):
    total:   int
    page:    int
    size:    int
    pages:   int
    items:   List[MovieCard]