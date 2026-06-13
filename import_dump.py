# import pymysql
#
# conn = pymysql.connect(
#     host='gateway01.ap-northeast-1.prod.aws.tidbcloud.com',
#     port=4000,
#     user='2GAkx6kiSvj5QbZ.root',
#     password='ONkkc5AFv6ID3a5v',
#     database='movie_db',
#     ssl_ca='isrgrootx1.pem',
#     ssl_verify_cert=True,
#     charset='utf8mb4'
# )
#
# def split_sql(sql):
#     """按 ; 分割语句，但忽略字符串内部的 ;"""
#     statements = []
#     current = []
#     in_string = False
#     quote_char = None
#     i = 0
#     while i < len(sql):
#         ch = sql[i]
#         if in_string:
#             if ch == '\\':  # 转义字符，跳过下一个字符
#                 current.append(ch)
#                 if i + 1 < len(sql):
#                     current.append(sql[i+1])
#                     i += 2
#                     continue
#             elif ch == quote_char:
#                 in_string = False
#         else:
#             if ch in ("'", '"'):
#                 in_string = True
#                 quote_char = ch
#             elif ch == ';':
#                 stmt = ''.join(current).strip()
#                 if stmt:
#                     statements.append(stmt)
#                 current = []
#                 i += 1
#                 continue
#         current.append(ch)
#         i += 1
#     stmt = ''.join(current).strip()
#     if stmt:
#         statements.append(stmt)
#     return statements
#
#
#
# with open('movie_db_dump.sql', 'r', encoding='utf-8') as f:
#     sql = f.read()
#
# # 在连接成功后，导入前先执行（清空所有表）
# with conn.cursor() as cur:
#     cur.execute("SET FOREIGN_KEY_CHECKS=0")
#     cur.execute("SHOW TABLES")
#     tables = [r[0] for r in cur.fetchall()]
#     for t in tables:
#         cur.execute(f"DROP TABLE IF EXISTS `{t}`")
#     cur.execute("SET FOREIGN_KEY_CHECKS=1")
# conn.commit()
# print("已清空所有表")
#
# statements = split_sql(sql)
# print(f"共解析出 {len(statements)} 条语句")
#
# errors = 0
# with conn.cursor() as cur:
#     for i, stmt in enumerate(statements):
#         if stmt.startswith('--') or stmt.upper().startswith('CREATE DATABASE') or 'character_set_client' in stmt:
#             continue
#         try:
#             cur.execute(stmt)
#         except Exception as e:
#             errors += 1
#             print(f"语句 {i} 出错: {str(e)[:200]}")
#         if i % 50 == 0:
#             print(f"进度: {i}/{len(statements)}")
#     conn.commit()
#
# print(f"完成，共 {len(statements)} 条语句，{errors} 条出错")

import pymysql

conn = pymysql.connect(
    host='gateway01.ap-northeast-1.prod.aws.tidbcloud.com',
    port=4000,
    user='2GAkx6kiSvj5QbZ.root',
    password='ONkkc5AFv6ID3a5v',
    database='movie_db',
    ssl_ca='isrgrootx1.pem',
    ssl_verify_cert=True,
    charset='utf8mb4'
)

with conn.cursor() as cur:
    cur.execute("SHOW TABLES")
    for (table,) in cur.fetchall():
        cur.execute(f"SELECT COUNT(*) FROM `{table}`")
        print(f"{table}: {cur.fetchone()[0]} 条")

conn.close()