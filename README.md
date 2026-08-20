# Honeyword-Triggered Decoy — Signal Testbed

허니워드로 로그인하면 **LLM 디코이**로, 진짜 비밀번호로 로그인하면 **진짜 서비스**로 라우팅되는
최소 파이프라인. 로그인 응답은 두 경로가 **동일**하고, 오직 **non-semantic signal**(응답시간·크기·상태·인젝션)로만 구별된다는 것을 실증하기 위한 테스트베드.

> 연구용 프로토타입. 실서비스 아님 (SECRET·비밀번호 전부 더미).

## 구성

| 파일 | 역할 |
|---|---|
| `main.py` | FastAPI 앱: 로그인 + genuine/honey 라우팅 + 노트 API |
| `auth.py` | JWT 발급/검증 + 허니워드 판정 |
| `decoy.py` | 얇은 LLM 디코이 (Ollama 호출, 로그인 username 주입) |
| `seed.py` | 사용자별 진짜 비번 + 허니워드 (더미) |
| `measure_pipeline.sh` | genuine vs honey signal 측정 (타이밍·크기·CRUD·인젝션) |
| `requirements.txt` | 파이썬 의존성 |

## 흐름

```
공격자 --로그인--> [main.py: 허니워드 판정]
                       ├─ 진짜 비번  --> genuine 로직 (실제 상태 유지, ms 응답)
                       └─ 허니워드   --> LLM 디코이 (Ollama 생성, 초 단위·상태 없음)
로그인 응답은 두 경로가 완전히 동일 → content로는 구별 불가
```

## 설치 & 실행

### 1. 사전 준비
- Python 3.10+
- [Ollama](https://ollama.com) 설치 + 모델: `ollama pull llama3`
  (다른 모델 쓰면 `decoy.py`의 `MODEL` 수정)

### 2. 가상환경 + 의존성
```bash
python -m venv venv
source venv/Scripts/activate      # Windows Git Bash
# source venv/bin/activate        # macOS/Linux
pip install -r requirements.txt
```

### 3. 서버 실행
```bash
uvicorn main:app --host 127.0.0.1 --port 8000
```

## 테스트

### 빠른 확인 (로그인 두 경로가 동일한지)
```bash
# genuine
curl -s -X POST localhost:8000/api/login -H "Content-Type: application/json" \
  -d '{"username":"user01","password":"Pa$$w0rd_01"}'
# honey
curl -s -X POST localhost:8000/api/login -H "Content-Type: application/json" \
  -d '{"username":"user01","password":"summer2024"}'
```
→ 두 응답 구조가 동일(status·token·redirect), 값만 랜덤 = content로 구별 불가.

### 전체 signal 측정 (한 방)
```bash
bash measure_pipeline.sh
```
genuine vs honey를 4가지로 비교:
- **타이밍/크기**: genuine ms·고정 / honey 초·변동
- **CRUD 상태**: genuine 일관 / honey 앞뒤 불일치
- **인젝션**: genuine 무시 / honey 복종(적응형 payload)

> honey는 LLM이라 느려서 전체 1~2분 소요.

## 계정 (seed.py)

| username | 진짜 비번 | 허니워드(예) |
|---|---|---|
| user01 | `Pa$$w0rd_01` | summer2024, qwerty123! … |
| user02 | `Tr0ub4dour&3` | dragon2023, letmein99 … |

## 핵심 관찰

로그인 성공 응답을 완전히 똑같이 맞추고, 디코이 내용(username 등)까지 맞춰도
**응답시간·상태 일관성·인젝션 반응** 같은 non-semantic signal은 남는다.
→ "semantic을 아무리 맞춰도 signal은 샌다"를 실제 허니워드 파이프라인에서 확인.