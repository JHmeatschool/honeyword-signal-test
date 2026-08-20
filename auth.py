# auth.py — JWT 발급/검증 + 허니워드 판정
import datetime
import jwt  # PyJWT
from seed import USERS

SECRET = "dev-secret-change-me"   # 실서비스면 환경변수로
ALGO = "HS256"


def check_credential(username: str, password: str) -> str:
    """genuine / honey / invalid 반환"""
    u = USERS.get(username)
    if not u:
        return "invalid"
    if password == u["genuine"]:
        return "genuine"
    if password in u["honeywords"]:
        return "honey"
    return "invalid"


def make_token(username: str, sid: str) -> str:
    # 주의: genuine/honey 경로는 토큰에 넣지 않는다.
    #       (JWT payload는 누구나 열어볼 수 있어서 → 경로는 서버(SESSIONS)에만 보관)
    payload = {
        "sub": username,
        "sid": sid,
        "iat": datetime.datetime.utcnow(),
        "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=1),
    }
    return jwt.encode(payload, SECRET, algorithm=ALGO)


def read_token(token: str) -> dict:
    return jwt.decode(token, SECRET, algorithms=[ALGO])
