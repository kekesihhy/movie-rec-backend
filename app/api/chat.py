from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, selectinload
from sqlalchemy import or_
from pydantic import BaseModel
from typing import Optional

from app.core.database import get_db
from app.core.security import get_current_user_optional
from app.models.user import User
from app.models.movie import Movie
from app.models.rating import UserRating
from app.services.chat_service import chat_completion

router = APIRouter()

class ChatMessage(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    messages: list[ChatMessage]

@router.post("/")
def chat(
    req: ChatRequest,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    if not req.messages:
        raise HTTPException(status_code=400, detail="消息不能为空")

    # 1. 用户上下文
    user_context = ""
    if current_user:
        ratings = (db.query(UserRating)
                   .filter(UserRating.user_id == current_user.id)
                   .order_by(UserRating.rating.desc())
                   .limit(5).all())
        if ratings:
            ids = [str(r.movie_id) for r in ratings]
            user_context = f"用户：{current_user.username}，高分评价过的电影ID：{', '.join(ids)}"
        else:
            user_context = f"用户：{current_user.username}，暂无评分记录"

    # 2. 数据库检索注入：搜索用户最后一条消息相关的电影
    last_msg = req.messages[-1].content if req.messages else ""
    if len(last_msg) >= 2:
        keyword = last_msg[:30]
        results = (db.query(Movie)
                   .options(selectinload(Movie.genres))
                   .filter(or_(
                       Movie.title.ilike(f"%{keyword}%"),
                       Movie.original_title.ilike(f"%{keyword}%"),
                       Movie.overview.ilike(f"%{keyword}%")
                   ))
                   .limit(3).all())
        if results:
            lines = []
            for m in results:
                genres = "、".join(g.name for g in m.genres[:3])
                lines.append(
                    f"《{m.title}》({m.year}) 评分{m.vote_average} 类型:{genres} 简介:{(m.overview or '')[:80]}"
                )
            db_context = "数据库中找到相关电影：\n" + "\n".join(lines)
            user_context = (user_context + "\n" + db_context).strip() if user_context else db_context

    try:
        reply = chat_completion(
            [{"role": m.role, "content": m.content} for m in req.messages],
            user_context
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI 服务调用失败: {str(e)}")

    return {"reply": reply}