## ADDED Requirements

### Requirement: 메시지 전송
시스템은(SHALL) 팀 멤버가 `POST /teams/{id}/messages`를 통해 최대 1000자의 내용으로 메시지를 게시할 수 있게 해야 한다. 클라이언트가 이미 길이를 검증했더라도 시스템은 서버 측에서도 길이를 검증해야 한다.

#### Scenario: 메시지 전송 성공
- **WHEN** 팀 멤버가 1000자 이하의 내용으로 `POST /teams/{id}/messages`를 호출하면
- **THEN** 시스템은 `messages` 레코드(team_id, user_id=호출자, content, created_at)를 생성하고 HTTP 201을 반환한다

#### Scenario: 메시지 길이 초과
- **WHEN** 팀 멤버가 1000자를 초과하는 내용으로 `POST /teams/{id}/messages`를 호출하면
- **THEN** 시스템은 HTTP 400과 `{ error: { code: "TOO_LONG", message: "메시지는 1000자 이내", limit: 1000, actual: <길이> } }`를 반환하며 메시지를 생성하지 않는다

### Requirement: 메시지 폴링
시스템은(SHALL) `GET /teams/{id}/messages`를 통해 팀의 메시지를 반환해야 하며, 해당 시각 이후 생성된 메시지만 반환하는 선택적 `since=` 타임스탬프 파라미터를 지원해야 한다. 클라이언트는 고정된 5초 간격으로 이 엔드포인트를 폴링해야 하며, 시스템은 클라이언트의 동적 폴링 주기 조정이나 재연결 backoff 동작을 요구하거나 의존하지 않아야 한다.

#### Scenario: since 없이 최초 로딩
- **WHEN** 팀 멤버가 `since` 파라미터 없이 `GET /teams/{id}/messages`를 호출하면
- **THEN** 시스템은 해당 팀의 가장 최근 메시지(예: 최근 50개)를 오래된 순으로 반환한다

#### Scenario: since를 사용한 증분 폴링
- **WHEN** 팀 멤버가 `GET /teams/{id}/messages?since=<타임스탬프>`를 호출하면
- **THEN** 시스템은 `created_at`이 `<타임스탬프>` 이후인 메시지만 반환하거나, 없으면 빈 배열을 반환한다

#### Scenario: 신규 메시지 없음
- **WHEN** 폴링의 `since` 타임스탬프가 어떤 메시지보다도 최신인 경우
- **THEN** 시스템은 HTTP 200과 빈 배열을 반환한다(에러가 아님)

### Requirement: 메시지 삭제
시스템은(SHALL) 사용자가 `DELETE /messages/{id}`를 통해 본인의 메시지만 삭제할 수 있게 해야 한다. 팀 owner라도 다른 멤버의 메시지를 삭제할 수 없어야 한다.

#### Scenario: 본인 메시지 삭제
- **WHEN** 사용자가 `user_id`가 호출자와 일치하는 메시지에 대해 `DELETE /messages/{id}`를 호출하면
- **THEN** 시스템은 메시지를 삭제하고 HTTP 200을 반환한다

#### Scenario: 타인 메시지 삭제 시도
- **WHEN** 사용자(팀 owner 포함)가 다른 사람이 작성한 메시지에 대해 `DELETE /messages/{id}`를 호출하면
- **THEN** 시스템은 HTTP 403과 `{ error: { code: "NOT_OWNER", message: "본인 메시지만 삭제 가능" } }`를 반환하며 메시지를 삭제하지 않는다

### Requirement: 메시지 무손실 보장
시스템은(SHALL) 성공적으로 생성된(HTTP 201) 메시지가 명시적으로 삭제되기 전까지 이후의 모든 `GET /teams/{id}/messages` 호출에서 (적절한 `since` 값과 함께) 조회 가능함을 보장해야 한다.

#### Scenario: 폴링 공백 이후에도 메시지가 유지됨
- **WHEN** 클라이언트가 폴링하지 않는 동안(예: 일시적 오프라인) 메시지가 성공적으로 전송되고, 이후 클라이언트가 메시지의 `created_at` 이전 시각으로 `since=`를 설정해 폴링을 재개하면
- **THEN** 해당 메시지가 다음 폴링 응답에 포함된다
