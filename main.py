# main.py — 로그인 앞단 + genuine/honey 라우팅 + 노트 API
#
# 흐름:
#   POST /api/login  ->  진짜비번=genuine / 허니워드=honey  (응답은 완전히 동일)
#   이후 요청은 토큰의 세션으로 경로 판별:
#       genuine -> 진짜 로직(실제 상태 유지)
#       honey   -> LLM 디코이(생성, 상태 없음)
#
# 실행:  uvicorn main:app --host 127.0.0.1 --port 8000
import uuid
from fastapi import FastAPI, Request, Header
from fastapi.responses import JSONResponse, Response
from auth import check_credential, make_token, read_token
from decoy import llm_decoy

app = FastAPI()

SESSIONS = {}        # sid -> "genuine" / "honey"   (경로는 서버에만)
NOTES = {}           # genuine 저장소: username -> {id: content}
_next_id = {"v": 1}


def _path(authorization: str):
    """토큰에서 (경로, 사용자) 판별. 실패 시 (None, None)."""
    if not authorization:
        return None, None
    token = authorization.replace("Bearer ", "").strip()
    try:
        data = read_token(token)
    except Exception:
        return None, None
    return SESSIONS.get(data.get("sid")), data.get("sub")


# ---------- 로그인 ----------
@app.post("/api/login")
async def login(req: Request):
    data = await req.json()
    username = data.get("username", "")
    password = data.get("password", "")
    verdict = check_credential(username, password)
    if verdict == "invalid":
        return JSONResponse({"status": "fail", "message": "Invalid credentials"}, status_code=401)

    sid = uuid.uuid4().hex
    SESSIONS[sid] = verdict          # genuine/honey 는 서버에만 저장
    token = make_token(username, sid)

    # ★ genuine이든 honey든 로그인 응답은 「완전히 동일」 → content로는 구별 불가
    return JSONResponse({
        "status": "success",
        "accessToken": token,
        "sessionId": sid,
        "redirect": "/dashboard",
    }, status_code=200)


# ---------- 대시보드 ----------
@app.get("/api/dashboard")
def dashboard(authorization: str = Header(None)):
    path, user = _path(authorization)
    if path is None:
        return JSONResponse({"status": "fail", "message": "Unauthorized"}, status_code=401)
    if path == "genuine":
        return {"user": user, "plan": "free",
                "recentItems": list(NOTES.get(user, {}).values())}
    return Response(content=llm_decoy("GET", "/api/dashboard", None, user),
                    media_type="application/json")


# ---------- 노트 CRUD ----------
@app.post("/api/notes")
async def create_note(req: Request, authorization: str = Header(None)):
    path, user = _path(authorization)
    if path is None:
        return JSONResponse({"status": "fail"}, status_code=401)
    body = await req.json()
    if path == "genuine":
        nid = _next_id["v"]; _next_id["v"] += 1
        NOTES.setdefault(user, {})[nid] = body.get("content", "")
        return {"status": "success", "id": nid}
    return Response(content=llm_decoy("POST", "/api/notes", body, user),
                    media_type="application/json")


@app.get("/api/notes")
def list_notes(authorization: str = Header(None)):
    path, user = _path(authorization)
    if path is None:
        return JSONResponse({"status": "fail"}, status_code=401)
    if path == "genuine":
        notes = [{"id": i, "content": c} for i, c in NOTES.get(user, {}).items()]
        return {"notes": notes}
    return Response(content=llm_decoy("GET", "/api/notes", None, user),
                    media_type="application/json")


@app.delete("/api/notes/{note_id}")
def delete_note(note_id: int, authorization: str = Header(None)):
    path, user = _path(authorization)
    if path is None:
        return JSONResponse({"status": "fail"}, status_code=401)
    if path == "genuine":
        NOTES.get(user, {}).pop(note_id, None)
        return {"status": "deleted", "id": note_id}
    return Response(content=llm_decoy("DELETE", f"/api/notes/{note_id}", None, user),
                    media_type="application/json")