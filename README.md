# goenaé SEO LAB v2 — 서버 배포 준비용

휴대폰/PC 반응형 Flask 웹앱. 검색량은 네이버 검색광고 공식 API `/keywordstool`에서 인증 후 조회하며, 쇼핑 자연검색 순위는 **자동 조회하지 않음**. 순위 수동 입력은 '미검증'으로 표기.

## 필수 보안 환경변수

- `GOENAE_APP_USER`: 로그인 아이디 (네이버 아이디와 다르게 정할 것)
- `GOENAE_APP_PASSWORD_HASH`: 웹앱 전용 비밀번호의 Werkzeug 해시값 (평문 비밀번호 아님)
- `NAVER_AD_API_KEY`: 네이버 검색광고 API KEY
- `NAVER_AD_SECRET_KEY`: 네이버 검색광고 SECRET KEY
- `NAVER_AD_CUSTOMER_ID`: 네이버 검색광고 CUSTOMER ID
- `GOENAE_DB`: 데이터베이스 저장 위치 (선택; 영구 디스크 권장)

비밀번호 해시 생성은 로컬 Python에서 `python -c "from werkzeug.security import generate_password_hash; import getpass; print(generate_password_hash(getpass.getpass('웹앱 비밀번호: ')))"` 실행. 생성된 해시만 호스팅 환경변수에 넣습니다. 네이버 로그인 비밀번호는 절대 재사용하지 마세요.

환경변수에 로그인 계정/해시가 없으면 모든 요청을 503으로 차단합니다. 로그인 시 브라우저의 HTTP Basic 인증 팝업이 뜹니다. **반드시 HTTPS 제공 호스팅에서만 운영**하세요.

## 배포

Python 지원 웹 호스팅에 소스 등록, `pip install -r requirements.txt`, 시작 명령 `gunicorn --bind 0.0.0.0:$PORT --workers 1 --threads 2 app:A` 설정. 무료 호스팅의 임시 디스크는 재시작 시 SQLite 데이터가 사라질 수 있으므로 영구 저장소를 별도로 마련하세요.

## 데이터 정확도

- API 연결 전 검색량은 미확인으로 표시.
- 검색광고 API에서 `<10` 같은 비숫자 반환값은 미확인으로 표시.
- 쇼핑 순위 수동 입력은 미검증으로 표시.
- `노와이어브라`, `풀컵브라` 등 초기 후보는 상품 적합성 확인 후 사용.
- 서버에서 직접 API 인증을 성공시키기 전까지 실측 성공이라고 말할 수 없음.

## 보안/운영 주의

기본 인증은 단일 관리자용 최소 보호입니다. 상용 공개 서비스에는 사용자 인증, CSRF 보호, 요청 제한, 백업 및 감사를 추가해야 합니다. API 키나 `.env` 파일을 GitHub에 올리지 마세요. 인증정보가 노출되면 즉시 재발급하세요.
