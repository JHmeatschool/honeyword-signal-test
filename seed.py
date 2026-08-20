# seed.py — 사용자별 진짜 비밀번호 + 허니워드
# (연구용 프로토타입이라 평문. 실서비스면 해시/허니체커 분리)

USERS = {
    "user01": {
        "genuine": "Pa$$w0rd_01",
        "honeywords": ["summer2024", "qwerty123!", "user01love", "iloveyou7"],
    },
    "user02": {
        "genuine": "Tr0ub4dour&3",
        "honeywords": ["dragon2023", "letmein99", "user02pw!", "monkey123"],
    },
}
