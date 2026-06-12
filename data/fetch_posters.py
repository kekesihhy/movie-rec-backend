import os, time, pymysql, requests
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

TMDB_API_KEY = "4df0445a07cf2255b150b106bf97538d"

conn = pymysql.connect(
    host=os.getenv('DB_HOST', 'localhost'),
    port=int(os.getenv('DB_PORT', 3306)),
    user=os.getenv('DB_USER', 'root'),
    password=os.getenv('DB_PASSWORD', ''),
    database=os.getenv('DB_NAME', 'movie_db'),
    charset='utf8mb4'
)

with conn.cursor() as cur:
    cur.execute("SELECT id FROM movies WHERE poster_url IS NULL ORDER BY popularity DESC")
    ids = [r[0] for r in cur.fetchall()]

print(f"共 {len(ids)} 部需要处理")

updated = 0
for i, mid in enumerate(ids):
    try:
        r = requests.get(
            f"https://api.themoviedb.org/3/movie/{mid}",
            params={"api_key": TMDB_API_KEY},
            timeout=5
        )
        if r.status_code == 200:
            path = r.json().get("poster_path")
            if path:
                with conn.cursor() as cur:
                    cur.execute(
                        "UPDATE movies SET poster_url=%s WHERE id=%s",
                        (f"https://image.tmdb.org/t/p/w500{path}", mid)
                    )
                conn.commit()
                updated += 1
    except Exception:
        pass

    if (i + 1) % 100 == 0:
        print(f"{i+1}/{len(ids)} 已更新 {updated} 张")
    time.sleep(0.26)  # 不超过限速 4次/秒

conn.close()
print(f"完成，共更新 {updated} 张海报")