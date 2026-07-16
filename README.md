# TaskFlow MVP

소규모 팀(3-5인)이 칸반 + 실시간(폴링) 채팅으로 업무 진행을 한 화면에서 추적하는 MVP입니다.

기획·스펙은 [`docs/TaskFlow_프로그램정의.pdf`](docs/TaskFlow_프로그램정의.pdf), [`docs/TaskFlow_스토리보드.pdf`](docs/TaskFlow_스토리보드.pdf)를 기반으로 [OpenSpec](https://github.com/Fission-AI/OpenSpec)의 `add-mvp-core` change로 정리했고, 구현 완료 후 `openspec/changes/archive/2026-07-16-add-mvp-core/`로 아카이브했습니다. 확정된 스펙은 `openspec/specs/{user-auth,team-management,kanban-board,team-chat}/spec.md`에 있습니다.

## 기술 스택

- **Backend**: FastAPI + SQLAlchemy (로컬 SQLite / 운영 Neon Postgres, `DATABASE_URL`로 전환)
- **Frontend**: Vanilla JS + Tailwind CSS (CDN), 프레임워크 없음
- **Auth**: JWT(24h, 갱신 없음) + bcrypt
- **배포**: Vercel (FE+BE) + Vercel Storage(Neon) — https://taskflow-umber-seven.vercel.app

## 기능

1. **인증** — 회원가입, 로그인, JWT 발급, stateless 로그아웃
2. **팀 관리** — 팀 생성 + 초대코드 발급, 초대코드로 합류, 멤버 목록, 팀 탈퇴(member만; owner는 차단)
3. **칸반** — TODO/DOING/DONE 3컬럼, 생성/상태변경(드래그)/수정/삭제, 담당자 필터(전체/@me/미할당)
4. **채팅** — 팀 단위 메시지, 5초 고정 폴링(`since=`), 1000자 제한, 본인 메시지만 삭제

Out of Scope: 알림, 파일 첨부, 전문 검색, 세분화된 권한, 다국어, WebSocket, 자동화 테스트, 팀 삭제/오너 승계. (자세한 내용은 `openspec/changes/add-mvp-core/proposal.md` 참고)

## 로컬 실행

```bash
cd backend
python -m venv .venv
./.venv/Scripts/activate   # Windows
pip install -r requirements.txt
uvicorn main:app --reload
```

기본 포트(8000)가 사용 중이면 `--port` 옵션으로 바꿀 수 있습니다:

```bash
uvicorn main:app --reload --port 8010
```

서버가 뜨면 프론트엔드는 백엔드가 정적 파일로 같은 origin에 서빙합니다:

- 로그인: `http://127.0.0.1:8010/login.html`
- 회원가입: `http://127.0.0.1:8010/signup.html`
- API 문서(Swagger): `http://127.0.0.1:8010/docs`

로컬 DB는 `backend/taskflow.db` (SQLite, git에서 제외됨)에 생성됩니다.

## 환경 변수

| 변수 | 기본값 | 설명 |
|---|---|---|
| `DATABASE_URL` | `sqlite:///./taskflow.db` | 운영에서는 Neon Postgres 연결 문자열로 교체 |
| `JWT_SECRET` | `dev-secret-change-me` | 운영 배포 전 반드시 교체 |
| `CORS_ORIGINS` | 로컬 개발 origin들 | 배포 도메인 추가 시 쉼표로 구분해 설정 |

## 프로젝트 구조

```
backend/            FastAPI 앱 (main.py, models.py, routers/, ...)
frontend/           Vanilla JS + Tailwind 화면 9종
openspec/           OpenSpec 스펙 (proposal/design/specs/tasks)
docs/                기획 PDF 2종 + 수동 검증 결과(docx, 스크린샷)
```

## 배포

- **Production**: https://taskflow-umber-seven.vercel.app
- FE는 `frontend/`를 정적 파일로, BE는 `api/index.py`(→ `backend/main.py`)를 Python Serverless Function으로 배포 (`vercel.json` 참고)
- DB는 Vercel Marketplace의 Neon 통합(`vercel integration add neon`)으로 자동 프로비저닝, `DATABASE_URL`이 프로젝트에 자동 주입됨

## 진행 상태

`openspec/changes/archive/2026-07-16-add-mvp-core/tasks.md` 기준 44개 작업 전부 완료. 백엔드 API 18개 + 프론트엔드 9화면 구현·로컬 수동 검증·Vercel+Neon 프로덕션 배포·배포 후 스모크 테스트(브라우저 자동화 + curl)까지 완료했습니다.

수동 검증 결과는 [`docs/TaskFlow_MVP_테스트결과.docx`](docs/TaskFlow_MVP_테스트결과.docx)에서 화면 캡처와 함께 확인할 수 있습니다.
