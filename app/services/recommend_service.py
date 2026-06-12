import os, pickle
import numpy as np
from typing import List
from sqlalchemy.orm import Session

# 矩阵文件路径
_CACHE = os.path.join(os.path.dirname(__file__), '..', '..', 'cache', 'tfidf_matrix.pkl')

_data = None

def _load():
    global _data
    if _data is None:
        with open(_CACHE, 'rb') as f:
            _data = pickle.load(f)
    return _data

# ── 基于内容的推荐（TF-IDF 相似度）──────────────────
def content_recommend(movie_id: int, n: int = 10, exclude: set = None) -> List[int]:
    d = _load()
    if movie_id not in d['id_to_index']:
        return []

    idx     = d['id_to_index'][movie_id]
    sim_row = d['similarity'][idx]
    order   = np.argsort(sim_row)[::-1]

    result = []
    for i in order:
        mid = d['movie_ids'][i]
        if mid == movie_id:
            continue
        if exclude and mid in exclude:
            continue
        result.append(mid)
        if len(result) >= n:
            break
    return result

# ── 基于协同过滤的推荐（UserCF）────────────────────
def usercf_recommend(user_id: int, db: Session, n: int = 10) -> List[int]:
    from sklearn.metrics.pairwise import cosine_similarity
    from app.models.rating import UserRating

    rows = db.query(UserRating).all()
    if not rows:
        return []

    users  = list({r.user_id  for r in rows})
    movies = list({r.movie_id for r in rows})
    u_idx  = {u: i for i, u in enumerate(users)}
    m_idx  = {m: i for i, m in enumerate(movies)}

    mat = np.zeros((len(users), len(movies)))
    for r in rows:
        mat[u_idx[r.user_id]][m_idx[r.movie_id]] = r.rating

    if user_id not in u_idx:
        return []

    uid  = u_idx[user_id]
    sims = cosine_similarity(mat[uid].reshape(1, -1), mat)[0]
    sims[uid] = 0

    K      = min(10, len(users) - 1)
    top_k  = np.argsort(sims)[::-1][:K]
    seen   = {r.movie_id for r in rows if r.user_id == user_id}

    scores = {}
    for k in top_k:
        if sims[k] <= 0:
            continue
        for mi, rating in enumerate(mat[k]):
            if rating >= 4.0:
                mid = movies[mi]
                if mid not in seen:
                    scores[mid] = scores.get(mid, 0) + sims[k] * rating

    return [mid for mid, _ in sorted(scores.items(), key=lambda x: -x[1])[:n]]

# ── 混合推荐 ────────────────────────────────────────
def hybrid_recommend(user_id: int, db: Session, n: int = 20) -> List[int]:
    from app.models.rating import UserRating
    from app.models.movie import Movie

    cnt  = db.query(UserRating).filter(UserRating.user_id == user_id).count()
    seen = {r.movie_id for r in db.query(UserRating).filter(UserRating.user_id == user_id).all()}

    # 冷启动：评分不足 5 条，返回热门未看
    if cnt < 5:
        movies = (db.query(Movie)
                  .filter(Movie.vote_count > 100)
                  .order_by(Movie.popularity.desc())
                  .limit(n + len(seen)).all())
        return [m.id for m in movies if m.id not in seen][:n]

    # 取用户评分最高的 3 部做内容推荐种子
    top = (db.query(UserRating)
           .filter(UserRating.user_id == user_id, UserRating.rating >= 4.0)
           .order_by(UserRating.rating.desc())
           .limit(3).all())

    content_ids = []
    for r in top:
        content_ids += content_recommend(r.movie_id, n=30, exclude=seen)
    # 去重保序
    seen_set, content_ids = set(), [x for x in content_ids
                                     if not (x in seen_set or seen_set.add(x))]

    cf_ids = usercf_recommend(user_id, db, n=n)

    # 加权合并：CF 0.6 + 内容 0.4
    scores = {}
    for i, mid in enumerate(cf_ids):
        scores[mid] = scores.get(mid, 0) + 0.6 / (i + 1)
    for i, mid in enumerate(content_ids[:n * 2]):
        scores[mid] = scores.get(mid, 0) + 0.4 / (i + 1)

    return [mid for mid, _ in sorted(scores.items(), key=lambda x: -x[1])[:n]]