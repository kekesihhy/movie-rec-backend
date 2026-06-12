from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api import auth, movies, ratings, recommend, analytics, chat

# app = FastAPI(title="电影推荐系统 API", version="1.0.0")
app = FastAPI(title="电影推荐系统 API", version="1.0.0", debug=True)

import traceback as tb
from fastapi import Request
from fastapi.responses import JSONResponse

@app.exception_handler(Exception)
async def catch_all(request: Request, exc: Exception):
    return JSONResponse(status_code=500, content={
        "error": type(exc).__name__,
        "message": str(exc),
        "traceback": tb.format_exc()
    })

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS_LIST,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router,      prefix="/api/auth",      tags=["用户认证"])
app.include_router(movies.router,    prefix="/api/movies",    tags=["电影"])
app.include_router(ratings.router,   prefix="/api/ratings",   tags=["评分收藏"])
app.include_router(recommend.router, prefix="/api/recommend", tags=["推荐"])
app.include_router(analytics.router, prefix="/api/analytics", tags=["数据分析"])
app.include_router(chat.router,      prefix="/api/chat",      tags=["智能问答"])

@app.get("/health")
def health():
    return {"status": "ok"}