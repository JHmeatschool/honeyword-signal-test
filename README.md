# Honeyword-Triggered Decoy — Signal Testbed

허니워드로 로그인하면 **LLM 디코이**로, 진짜 비밀번호로 로그인하면 **진짜 서비스**로 라우팅되는
최소 파이프라인. 로그인 응답은 두 경로가 **동일**하고, 오직 **non-semantic signal**(응답시간·크기·상태·인젝션 등)로만 구별된다는 것을 실증하기 위한 테스트베드.

> 연구용 프로토타입. 실서비스 아님 (SECRET·비밀번호 전부 더미).

## 구성

| 파일 | 역할 |
|---|---|
| `main.py` | FastAPI 앱: 로그인 + genuine/honey 라우팅 + 노트 API |
| `auth.py` | JWT 발급/검증 + 허니워드 판정 |
| `decoy.py` | 얇은 LLM 디코이 (Ollama 호출, 로그인 username 주입) |
| `seed.py` | 사용자별 진짜 비번 + 허니워드 (더미) |
| `measure_pipeline.sh` | genuine vs honey **signal 7종** 측정 |
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

### 전체 signal 측정 (한 방, 7종)
```bash
bash measure_pipeline.sh
```
genuine vs honey를 7가지 signal로 비교:

| # | signal | genuine | honey (LLM 디코이) |
|---|---|---|---|
| 1 | 타이밍 (latency) | ms | 초 |
| 2 | 거대응답 유도 | 작음·빠름 | 큼·느림 (요청으로 생성비용 유도) |
| 3 | 동시성 (부하) | flat | 추론큐 포화로 급증 |
| 4 | 비결정성 (크기) | 고정 | 매번 변동 |
| 5 | 정체성 | 동일 | 본문 드리프트 (헤더는 masked, 아래 참고) |
| 6 | 상태/인과 (CRUD) | 저장→조회 일관 | 있는척+앞뒤 불일치 |
| 7 | 프롬프트 인젝션 | 무시(데이터) | 복종 (적응형 payload) |

> honey는 LLM이라 느려서 전체 3~5분 소요.

## 계정 (seed.py)

| username | 진짜 비번 | 허니워드(예) |
|---|---|---|
| user01 | `Pa$$w0rd_01` | summer2024, qwerty123! … |
| user02 | `Tr0ub4dour&3` | dragon2023, letmein99 … |

## 핵심 관찰

1. **semantic을 맞춰도 signal은 샌다.** 로그인 성공 응답을 완전히 똑같이 맞추고 디코이 내용(username 등)까지 맞춰도, 응답시간·상태 일관성·인젝션 반응 같은 non-semantic signal은 남는다.

2. **공유 front-end가 헤더 정체성을 masking 한다.** genuine·honey 모두 같은 uvicorn 앞단을 거쳐 `Server` 헤더가 동일하다. 즉 헤더 레벨 정체성 신호는 공통 상쇄되고, 정체성 드리프트는 **LLM 생성 본문**에서만 나타나 사실상 비결정성과 겹친다. → 허니워드-디코이 아키텍처에서 어떤 signal이 살아남는지를 보여주는 사례.

3. **형식 제약은 완화지 해결이 아니다.** 디코이의 "JSON 스키마만 응답" 제약은 순진한 인젝션/거대응답을 막지만, **형식에 맞춘 적응형 payload**(예: `id` 필드에 마커/긴 문자열 주입)에는 뚫린다.