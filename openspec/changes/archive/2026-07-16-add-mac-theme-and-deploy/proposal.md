## Why

`add-mvp-core` 구현까지는 완료됐지만 실제 배포된 서비스가 없었고, 기본 Tailwind 스타일은 밋밋해서 사용자가 매번 로그인 폼을 다시 마주해야 했다. Vercel/Neon으로 실제 배포하고, 재방문 시 다시 로그인하지 않아도 되게 하고, 화면을 macOS 감성의 완성도 있는 디자인으로 바꿔 제품처럼 보이게 한다.

## What Changes

- FastAPI 백엔드를 Vercel Python Serverless Function으로, 프론트엔드를 정적 파일로 배포(`vercel.json`, `api/index.py`)
- Vercel Marketplace 통합으로 Neon Postgres를 프로비저닝하고 `DATABASE_URL`을 자동 주입, `postgres://` 스킴을 SQLAlchemy용으로 정규화
- 배포 도메인 루트(`/`) 404를 해결하는 `frontend/index.html` 라우팅 페이지 추가
- 로그인 상태 유지 체크박스 추가: 체크 시 `localStorage`(브라우저 재시작 후에도 유지), 해제 시 `sessionStorage`(탭/창 종료 시 로그아웃)에 JWT 저장
- 자동 로그인: 유효한 토큰이 있으면 로그인/회원가입 화면 대신 팀 상태에 맞는 화면(`/app.html` 또는 `/team-select.html`)으로 즉시 이동
- 라이트/다크 모드 토글 추가, 선택값은 `localStorage`에 저장되어 페이지 간 유지, 최초 방문 시 시스템 선호도(`prefers-color-scheme`)를 따름
- 5개 화면(로그인/회원가입/팀선택/앱/인덱스) 전체를 macOS 스타일(프로스티드 글라스 카드, 트래픽라이트 타이틀바, 그라디언트 배경, Fraunces 로고 폰트)로 재구성
- **BREAKING**: 없음 (기존 API 계약 변경 없음, 프론트엔드 시각/UX만 변경)

## Capabilities

### New Capabilities
- `frontend-shell`: 테마(라이트/다크) 선택 및 지속, 세션 지속 방식(로그인 상태 유지 체크박스) 선택, 유효 세션 보유 시 자동 로그인 라우팅

### Modified Capabilities
(없음 — 기존 `user-auth`/`team-management`/`kanban-board`/`team-chat`의 API 계약은 변경되지 않음)

## Impact

- **Frontend**: `frontend/` 5개 HTML 전체, 신규 `frontend/css/theme.css`·`frontend/js/theme.js`, `frontend/js/api.js`(토큰 저장 방식), `frontend/js/app.js`(색상 팔레트만 변경)
- **Backend**: `backend/database.py`(postgres:// 정규화), `backend/main.py`(Vercel 환경에서 StaticFiles 마운트 생략), `backend/requirements.txt`(psycopg2-binary 추가)
- **배포**: `vercel.json`, `api/index.py` 신규. Vercel 프로젝트 `gmchoi-s-projects/taskflow-openspec`, Neon Postgres 통합, 프로덕션 URL `https://taskflow-openspec-ochre.vercel.app`
- **DB**: 로컬 SQLite는 변경 없음, 운영은 Neon Postgres로 전환 완료(기존에는 미배포 상태)
