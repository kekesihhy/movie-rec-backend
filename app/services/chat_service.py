import os, requests
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), '..', '..', '.env'))

API_KEY = os.getenv('OPENROUTER_API_KEY')
MODEL   = os.getenv('OPENROUTER_MODEL', 'openrouter/auto')
URL     = "https://openrouter.ai/api/v1/chat/completions"

SYSTEM_PROMPT = """你是 MovieRec 电影推荐网站的智能助手，名字叫"小幕"。
你了解 TMDB 电影数据库中的电影信息（包括电影名称、上映年份、评分、类型、简介等）。
你可以帮用户：
1. 推荐电影（根据类型、心情、相似电影等）
2. 回答电影相关问题（上映时间、评分、剧情简介等）
3. 分析用户的观影口味

回答时态度友好、简洁，使用中文回复。如果用户问的电影你不确定具体信息，可以诚实告知，
但仍然可以基于你的知识给出大致推荐建议。回复控制在 150 字以内，除非用户要求详细说明。"""

def chat_completion(messages: list[dict], user_context: str = "") -> str:
    system = SYSTEM_PROMPT
    if user_context:
        system += f"\n\n用户信息：{user_context}"

    payload = {
        "model": MODEL,
        "messages": [{"role": "system", "content": system}] + messages,
        "max_tokens": 1500,
        "temperature": 0.7,
    }
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    resp = requests.post(URL, json=payload, headers=headers, timeout=30)
    resp.raise_for_status()
    data = resp.json()
    return data["choices"][0]["message"]["content"]