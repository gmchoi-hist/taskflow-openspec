## ADDED Requirements

### Requirement: 태스크 생성
시스템은(SHALL) 팀 멤버가 `POST /teams/{id}/tasks`를 통해 제목(1-100자)과 선택적인 `assignee_id`로 태스크를 생성할 수 있게 해야 한다. 신규 태스크는 기본값으로 `status = TODO`여야 하며, `creator_id`를 호출자로, `created_at`을 기록해야 한다.

#### Scenario: 담당자를 지정한 태스크 생성
- **WHEN** 팀 멤버가 제목과 함께 팀 멤버 중 한 명(또는 생략/null)으로 설정된 `assignee_id`로 `POST /teams/{id}/tasks`를 호출하면
- **THEN** 시스템은 `status=TODO`, `creator_id=호출자`, 지정된 `assignee_id`를 가진 `tasks` 레코드를 생성하고 HTTP 201을 반환한다

### Requirement: 태스크 목록 조회 및 필터
시스템은(SHALL) `GET /teams/{id}/tasks`를 통해 팀의 태스크를 `created_at` 내림차순으로 반환해야 하며, 전체 조회·본인 태스크(`assignee_id = current_user_id`)·미할당(`assignee_id IS NULL`) 필터를 지원해야 한다.

#### Scenario: 전체 태스크 조회
- **WHEN** 팀 멤버가 필터 없이 `GET /teams/{id}/tasks`를 호출하면
- **THEN** 시스템은 해당 팀의 모든 태스크를 최신순으로 반환한다

#### Scenario: "내 태스크" 필터
- **WHEN** 팀 멤버가 `GET /teams/{id}/tasks?filter=me`를 호출하면
- **THEN** 시스템은 `assignee_id`가 호출자의 id와 일치하는 태스크만 반환한다(`creator_id` 기준이 아님)

#### Scenario: 미할당 필터
- **WHEN** 팀 멤버가 `GET /teams/{id}/tasks?filter=unassigned`를 호출하면
- **THEN** 시스템은 `assignee_id IS NULL`인 태스크만 반환한다

### Requirement: 태스크 상태 변경
시스템은(SHALL) 팀 멤버가 태스크 제목과 무관하게 `PATCH /tasks/{id}/status`를 통해 `TODO`, `DOING`, `DONE` 사이에서 태스크를 이동할 수 있게 해야 한다.

#### Scenario: 다른 컬럼으로 태스크 이동
- **WHEN** 팀 멤버가 자신의 팀에 속한 태스크에 대해 `{ status: "DOING" }`으로 `PATCH /tasks/{id}/status`를 호출하면
- **THEN** 시스템은 태스크의 상태를 업데이트하고 HTTP 200을 반환한다

### Requirement: 태스크 상세 수정
시스템은(SHALL) 팀 멤버가 `PUT /tasks/{id}`를 통해 태스크의 제목 및/또는 담당자를 수정할 수 있게 하고, `GET /tasks/{id}`를 통해 단일 태스크 상세를 조회할 수 있게 해야 한다.

#### Scenario: 제목과 담당자 수정
- **WHEN** 팀 멤버가 새 제목 및/또는 `assignee_id`로 `PUT /tasks/{id}`를 호출하면
- **THEN** 시스템은 해당 필드를 업데이트하고 HTTP 200과 수정된 태스크를 반환한다

### Requirement: 태스크 삭제 권한
시스템은(SHALL) 태스크의 `creator_id` 또는 팀의 `owner_id`만 `DELETE /tasks/{id}`로 태스크를 삭제할 수 있게 해야 한다. 그 외 멤버는 HTTP 403을 받아야 한다.

#### Scenario: 생성자가 본인 태스크 삭제
- **WHEN** 태스크의 생성자가 `DELETE /tasks/{id}`를 호출하면
- **THEN** 시스템은 태스크를 삭제하고 HTTP 200을 반환한다

#### Scenario: owner가 다른 멤버의 태스크 삭제
- **WHEN** 팀 owner(생성자가 아님)가 `DELETE /tasks/{id}`를 호출하면
- **THEN** 시스템은 태스크를 삭제하고 HTTP 200을 반환한다

#### Scenario: 생성자도 owner도 아닌 멤버의 삭제 시도
- **WHEN** 생성자도 owner도 아닌 멤버가 `DELETE /tasks/{id}`를 호출하면
- **THEN** 시스템은 HTTP 403과 `{ error: { code: "FORBIDDEN", message: "권한이 없습니다" } }`를 반환하며 태스크는 삭제되지 않는다

### Requirement: 다른 팀 태스크 접근 차단
시스템은(SHALL) 호출자의 `team_id`가 태스크의 `team_id`와 일치하지 않는 경우 모든 태스크 읽기/쓰기 작업을 거부해야 한다.

#### Scenario: 비멤버가 다른 팀의 태스크에 접근
- **WHEN** 태스크 `{id}`를 소유하지 않은 팀의 사용자가 `GET /tasks/{id}`, `PUT /tasks/{id}`, `PATCH /tasks/{id}/status`, `DELETE /tasks/{id}` 중 하나를 호출하면
- **THEN** 시스템은 각 요청에 대해 HTTP 403과 `{ error: { code: "FORBIDDEN", ... } }`를 반환한다
