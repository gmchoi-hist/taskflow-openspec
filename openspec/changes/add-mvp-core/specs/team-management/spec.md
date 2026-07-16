## ADDED Requirements

### Requirement: 팀 생성
시스템은(SHALL) 팀이 없는(`team_id = NULL`) 인증된 사용자가 `POST /teams`를 통해 팀을 생성할 수 있게 해야 한다. 시스템은 `^[A-Z]{4}-[0-9]{4}$` 형식의 고유한 초대코드를 자동 생성하고, 생성자를 `owner_id`로 지정하며, 생성자의 `team_id`를 새 팀으로 업데이트해야 한다.

#### Scenario: 팀 생성 성공
- **WHEN** `team_id = NULL`인 인증된 사용자가 이름(1-30자)과 함께 `POST /teams`를 호출하면
- **THEN** 시스템은 자동 생성된 `invite_code`를 가진 `teams` 레코드를 만들고, `owner_id`를 호출자로 설정하고, 호출자의 `users.team_id`를 업데이트하고, HTTP 201과 팀 정보(id, name, invite_code, owner_id, created_at)를 반환한다

### Requirement: 초대코드로 팀 합류
시스템은(SHALL) 팀이 없는 인증된 사용자가 유효한 초대코드로 `POST /teams/join`을 호출해 기존 팀에 합류하고 `users.team_id`를 업데이트할 수 있게 해야 한다.

#### Scenario: 합류 성공
- **WHEN** `team_id = NULL`인 사용자가 유효하고 존재하는 초대코드로 `POST /teams/join`을 호출하면
- **THEN** 시스템은 매칭된 팀의 id로 `users.team_id`를 설정하고, HTTP 200과 팀 정보 및 이동 대상(redirect)을 반환한다

#### Scenario: 초대코드 형식 오류
- **WHEN** 사용자가 `^[A-Z]{4}-[0-9]{4}$` 형식에 맞지 않는 코드로 `POST /teams/join`을 호출하면
- **THEN** 시스템은 HTTP 400과 `{ error: { code: "VALIDATION_ERROR", ... } }`를 반환한다

#### Scenario: 초대코드 미존재
- **WHEN** 사용자가 형식은 올바르지만 존재하지 않는 초대코드로 `POST /teams/join`을 호출하면
- **THEN** 시스템은 HTTP 404와 `{ error: { code: "NOT_FOUND", message: "해당 초대코드를 찾을 수 없습니다" } }`를 반환한다

#### Scenario: 이미 다른 팀에 소속됨
- **WHEN** `team_id`가 null이 아닌 사용자가 `POST /teams/join`을 호출하면
- **THEN** 시스템은 HTTP 409와 `{ error: { code: "ALREADY_IN_TEAM", message: "이미 다른 팀에 소속되어 있습니다" } }`를 반환한다

### Requirement: 팀 정보 조회
시스템은(SHALL) `GET /teams/{id}`를 통해 해당 팀의 멤버에게만 팀 상세 정보를 반환해야 한다.

#### Scenario: 멤버의 팀 정보 조회
- **WHEN** 팀 `{id}`의 멤버가 `GET /teams/{id}`를 호출하면
- **THEN** 시스템은 HTTP 200과 팀의 name, invite_code, owner_id, member_count를 반환한다

#### Scenario: 비멤버의 팀 정보 조회 시도
- **WHEN** `team_id`가 `{id}`와 다르거나(또는 null인) 사용자가 `GET /teams/{id}`를 호출하면
- **THEN** 시스템은 HTTP 403과 `{ error: { code: "FORBIDDEN", message: "이 팀의 멤버가 아닙니다" } }`를 반환한다

### Requirement: 팀 멤버십 접근 제어
시스템은(SHALL) 모든 `/teams/{id}/*` 라우트(태스크, 메시지, 멤버)를 `team_id`가 `{id}`와 일치하는 사용자로만 제한해야 한다. 다른 팀 소속 인증 사용자를 포함한 그 외 모든 사용자는 HTTP 403을 받아야 한다.

#### Scenario: 비멤버가 다른 팀의 리소스에 접근
- **WHEN** 사용자 A(team_id=1)가 `GET /teams/2/tasks`, `GET /teams/2/messages`, `GET /teams/2/members`를 호출하면
- **THEN** 시스템은 각 요청에 대해 HTTP 403과 `{ error: { code: "FORBIDDEN", ... } }`를 반환한다

### Requirement: 팀 멤버 목록
시스템은(SHALL) `GET /teams/{id}/members`를 통해 각 멤버의 이메일과 owner 여부를 포함한 팀 멤버 목록을 반환해야 한다.

#### Scenario: 멤버 목록 조회
- **WHEN** 팀 `{id}`의 멤버가 `GET /teams/{id}/members`를 호출하면
- **THEN** 시스템은 HTTP 200과 해당 팀에 속한 사용자 배열을 반환하며, `owner_id`와 일치하는 사용자를 owner로 표시한다

### Requirement: 팀 탈퇴
시스템은(SHALL) owner가 아닌 멤버가 `DELETE /teams/{id}/leave`를 통해 팀을 탈퇴하고 `users.team_id`를 `NULL`로 설정할 수 있게 해야 한다. owner의 탈퇴는 차단해야 한다.

#### Scenario: 멤버의 팀 탈퇴
- **WHEN** 팀 `{id}`의 owner가 아닌 멤버가 `DELETE /teams/{id}/leave`를 호출하면
- **THEN** 시스템은 호출자의 `users.team_id`를 `NULL`로 설정하고 HTTP 200을 반환한다

#### Scenario: owner의 탈퇴 시도
- **WHEN** 팀의 owner가 `DELETE /teams/{id}/leave`를 호출하면
- **THEN** 시스템은 HTTP 403과 `{ error: { code: "OWNER_CANNOT_LEAVE", message: "팀 소유자는 탈퇴할 수 없습니다" } }`를 반환하며 `team_id`를 변경하지 않는다
