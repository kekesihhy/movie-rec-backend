import os, sys, json, pickle
import pandas as pd
import pymysql
from dotenv import load_dotenv
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

DB_HOST     = os.getenv('DB_HOST', 'localhost')
DB_PORT     = int(os.getenv('DB_PORT', 3306))
DB_USER     = os.getenv('DB_USER', 'root')
DB_PASSWORD = os.getenv('DB_PASSWORD', '')
DB_NAME     = os.getenv('DB_NAME', 'movie_db')

CSV_PATH  = os.path.join(os.path.dirname(__file__), 'tmdb_5000_movies.csv')
CACHE_DIR = os.path.join(os.path.dirname(__file__), '..', 'cache')

COLUMNS = [
    'budget','genres','homepage','id','keywords','original_language',
    'original_title','overview','popularity','production_companies',
    'production_countries','release_date','revenue','runtime',
    'spoken_languages','status','tagline','title','vote_average','vote_count'
]

# ── 第一步：读取清洗 ──────────────────────────────

def load_and_clean():
    print("【1/3】读取并清洗 CSV...")
    df = pd.read_csv(CSV_PATH, header=None, names=COLUMNS)
    print(f"  原始行数: {len(df)}")

    df = df[df['status'] == 'Released'].copy()

    df['id']           = pd.to_numeric(df['id'], errors='coerce').fillna(0).astype(int)
    df['vote_count']   = pd.to_numeric(df['vote_count'], errors='coerce').fillna(0).astype(int)
    df['popularity']   = pd.to_numeric(df['popularity'], errors='coerce').fillna(0.0)
    df['vote_average'] = pd.to_numeric(df['vote_average'], errors='coerce').fillna(0.0)

    df['budget']  = pd.to_numeric(df['budget'], errors='coerce')
    df['revenue'] = pd.to_numeric(df['revenue'], errors='coerce')
    df['budget']  = df['budget'].apply(lambda x: None if pd.isna(x) or x == 0 else int(x))
    df['revenue'] = df['revenue'].apply(lambda x: None if pd.isna(x) or x == 0 else int(x))

    df['runtime'] = pd.to_numeric(df['runtime'], errors='coerce')
    median_rt = int(df[df['runtime'] > 0]['runtime'].median())
    df['runtime'] = df['runtime'].apply(lambda x: median_rt if pd.isna(x) or x == 0 else int(x))

    for col in ['overview', 'tagline', 'homepage', 'original_title']:
        df[col] = df[col].fillna('')

    df['release_date'] = pd.to_datetime(df['release_date'], errors='coerce')
    df['year']         = df['release_date'].dt.year.fillna(0).astype(int)
    df['release_date'] = df['release_date'].apply(lambda x: x.date() if pd.notna(x) else None)

    df = df[df['id'] > 0].drop_duplicates(subset='id')
    print(f"  清洗后行数: {len(df)}")
    return df

# ── 第二步：导入数据库 ────────────────────────────

TABLES_SQL = [
"""CREATE TABLE IF NOT EXISTS movies (
    id INT PRIMARY KEY, title VARCHAR(255) NOT NULL,
    original_title VARCHAR(255), overview TEXT, tagline VARCHAR(1000),
    release_date DATE, year SMALLINT, runtime SMALLINT,
    budget BIGINT, revenue BIGINT, popularity FLOAT,
    vote_average FLOAT, vote_count INT, status VARCHAR(50),
    original_language VARCHAR(10), homepage VARCHAR(1000),
    poster_url VARCHAR(500),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4""",
"""CREATE TABLE IF NOT EXISTS genres (
    id INT PRIMARY KEY, name VARCHAR(100) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4""",
"""CREATE TABLE IF NOT EXISTS movie_genres (
    movie_id INT NOT NULL, genre_id INT NOT NULL,
    PRIMARY KEY (movie_id, genre_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4""",
"""CREATE TABLE IF NOT EXISTS keywords (
    id INT PRIMARY KEY, name VARCHAR(300) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4""",
"""CREATE TABLE IF NOT EXISTS movie_keywords (
    movie_id INT NOT NULL, keyword_id INT NOT NULL,
    PRIMARY KEY (movie_id, keyword_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4""",
"""CREATE TABLE IF NOT EXISTS companies (
    id INT PRIMARY KEY, name VARCHAR(300) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4""",
"""CREATE TABLE IF NOT EXISTS movie_companies (
    movie_id INT NOT NULL, company_id INT NOT NULL,
    PRIMARY KEY (movie_id, company_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4""",
"""CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(100) NOT NULL UNIQUE,
    email VARCHAR(200) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    avatar_url VARCHAR(500),
    preferred_genres VARCHAR(500),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4""",
"""CREATE TABLE IF NOT EXISTS user_ratings (
    user_id INT NOT NULL, movie_id INT NOT NULL,
    rating FLOAT NOT NULL, rated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (user_id, movie_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4""",
"""CREATE TABLE IF NOT EXISTS user_favorites (
    user_id INT NOT NULL, movie_id INT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (user_id, movie_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4""",
]

def parse_json_items(s):
    try:
        return [(int(x.get('id',0)), str(x.get('name','')).strip())
                for x in json.loads(s) if x.get('name')]
    except:
        return []

def get_conn(with_db=True):
    kwargs = dict(host=DB_HOST, port=DB_PORT, user=DB_USER,
                  password=DB_PASSWORD, charset='utf8mb4',
                  cursorclass=pymysql.cursors.DictCursor)
    if with_db:
        kwargs['database'] = DB_NAME
    return pymysql.connect(**kwargs)

def setup_database():
    conn = get_conn(with_db=False)
    with conn.cursor() as cur:
        cur.execute(f"CREATE DATABASE IF NOT EXISTS `{DB_NAME}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
    conn.commit(); conn.close()

    conn = get_conn()
    with conn.cursor() as cur:
        for sql in TABLES_SQL:
            cur.execute(sql)
    conn.commit(); conn.close()
    print("  数据库和表结构就绪")

def import_data(df):
    def _f(v, default=0.0):
        try:
            r = float(v)
            return default if r != r else r
        except Exception:
            return default

    def _i(v, default=0):
        try:
            r = float(v)
            return default if r != r else int(r)
        except Exception:
            return default

    def _s(v, maxlen=None, default=''):
        s = str(v) if v is not None else default
        if s.lower() == 'nan':
            s = default
        return s[:maxlen] if maxlen else s

    def _n(v):
        if v is None:
            return None
        try:
            import pandas as pd
            if pd.isna(v):
                return None
        except Exception:
            pass
        try:
            f = float(v)
            return None if f != f else int(f)
        except Exception:
            return None

    def _date(v):
        if v is None:
            return None
        try:
            import pandas as pd
            if pd.isna(v):
                return None
        except Exception:
            pass
        return v

    conn = get_conn()
    try:
        with conn.cursor() as cur:
            rows = [(_i(r['id']), _s(r['title'], 255), _s(r['original_title'], 255),
                     _s(r['overview']), _s(r['tagline'], 1000), _date(r['release_date']),
                     _i(r['year']), _i(r['runtime']), _n(r['budget']), _n(r['revenue']),
                     _f(r['popularity']), _f(r['vote_average']), _i(r['vote_count']),
                     _s(r['status']), _s(r['original_language'], 10), _s(r['homepage'], 1000))
                    for _, r in df.iterrows()]
            cur.executemany("""INSERT IGNORE INTO movies
                (id,title,original_title,overview,tagline,release_date,year,runtime,
                 budget,revenue,popularity,vote_average,vote_count,status,original_language,homepage)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""", rows)
            print(f"  movies: {len(rows)} 条")

            # genres
            gmap, mg = {}, []
            for _, r in df.iterrows():
                for gid, gname in parse_json_items(r['genres']):
                    if gid > 0:
                        gmap[gid] = gname
                        mg.append((int(r['id']), gid))
            for gid, gname in gmap.items():
                cur.execute("INSERT IGNORE INTO genres VALUES (%s,%s)", (gid, gname[:100]))
            cur.executemany("INSERT IGNORE INTO movie_genres VALUES (%s,%s)", mg)
            print(f"  genres: {len(gmap)} 个类型，{len(mg)} 条关联")

            # keywords
            kmap, mk = {}, []
            for _, r in df.iterrows():
                for kid, kname in parse_json_items(r['keywords']):
                    if kid > 0:
                        kmap[kid] = kname
                        mk.append((int(r['id']), kid))
            for kid, kname in kmap.items():
                cur.execute("INSERT IGNORE INTO keywords VALUES (%s,%s)", (kid, kname[:300]))
            cur.executemany("INSERT IGNORE INTO movie_keywords VALUES (%s,%s)", mk)
            print(f"  keywords: {len(kmap)} 个关键词，{len(mk)} 条关联")

            # companies
            cmap, mc = {}, []
            for _, r in df.iterrows():
                for cid, cname in parse_json_items(r['production_companies']):
                    if cid > 0:
                        cmap[cid] = cname
                        mc.append((int(r['id']), cid))
            for cid, cname in cmap.items():
                cur.execute("INSERT IGNORE INTO companies VALUES (%s,%s)", (cid, cname[:300]))
            cur.executemany("INSERT IGNORE INTO movie_companies VALUES (%s,%s)", mc)
            print(f"  companies: {len(cmap)} 家公司，{len(mc)} 条关联")

        conn.commit()
    finally:
        conn.close()

# ── 第三步：TF-IDF ────────────────────────────────

def compute_tfidf():
    print("【3/3】计算 TF-IDF 相似度矩阵（约1分钟）...")
    conn = get_conn()
    with conn.cursor() as cur:
        cur.execute("SELECT id, overview FROM movies ORDER BY id")
        movies = cur.fetchall()
        cur.execute("SELECT mg.movie_id, g.name FROM movie_genres mg JOIN genres g ON mg.genre_id=g.id")
        genre_rows = cur.fetchall()
        cur.execute("SELECT mk.movie_id, k.name FROM movie_keywords mk JOIN keywords k ON mk.keyword_id=k.id")
        kw_rows = cur.fetchall()
    conn.close()

    gdict = {}
    for r in genre_rows:
        gdict.setdefault(r['movie_id'], []).append(r['name'].replace(' ','_'))
    kdict = {}
    for r in kw_rows:
        kdict.setdefault(r['movie_id'], []).append(r['name'].replace(' ','_'))

    movie_ids = [m['id'] for m in movies]
    contents = []
    for m in movies:
        g = ' '.join(gdict.get(m['id'], []))
        k = ' '.join(kdict.get(m['id'], [])[:30])
        o = str(m['overview'] or '')
        contents.append(f"{g} {g} {g} {k} {o}")  # genres 重复3次加权

    vec = TfidfVectorizer(max_features=8000, stop_words='english', ngram_range=(1,2), min_df=2)
    mat = vec.fit_transform(contents)
    sim = cosine_similarity(mat)

    os.makedirs(CACHE_DIR, exist_ok=True)
    cache_path = os.path.join(CACHE_DIR, 'tfidf_matrix.pkl')
    with open(cache_path, 'wb') as f:
        pickle.dump({'movie_ids': movie_ids, 'similarity': sim,
                     'id_to_index': {mid: i for i, mid in enumerate(movie_ids)}}, f,
                    protocol=pickle.HIGHEST_PROTOCOL)
    print(f"  矩阵维度: {sim.shape}，已缓存到 cache/tfidf_matrix.pkl")

# ── 入口 ──────────────────────────────────────────

if __name__ == '__main__':
    print("=" * 45)
    print("  电影推荐系统 · 数据预处理")
    print("=" * 45)
    df = load_and_clean()
    print("【2/3】导入数据库...")
    setup_database()
    import_data(df)
    compute_tfidf()
    print("\n✅ 全部完成，可以启动后端了！")