## Context

TaskFlow MVP는 신규 프로젝트로, 기존 스펙/코드가 없다. 입력 자료는 `docs/TaskFlow_프로그램정의.pdf`(미션·페르소나·기능5종·DB4테이블·API18개·ACME·비기능요구사항·Out of Scope 7종)와 `docs/TaskFlow_스토리보드.pdf`(화면 상태·에러 케이스·결정추적표 8건 + explore 단계에서 추가한 결정 #9, #10)다. 제약: Day 2 안에 완성, 팀당 5명 이하·동시 50명 이하, 한국어 UI만, 자동화 테스트 없음, print 디버깅만.

## Goals / Non-Goals

**Goals:**
- 인증 → 팀 → 칸반 → 채팅으로 이어지는 4개 캡슬리티(`user-auth`, `team-management`, `kanban-board`, `team-chat`)를 API 18개, DB 4테이블로 구현
- 로컬 SQLite와 운영 Neon(Postgres)을 `DATABASE_URL` 하나로 전환 가능하게 함
- 모든 에러 응답을 `{ error: { code, message } }`로 표준화

**Non-Goals:**
- 알림(이메일/SMS/푸시), 파일 첨부, 전문 검색, 세분화된 권한(admin/member 이상), 다국어, WebSocket 실시간, 자동화 테스트
- 팀 삭제, 오너 승계, 초대코드 재발급
- JWT 갱신 토큰, 로그인 실패 cooldown, 관측성 도구(Sentry 등)

## Decisions

1. **1인 1팀, `users.team_id` nullable FK** — 별도 멤버십 테이블 대신 `users.team_id`로 단순화. `team_id = NULL`이면 팀 선택 화면으로 강제 이동. (스토리보드 결정 #1)
2. **`tasks.assignee_id` nullable FK, `creator_id`와 분리** — "내 태스크" = `assignee_id = current_user_id`. creator는 카드 생성자일 뿐 담당자가 아닐 수 있음. (결정 #4)
3. **상태 변경은 `PATCH /tasks/{id}/status`, 제목 수정은 `PUT /tasks/{id}`로 분리** — 두 동작이 같은 path를 공유하던 원본 설계의 모호함 해소. 드래그(상태변경)와 폼 수정(제목)의 실패 모드가 다르므로 분리. (결정 #3)
4. **`DELETE /teams/{id}/leave`: member만 허용, owner는 403** — "팀 목록" API를 없애는 대신 넣은 신규 엔드포인트. owner 탈퇴를 허용하면 고아 팀(누구도 owner가 아닌 팀) 상태가 생기는데, 팀 삭제·오너 승계가 Non-Goal이라 이 상태를 처리할 방법이 없다. 그래서 owner 탈퇴 자체를 막는다. (결정 #9)
5. **채팅 폴링은 5초 고정, 재연결 backoff 없음** — 모바일에서 폴링 주기를 동적으로 바꾸거나(2초) exponential backoff를 넣는 대안을 검토했으나, 비기능요구사항의 "5초 폴링" 제약 및 "관측성 최소화" 원칙과 충돌해 폐기. 실패 시 고정 5초 재시도 + 단순 배지 표시만 한다. (결정 #10)
6. **로그아웃은 stateless** — JWT 블랙리스트 서버 상태를 두지 않음. `POST /auth/logout`은 200만 반환하고 클라이언트가 `localStorage`에서 토큰을 지운다. 토큰은 만료(24h) 전까지 여전히 유효함을 감수한다. (결정 #5)
7. **DELETE 권한: `tasks`는 creator 또는 team owner, `messages`는 본인만(owner도 예외 없음)** — 태스크는 팀 운영 관점(owner가 정리 가능)이 필요하지만, 채팅은 개인 발언이라 owner도 타인 메시지를 지울 수 없게 해 신뢰 모델을 일관되게 유지. (결정 #6)
8. **기술 스택은 고정, 세부 구현은 위임** — Backend: FastAPI + SQLAlchemy + bcrypt + python-jose(또는 동급) 자유 선택. Frontend: Vanilla JS + Tailwind, 프레임워크 없음. 파일 구조·라우팅 방식·CSS 빌드 방식은 구현 단계에서 결정.
9. **성능/검증 지표는 정성 검증으로 명시** — 칸반 드래그 반응 50ms, 신규 합류자 1분 파악 등은 자동 측정 도구 없이 수동 확인으로 검증. 자동화 테스트 Non-Goal과 일치. (결정 #7)

## Risks / Trade-offs

- **[Risk] JWT 24h + 갱신 없음** → 세션이 길게 유지되어 탈취 시 위험 창이 큼. **Mitigation**: MVP 범위로 명시적으로 감수(Non-Goal), 프로덕션화 시 리프레시 토큰 도입 필요.
- **[Risk] owner가 유일한 멤버인 팀에서 탈퇴를 원할 경우 막혀서 오도 가도 못함** → **Mitigation**: 팀 삭제/승계는 Non-Goal이므로 UI에서 "owner는 탈퇴할 수 없습니다" 안내만 하고 실제 처리는 차기 스코프로 미룸.
- **[Risk] 5초 고정 폴링은 네트워크 불안정 환경에서 사용자가 지연을 느낄 수 있음** → **Mitigation**: MVP 수용 범위로 명시. 필요 시 차기 스코프에서 WebSocket 검토(현재 Non-Goal).
- **[Risk] 로컬 SQLite ↔ 운영 Neon 전환 시 타입/방언 차이(예: BOOLEAN, TIMESTAMP)로 미묘한 버그 발생 가능** → **Mitigation**: SQLAlchemy ORM으로 방언 차이를 흡수하고, 배포 전 Neon에서 마이그레이션 1회 수동 검증.
- **[Trade-off] 자동화 테스트 없음** → 회귀 위험이 수동 확인에 의존. Day 2 범위 원칙(단순성)과의 트레이드오프로 의도적으로 수용.

## Migration Plan

1. 로컬 개발: FastAPI + SQLite(`sqlite:///./taskflow.db`)로 API 18개, 화면 9개 구현 및 수동 동작 확인
2. GitHub `main` push → Vercel이 프론트(정적 파일) + 백엔드(Serverless Functions) 동시 배포
3. Vercel Storage에서 Neon(Postgres) 프로비저닝, `DATABASE_URL` 환경변수(Pooled) 자동 주입
4. 배포 후 스모크 테스트: 회원가입 → 팀 생성 → 칸반 카드 생성/이동 → 채팅 전송, 각 1회 수동 확인
5. 롤백: Vercel 이전 배포로 즉시 되돌리기(플랫폼 기본 기능), DB는 Neon point-in-time recovery(Free 플랜 기본) 사용

## Open Questions

- 프론트 파일 구조(SPA vs MPA)와 라우팅 방식은 구현 단계에서 결정 — 구현자가 tasks.md 작성 시 확정
- CORS 허용 도메인 목록(로컬 origin, `*.vercel.app` 등)의 정확한 값은 배포 시점에 확정 필요
