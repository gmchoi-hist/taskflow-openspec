## 1. 프로젝트 셋업

- [x] 1.1 FastAPI 프로젝트 초기화 (로컬 `uvicorn main:app --reload`)
- [x] 1.2 SQLAlchemy 설정: `DATABASE_URL` 환경변수로 로컬 SQLite ↔ 운영 Neon 전환 가능하게 구성
- [x] 1.3 `users`, `teams`, `tasks`, `messages` 4테이블 모델 정의 (team_id nullable FK on users, assignee_id nullable FK on tasks)
- [x] 1.4 표준 에러 응답 헬퍼 구현: `{ error: { code, message, ...meta } }`
- [x] 1.5 CORS 허용 도메인 설정 (로컬 origin + 배포 도메인)

## 2. 인증 (`user-auth`)

- [x] 2.1 `POST /auth/signup`: 이메일 형식·비밀번호 8자 이상 검증, bcrypt 해시, 이메일 중복 시 409 `EMAIL_TAKEN`, 성공 시 201 + JWT
- [x] 2.2 `POST /auth/login`: 자격증명 검증, 실패 시 401 `INVALID_CREDENTIALS`(이메일 존재 여부 노출 안 함), 성공 시 200 + JWT(24h)
- [x] 2.3 `GET /auth/me`: JWT 검증 후 현재 사용자 반환, 만료/누락 시 401 `TOKEN_EXPIRED`
- [x] 2.4 `POST /auth/logout`: stateless, 항상 200 반환 (블랙리스트 없음)
- [x] 2.5 JWT 검증 미들웨어: 모든 보호된 라우트에 적용, 만료 시 401 표준 에러

## 3. 팀 관리 (`team-management`)

- [x] 3.1 `POST /teams`: team_id=NULL인 사용자만 생성 가능, invite_code 자동 생성(`^[A-Z]{4}-[0-9]{4}$`), owner_id=caller, caller.team_id 업데이트
- [x] 3.2 `POST /teams/join`: invite_code 형식(400)/존재(404)/중복소속(409) 검증, 성공 시 caller.team_id 업데이트
- [x] 3.3 `GET /teams/{id}`: 멤버만 조회 가능, 비멤버 403 `FORBIDDEN`
- [x] 3.4 `GET /teams/{id}/members`: 멤버 목록 + owner 표시
- [x] 3.5 `DELETE /teams/{id}/leave`: member는 team_id NULL 처리, owner는 403 `OWNER_CANNOT_LEAVE`
- [x] 3.6 팀 멤버십 검증 미들웨어: 모든 `/teams/{id}/*` 라우트에 적용

## 4. 칸반 (`kanban-board`)

- [x] 4.1 `POST /teams/{id}/tasks`: 제목(1-100자) + 선택적 assignee_id, status=TODO 기본값, creator_id=caller
- [x] 4.2 `GET /teams/{id}/tasks`: 전체/@me(assignee_id=current_user)/미할당(assignee_id IS NULL) 필터, created_at desc 정렬
- [x] 4.3 `GET /tasks/{id}`: 단일 태스크 상세, 비멤버 403
- [x] 4.4 `PUT /tasks/{id}`: 제목/assignee 수정
- [x] 4.5 `PATCH /tasks/{id}/status`: TODO/DOING/DONE 상태 이동
- [x] 4.6 `DELETE /tasks/{id}`: creator 또는 owner만 허용, 그 외 403 `FORBIDDEN`

## 5. 채팅 (`team-chat`)

- [x] 5.1 `POST /teams/{id}/messages`: 1000자 이내 서버측 검증(초과 시 400 `TOO_LONG`), 성공 시 201
- [x] 5.2 `GET /teams/{id}/messages`: `since=` 파라미터로 증분 조회, 미지정 시 최근 50개
- [x] 5.3 `DELETE /messages/{id}`: 본인 메시지만 허용(owner 예외 없음), 그 외 403 `NOT_OWNER`

## 6. 프론트엔드 — 화면 9종

- [x] 6.1 로그인 화면: 이메일/비밀번호 입력, 클라이언트 validation, 에러 표시(401/400)
- [x] 6.2 회원가입 화면: 초기/입력중/처리중 상태, 에러 표시(400/409)
- [x] 6.3 팀 선택 화면: team_id=NULL 강제 진입, 팀 만들기 + 초대코드 합류 폼, 에러 표시(400/404/409)
- [x] 6.4 칸반 화면: 3컬럼(TODO/DOING/DONE), 필터(전체/@me/미할당), 인라인 생성, HTML5 드래그로 PATCH 상태변경, 카드 상세/수정 모달, 삭제 확인 다이얼로그
- [x] 6.5 채팅 화면: 메시지 리스트, 5초 고정 폴링(`setInterval` + `since=`), 1000자 카운터, 본인 메시지 삭제 호버 메뉴
- [x] 6.6 팀 멤버 사이드 패널: 멤버 목록 + owner 표시
- [x] 6.7 모바일 반응형: 칸반 컬럼 스와이프, 채팅 풀스크린, 햄버거 메뉴 (breakpoint 768px) — 폴링 주기는 데스크탑과 동일하게 5초 고정 유지 (동적 단축/backoff 없음)
- [x] 6.8 401 발생 시 공통 처리: localStorage 토큰 삭제 + `/login` redirect (axios/fetch 인터셉터)
- [x] 6.9 403(비멤버 접근) 안내 화면

## 7. 배포

- [x] 7.1 로컬: SQLite 파일 기반 동작 확인 (`git`에서 DB 파일 제외)
- [x] 7.2 Vercel Storage에서 Neon Postgres 프로비저닝, `DATABASE_URL`(Pooled) 자동 주입 확인 (`vercel integration add neon`)
- [x] 7.3 Vercel에 FE(정적 파일) + BE(FastAPI Serverless Functions) 배포 (https://taskflow-openspec-ochre.vercel.app)
- [x] 7.4 운영 CORS 도메인 값 확정 및 적용 (`CORS_ORIGINS`에 배포 도메인 반영)

## 8. 수동 검증 (자동화 테스트 없음, Day 2 범위)

- [x] 8.1 회원가입 → 로그인 → 팀 생성 → 초대코드 합류(신규 계정) 흐름 1회 수동 확인 (브라우저, docs/TaskFlow_MVP_테스트결과.docx)
- [x] 8.2 칸반 카드 생성/드래그 이동/수정/삭제(권한별) 수동 확인 (브라우저 + curl)
- [x] 8.3 채팅 전송/폴링/1000자 초과/본인 아닌 메시지 삭제 시도(403) 수동 확인 (브라우저 + curl)
- [x] 8.4 비멤버가 다른 팀 리소스 접근 시 403 일괄 확인 (curl로 백엔드 API 확인 완료, UI 안내 화면은 6.9에서 별도 확인)
- [x] 8.5 owner의 `/teams/{id}/leave` 시도 시 403 확인
- [x] 8.6 배포된 Vercel URL에서 위 시나리오 스모크 테스트 1회 (Playwright + curl, https://taskflow-openspec-ochre.vercel.app)
