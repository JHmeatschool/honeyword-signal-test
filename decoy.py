# decoy.py — 얇은 LLM 디코이 (Ollama 호출)
# honey 경로일 때, 진짜 노트 API 응답을 흉내내도록 LLM에게 생성시킴.
# 로그인한 username을 컨텍스트로 주입 → 디코이 내용이 실제 로그인 사용자와 일치하게.
import requests

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "llama3"

# {username} 은 로그인한 사용자로 채워짐. (JSON 예시의 중괄호는 {{ }} 로 이스케이프)
SYSTEM = """You are the backend of a JSON notes web service.
The authenticated user's username is "{username}".
ALWAYS use exactly this username in any "user" field. Never invent a different name.
Respond ONLY with a realistic JSON body that such a server would return.
No explanation, no markdown code fences — JSON only.
Match this general shape:
- GET /api/dashboard  -> {{"user": "{username}", "plan": "free", "recentItems": [...]}}
- GET /api/notes      -> {{"notes": [{{"id": 1, "content": "..."}}]}}
- POST /api/notes     -> {{"status": "success", "id": <int>}}
- DELETE /api/notes/x -> {{"status": "deleted", "id": <int>}}
"""


def llm_decoy(method: str, endpoint: str, body, username: str = "user") -> str:
    system = SYSTEM.format(username=username)
    prompt = f"{system}\nRequest: {method} {endpoint}\nRequest body: {body}\nJSON response:"
    try:
        r = requests.post(
            OLLAMA_URL,
            json={"model": MODEL, "prompt": prompt, "stream": False},
            timeout=120,
        )
        return r.json().get("response", "{}")
    except Exception:
        return '{"error": "decoy unavailable"}'