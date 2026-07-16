## Why

소규모 팀(3-5인)이 업무 진행 상황을 칸반으로 추적하고 짧은 채팅으로 빠르게 합의하는 도구가 필요하다. 별도 알림·파일·검색·실시간 인프라 없이 인증부터 배포까지 최소 기능으로 Day 2 안에 동작하는 MVP를 만든다.

## What Changes

- 이메일+비밀번호 회원가입/로그인, JWT 발급(24h, 갱신 없음), bcrypt 해시, stateless 로그아웃 추가
- 팀 생성 + 초대코드(`AAAA-9999` 형식) 발급, 초대코드로 합류, 멤버 목록 조회 추가
- 1인 1팀 가정에 따라 "내 팀 목록" API 대신 팀 탈퇴(`DELETE /teams/{id}/leave`) 추가 — member만 탈퇴 가능, owner는 403 `OWNER_CANNOT_LEAVE`로 차단 (결정 #9)
- TODO/DOING/DONE 3컬럼 칸반: 태스크 생성/조회/상태 이동(PATCH)/제목 수정(PUT)/삭제, `assignee_id`(nullable) 기반 "내 태스크"/미할당 필터 추가
- 팀 단위 채팅: 메시지 송수신, `since=` 파라미터 기반 5초 고정 폴링, 1000자 제한(클라+서버 양쪽 검증), 본인 메시지만 삭제 가능. 모바일에서도 동일한 5초 고정 폴링을 유지하며 exponential backoff 재연결이나 2초 동적 폴링 같은 추가 복잡도는 넣지 않음 (결정 #10)
- 로컬은 FastAPI + SQLite, 배포는 Vercel(FE+BE) + Neon(Postgres)으로 전환되는 배포 파이프라인 추가
- 모든 API 에러 응답을 `{ error: { code, message } }` 형식으로 표준화
- **BREAKING**: 없음 (신규 프로젝트, 기존 스펙 없음)

## Capabilities

### New Capabilities
- `user-auth`: 회원가입, 로그인, JWT 발급/검증, 비밀번호 해시, stateless 로그아웃
- `team-management`: 팀 생성, 초대코드 발급/합류, 멤버 목록, 팀 탈퇴(member만), 팀 단위 접근 권한(비멤버 403)
- `kanban-board`: TODO/DOING/DONE 태스크 생성/조회/상태변경/수정/삭제, assignee 기반 필터
- `team-chat`: 팀 단위 메시지 송수신, 5초 고정 폴링(`since=`), 1000자 제한, 본인 메시지 삭제

### Modified Capabilities
(없음 — 신규 프로젝트, 기존 스펙 없음)

## Impact

- **Backend**: FastAPI 신규 프로젝트, API 18개(Auth 4 + Team 5 + Task 6 + Chat 3), JWT 미들웨어, 권한 검증 미들웨어, SQLAlchemy 기반 4테이블(users/teams/tasks/messages)
- **Frontend**: Vanilla JS + Tailwind, 9개 화면(회원가입/로그인/팀선택/칸반/채팅/멤버/모바일 변형), localStorage 기반 JWT 관리
- **DB**: 로컬 SQLite 파일 ↔ 운영 Neon Postgres, `DATABASE_URL` 환경변수로 전환
- **배포**: Vercel(FE+BE 동시 배포) + Vercel Storage(Neon) 연동
- **Out of Scope**: 알림, 파일 첨부, 전문 검색, 세분화된 권한, 다국어, WebSocket, 자동화 테스트, 팀 삭제/오너 승계
