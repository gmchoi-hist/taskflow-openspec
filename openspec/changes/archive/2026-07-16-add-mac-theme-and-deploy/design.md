## Context

`add-mvp-core`가 아카이브된 시점에는 로컬 검증만 끝난 상태였고 실제 배포는 없었다. Vercel CLI/MCP, Neon MCP를 이 세션에서 처음 인증했고, 프론트엔드는 Tailwind 기본 클래스만 쓴 밋밋한 화면이었다.

## Goals / Non-Goals

**Goals:**
- FastAPI + Vanilla JS 앱을 Vercel(FE 정적 + BE Python Serverless) + Neon(Postgres)으로 배포
- 배포 도메인 루트 404 제거
- 유효 세션이 있으면 로그인 화면을 다시 보여주지 않음(자동 로그인), 세션 지속 여부를 사용자가 선택(로그인 상태 유지 체크박스)
- 라이트/다크 모드와 macOS 스타일 비주얼 리디자인

**Non-Goals:**
- 커스텀 도메인 연결 (사용자가 별도 도메인 구매를 취소함, `.vercel.app` 기본 도메인 유지)
- 백엔드 API 계약 변경 (엔드포인트/응답 스키마는 `add-mvp-core`와 동일)
- OAuth/소셜 로그인, 리프레시 토큰 등 인증 방식 자체의 변경

## Decisions

1. **Vercel Python 배포는 `api/index.py`가 `backend/main.py`의 FastAPI `app`을 재노출하는 얇은 진입점 방식** — Vercel의 Python 런타임이 `app`이라는 이름의 ASGI 앱을 자동 인식하는 컨벤션에 맞춤. `backend/`를 그대로 두고 `sys.path`에 추가하는 방식을 택해 로컬 실행 코드와 배포 코드를 분리하지 않았다.
2. **로컬 전용 `StaticFiles` 마운트는 `os.environ.get("VERCEL")`로 조건부 처리** — Vercel에서는 `frontend/`가 `vercel.json`의 별도 정적 빌드로 서빙되므로 FastAPI가 다시 마운트할 필요가 없다. 환경변수 하나로 분기해 코드 중복을 피했다.
3. **DB는 Vercel Marketplace의 Neon 통합(`vercel integration add neon`)으로 자동 프로비저닝** — 별도로 Neon 콘솔에서 수동 생성 후 연결 문자열을 복사하는 것보다 빠르고, `DATABASE_URL`이 Production/Preview/Development에 자동 주입됨. `postgres://` 스킴은 SQLAlchemy/psycopg2 호환을 위해 `postgresql://`로 런타임에 치환한다.
4. **루트 경로 404는 `frontend/index.html`을 추가해 해결** — 별도 서버 리다이렉트(vercel.json rewrite)가 아니라 클라이언트 스크립트로 토큰 유무를 검사해 라우팅했다. 이렇게 하면 로그인 여부에 따른 분기 로직을 서버가 아닌 프론트 한 곳(`autoLoginRedirectIfPossible`)에 모을 수 있다.
5. **세션 지속 방식은 storage 종류로 표현** — "로그인 상태 유지" 체크 시 `localStorage`(브라우저 재시작 후에도 유지), 체크 해제 시 `sessionStorage`(탭/창 종료 시 소멸)에 JWT를 저장. 별도의 서버 세션이나 리프레시 토큰 없이, 기존 24h 만료 JWT를 어디에 두느냐만으로 "이 기기에서 계속 로그인 유지" 여부를 구현했다.
6. **자동 로그인은 모든 진입 페이지(index/login/signup)에서 공통 헬퍼(`autoLoginRedirectIfPossible`)를 호출** — 토큰이 있으면 `GET /auth/me`로 유효성을 확인하고 `team_id` 유무에 따라 `/app.html` 또는 `/team-select.html`로 보낸다. 토큰이 없거나 만료됐으면 원래 폼을 그대로 보여준다.
7. **디자인은 mac 스타일이되 기존 컴포넌트의 id/class 구조는 최대한 보존** — `app.js`의 DOM 선택자를 하나도 바꾸지 않고 시각적 클래스만 교체해, 기능 회귀 위험을 최소화했다. 커스텀 CSS(`theme.css`)는 Tailwind CDN만으로 표현하기 어려운 것(글래스모피즘, 그레인 텍스처, 트래픽라이트 점, keyframe 애니메이션)에만 사용했다.

## Risks / Trade-offs

- **[Risk] Neon 무료 플랜의 scale-to-zero로 인한 콜드 스타트 지연** → **Mitigation**: MVP 트래픽 규모에서는 수용 가능한 수준으로 판단, 필요 시 Neon 오토스케일링 설정으로 완화 가능(범위 외로 보류).
- **[Risk] `sessionStorage` 선택 시 여러 탭에서 로그인 상태가 공유되지 않음(탭마다 별도)** → **Mitigation**: 의도된 동작으로 명시(체크박스 설명에 "이 브라우저"가 아닌 "이 탭/창" 기준임을 향후 UI 카피에 반영할 여지 있음, 현재는 기능적으로만 구현).
- **[Trade-off] 커스텀 도메인 미연결** → `.vercel.app` 기본 도메인 유지. 사용자가 실제 결제가 필요한 도메인 구매를 취소했기 때문이며, 필요 시 언제든 재시도 가능.
- **[Trade-off] mac 스타일 CSS가 Tailwind CDN 런타임 컴파일과 별도의 정적 CSS 파일로 나뉨** → 빌드 스텝 없는 Vanilla JS 프로젝트 특성상 불가피. 두 스타일 시스템(Tailwind 유틸리티 + theme.css 커스텀 클래스)이 공존하지만, 커스텀 클래스는 Tailwind로 표현 불가능한 것에 한정해 충돌을 최소화했다.

## Migration Plan

1. `vercel link`로 프로젝트 연결 → `vercel integration add neon`으로 DB 프로비저닝 → `vercel deploy --prod`로 최초 배포
2. 루트 404 발견 → `frontend/index.html` 추가 → 재배포로 즉시 해결
3. 프론트엔드 리디자인은 정적 파일 교체만으로 이루어지므로 별도 마이그레이션 없이 `vercel deploy --prod` 재배포로 반영
4. 롤백: Vercel 대시보드/CLI에서 이전 배포로 즉시 alias 전환 가능(플랫폼 기본 기능), DB 스키마 변경 없었으므로 DB 롤백 불필요
