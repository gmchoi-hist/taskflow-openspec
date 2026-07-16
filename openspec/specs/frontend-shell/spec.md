## Purpose

로그인 세션 지속 방식(로그인 상태 유지), 자동 로그인 라우팅, 라이트/다크 테마 선택 및 지속을 담당하는 프론트엔드 공용 셸 기능.

## Requirements


### Requirement: 세션 지속 방식 선택
시스템은(SHALL) 로그인 화면에서 "로그인 상태 유지" 체크박스를 통해 JWT 저장 방식을 선택할 수 있게 해야 한다. 체크된 경우 `localStorage`(브라우저 재시작 후에도 유지), 체크 해제된 경우 `sessionStorage`(탭/창 종료 시 소멸)에 저장해야 한다.

#### Scenario: 로그인 상태 유지 체크
- **WHEN** 사용자가 "로그인 상태 유지"를 체크한 채로 로그인에 성공하면
- **THEN** 시스템은 JWT를 `localStorage`에 저장하고, 브라우저를 재시작해도 로그인 상태가 유지된다

#### Scenario: 로그인 상태 유지 체크 해제
- **WHEN** 사용자가 "로그인 상태 유지"를 체크 해제한 채로 로그인에 성공하면
- **THEN** 시스템은 JWT를 `sessionStorage`에만 저장하고, 해당 탭/창을 닫으면 로그인 상태가 사라진다

### Requirement: 자동 로그인
시스템은(SHALL) 유효한 JWT가 이미 저장되어 있는 상태로 `/`, `/login.html`, `/signup.html`에 접근하면 로그인/회원가입 폼을 보여주지 않고, 사용자의 `team_id` 유무에 따라 `/app.html` 또는 `/team-select.html`로 즉시 이동시켜야 한다.

#### Scenario: 유효한 토큰으로 로그인 화면 접근
- **WHEN** 유효한 JWT를 가진 사용자가 `/login.html`에 접근하면
- **THEN** 시스템은 `GET /auth/me`로 토큰을 검증하고, `team_id`가 있으면 `/app.html`로, 없으면 `/team-select.html`로 리다이렉트한다

#### Scenario: 만료되었거나 없는 토큰으로 접근
- **WHEN** 토큰이 없거나 만료된 사용자가 `/login.html`, `/signup.html`, 또는 `/`에 접근하면
- **THEN** 시스템은 리다이렉트 없이 원래 화면(로그인 폼 또는 `/login.html`)을 그대로 보여준다

### Requirement: 테마 선택 및 지속
시스템은(SHALL) 라이트/다크 테마를 토글할 수 있는 버튼을 모든 화면에 제공하고, 선택된 테마를 `localStorage`에 저장해 페이지 이동 간에도 유지해야 한다. 저장된 값이 없는 최초 방문 시에는 시스템의 `prefers-color-scheme` 설정을 따라야 한다.

#### Scenario: 테마 토글
- **WHEN** 사용자가 테마 토글 버튼을 클릭하면
- **THEN** 시스템은 현재 테마의 반대 값을 `localStorage`에 저장하고 화면 전체에 즉시 적용한다

#### Scenario: 저장된 테마 없이 재방문
- **WHEN** `localStorage`에 저장된 테마 값이 없는 사용자가 페이지를 방문하면
- **THEN** 시스템은 브라우저의 `prefers-color-scheme` 값(dark/light)을 기본 테마로 적용한다

#### Scenario: 페이지 이동 간 테마 유지
- **WHEN** 사용자가 다크 테마를 선택한 상태로 다른 화면(예: 로그인 → 칸반)으로 이동하면
- **THEN** 이동한 화면도 동일하게 다크 테마로 렌더링된다
