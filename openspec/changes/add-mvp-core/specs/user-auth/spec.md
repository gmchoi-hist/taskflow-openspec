## ADDED Requirements

### Requirement: 회원가입
시스템은(SHALL) `POST /auth/signup`을 통해 이메일과 비밀번호로 신규 사용자를 등록할 수 있게 해야 한다. 비밀번호는 저장 전 bcrypt로 해시해야 하며, 평문 비밀번호는 절대 저장하지 않아야 한다. 성공 시 HTTP 201과 JWT를 반환해야 한다.

#### Scenario: 회원가입 성공
- **WHEN** 클라이언트가 유효한 이메일과 8자 이상의 비밀번호로 `POST /auth/signup`을 호출하면
- **THEN** 시스템은 bcrypt로 해시된 비밀번호와 함께 `users` 레코드를 생성하고, HTTP 201과 JWT, 생성된 사용자 정보(id, email, team_id=null)를 반환한다

#### Scenario: 이메일 중복
- **WHEN** 클라이언트가 이미 `users`에 존재하는 이메일로 `POST /auth/signup`을 호출하면
- **THEN** 시스템은 HTTP 409와 `{ error: { code: "EMAIL_TAKEN", message: "이미 가입된 이메일입니다" } }`를 반환한다

#### Scenario: 이메일 형식 오류
- **WHEN** 클라이언트가 올바르지 않은 형식의 이메일로 `POST /auth/signup`을 호출하면
- **THEN** 시스템은 HTTP 400과 `{ error: { code: "VALIDATION_ERROR", ... } }`를 반환한다

#### Scenario: 비밀번호 길이 미달
- **WHEN** 클라이언트가 8자 미만의 비밀번호로 `POST /auth/signup`을 호출하면
- **THEN** 시스템은 HTTP 400과 `{ error: { code: "VALIDATION_ERROR", ... } }`를 반환한다

### Requirement: 로그인
시스템은(SHALL) `POST /auth/login`을 통해 이메일과 비밀번호로 사용자를 인증하고, 24시간 유효한 JWT를 발급해야 한다. 인증 실패 시 해당 이메일의 존재 여부를 노출하지 않아야 한다.

#### Scenario: 로그인 성공
- **WHEN** 클라이언트가 올바른 이메일과 비밀번호로 `POST /auth/login`을 호출하면
- **THEN** 시스템은 HTTP 200과 JWT(24시간 유효), `team_id`를 포함한 사용자 정보를 반환한다

#### Scenario: 자격 증명 오류
- **WHEN** 클라이언트가 잘못된 비밀번호 또는 존재하지 않는 이메일로 `POST /auth/login`을 호출하면
- **THEN** 시스템은 두 경우 모두 동일하게 HTTP 401과 `{ error: { code: "INVALID_CREDENTIALS", message: "이메일 또는 비밀번호가 일치하지 않습니다" } }`를 반환하며, 어느 필드가 잘못되었는지 드러내지 않는다

### Requirement: 현재 사용자 조회
시스템은(SHALL) 유효한 JWT가 제공될 때 `GET /auth/me`를 통해 인증된 사용자의 프로필을 반환해야 한다.

#### Scenario: 유효한 토큰
- **WHEN** 클라이언트가 만료되지 않은 유효한 JWT를 Authorization 헤더에 담아 `GET /auth/me`를 호출하면
- **THEN** 시스템은 HTTP 200과 사용자의 id, email, team_id를 반환한다

#### Scenario: 토큰 누락 또는 만료
- **WHEN** 클라이언트가 JWT 없이 또는 만료된 JWT로 `GET /auth/me`를 호출하면
- **THEN** 시스템은 HTTP 401과 `{ error: { code: "TOKEN_EXPIRED", message: "인증이 만료되었습니다" } }`를 반환한다

### Requirement: Stateless 로그아웃
시스템은(SHALL) 서버 측 토큰 블랙리스트를 유지하지 않고 HTTP 200만 반환하는 `POST /auth/logout`을 제공해야 한다. JWT 폐기는 클라이언트의 책임이다.

#### Scenario: 로그아웃 호출
- **WHEN** 클라이언트가 유효한 JWT로 `POST /auth/logout`을 호출하면
- **THEN** 시스템은 빈 본문과 함께 HTTP 200을 반환하며, 해당 JWT는 24시간 만료 시점까지 서버 측에서 여전히 기술적으로 유효한 상태로 남는다(폐기 처리 없음)

### Requirement: JWT 만료 검증
시스템은(SHALL) 만료되었거나 형식이 올바르지 않은 JWT로 보호된 엔드포인트에 접근하는 모든 요청을 거부하고 HTTP 401을 반환해야 한다.

#### Scenario: 보호된 라우트에서의 만료된 JWT
- **WHEN** 클라이언트가 `exp`가 지난 JWT로 보호된 엔드포인트(예: `GET /teams/{id}/tasks`)를 호출하면
- **THEN** 시스템은 HTTP 401과 `{ error: { code: "TOKEN_EXPIRED", ... } }`를 반환한다
