## 1. Vercel/Neon 배포

- [x] 1.1 Vercel MCP + CLI 인증, 프로젝트 `gmchoi-s-projects/taskflow-openspec` 연결
- [x] 1.2 `api/index.py` 작성: `backend/main.py`의 FastAPI `app`을 Vercel Python 런타임이 인식하도록 재노출
- [x] 1.3 `vercel.json` 작성: API 경로는 `api/index.py`로, 나머지는 `frontend/`의 정적 파일로 라우팅
- [x] 1.4 `backend/main.py`: `VERCEL` 환경변수일 때 로컬 전용 `StaticFiles` 마운트 생략
- [x] 1.5 `backend/database.py`: `postgres://` → `postgresql://` 스킴 정규화(SQLAlchemy/psycopg2 호환)
- [x] 1.6 `backend/requirements.txt`에 `psycopg2-binary` 추가
- [x] 1.7 `vercel integration add neon`으로 Neon Postgres 프로비저닝, `DATABASE_URL` 자동 주입 확인
- [x] 1.8 `JWT_SECRET`, `CORS_ORIGINS` 환경변수를 Production/Preview에 설정
- [x] 1.9 `vercel deploy --prod`로 배포, `GET /health` 200 확인

## 2. 루트 경로 404 수정

- [x] 2.1 배포 도메인 루트(`/`) 접근 시 404 발생 원인 파악(`frontend/index.html` 부재)
- [x] 2.2 `frontend/index.html` 추가: 토큰 유무 확인 후 로그인/팀선택/앱 화면으로 라우팅
- [x] 2.3 재배포 후 로그인 상태/비로그인 상태 각각 루트 접근 시 정상 리다이렉트 확인

## 3. 자동 로그인 + 로그인 상태 유지

- [x] 3.1 `frontend/js/api.js`: `setToken(token, remember)` — remember 여부에 따라 `localStorage`/`sessionStorage` 분기, `getToken()`은 둘 다 확인
- [x] 3.2 `frontend/js/api.js`: `autoLoginRedirectIfPossible()` 공용 헬퍼 추가(토큰 검증 후 `team_id`에 따라 리다이렉트)
- [x] 3.3 `login.html`에 "로그인 상태 유지" 체크박스 추가, 로그인 시 체크값을 `setToken`에 전달
- [x] 3.4 `login.html`, `signup.html`, `index.html`에서 페이지 로드시 `autoLoginRedirectIfPossible()` 호출

## 4. 다크/라이트 모드

- [x] 4.1 `frontend/js/theme.js` 작성: 테마 조회/적용/토글, `localStorage` 저장, `prefers-color-scheme` 폴백
- [x] 4.2 각 페이지 `<head>`에 FOUC 방지용 인라인 스크립트(테마 클래스를 렌더 전에 적용) + `tailwind.config = { darkMode: 'class' }`
- [x] 4.3 5개 화면에 테마 토글 버튼 추가 및 `initThemeToggle()` 연결

## 5. macOS 스타일 리디자인

- [x] 5.1 `frontend/css/theme.css` 작성: glass 카드(`mac-window`), 트래픽라이트 타이틀바, 그라디언트 배경, 그레인 텍스처, Fraunces 로고 폰트, 버튼/인풋 스타일
- [x] 5.2 `login.html`, `signup.html`, `team-select.html` mac 스타일로 재구성
- [x] 5.3 `app.html`: 헤더/네비/칸반/채팅/멤버/모달/확인창 전체를 glass-panel + mac-window로 재구성 (기존 id/class 셀렉터 유지)
- [x] 5.4 `frontend/js/app.js`: 활성 탭/필터/상태버튼 색상을 신규 accent(#0a84ff)로 교체, 칸반 카드·채팅 말풍선·멤버 아바타에 다크모드 클래스 추가

## 6. 검증

- [x] 6.1 로컬에서 로그인/자동로그인/다크모드 토글/칸반/채팅/멤버 화면 브라우저(Playwright) 검증
- [x] 6.2 커밋 후 `vercel deploy --prod` 재배포, 프로덕션에서 정적 자산(`css/theme.css`, `js/theme.js`) 및 화면 정상 서빙 확인
