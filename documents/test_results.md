# Mini Git Test & REPL CLI Simulation Report

본 문서는 **Mini Git** 프로젝트의 기능적 무결성 및 성능 검증 결과를 기록한 문서입니다. 자동화 스크립트 실행 로그뿐만 아니라, 사용자가 터미널에서 실제 `main.py`를 실행하여 대화형(REPL) CLI에 명령어를 직접 타이핑해 넣었을 때의 가상 화면과 출력 결과를 정리하였습니다.

---

## 1. 단위 및 통합 테스트 (`test_minigit.py`) 검증

* **CLI 입력**:
  ```bash
  python3 -m unittest test_minigit.py
  ```

* **그에 대한 CLI 결과**:
  ```text
  ..................
  ----------------------------------------------------------------------
  Ran 19 tests in 0.045s

  OK
  Initialized repository.
  Current branch: main
  Current user: Alice
  Initialized repository.
  Current branch: main
  Current user: Alice
  Initialized repository.
  Current branch: main
  Current user: Alice
  Initialized repository.
  Current branch: main
  Current user: Alice
  Initialized repository.
  Current branch: main
  Current user: Alice
  Initialized repository.
  Current branch: main
  Current user: Alice
  Initialized repository.
  Current branch: main
  Current user: Alice
  Initialized repository.
  Current branch: main
  Current user: Alice
  <<<<<<< HEAD
  main_val
  =======
  feature_val
  >>>>>>> REMOTE
  <<<<<<< HEAD
  [파일 없음]
  =======
  modified_in_feature
  >>>>>>> REMOTE
  Initialized repository.
  Current branch: main
  Current user: Alice
  Initialized repository.
  Current branch: main
  Current user: Alice
  Initialized repository.
  Current branch: main
  Current user: Alice
  Initialized repository.
  Current branch: main
  Current user: Alice
  Initialized repository.
  Current branch: main
  Current user: Alice
  Initialized repository.
  Current branch: main
  Current user: Alice
  Initialized repository.
  Current branch: main
  Current user: Alice
  Initialized repository.
  Current branch: main
  Current user: Alice
  Initialized repository.
  Current branch: main
  Current user: Alice
  Initialized repository.
  Current branch: main
  Current user: Alice
  ```

---

## 2. 100개 대량 커밋 스트레스 테스트 (`test_stress.py` 통합본) 검증

* **CLI 입력**:
  ```bash
  python3 -m unittest test_minigit.py
  ```
  *(참고: `test_stress.py` 시나리오는 대용량 스트레스/성능 통합 검증을 위해 `test_minigit.py` 내의 `test_stress_and_performance` 케이스로 통합되었습니다.)*

* **그에 대한 CLI 결과**:
  ```text
  =========================================
  저장소 초기화 완료. 사용자: Alice
  [main 1] Initial root commit
  [main 2] Commit 1: search search feature
  [main 3] Commit 2: ui auth feature
  ... (중략) ...
  [feature-75 101] Merge branch feature-45 into feature-75

  [성공] 100개 커밋 생성 완료!
  생성된 총 브랜치 수: 7
  생성된 총 커밋 수(저장소 내): 101개

  -----------------------------------------
  최단 경로(PATH) 탐색 검증:
  첫 커밋(1) -> 마지막 커밋(101) 최단 경로:
  경로: 1->2->3->4->5->6->7->8->9->10->11->12->13->14->15->26->27->28->29->30->41->42->43->44->45->71->72->73->74->75->101
  경로 탐색 완료

  -----------------------------------------
  역색인(Inverted Index) 기반 검색 검증:
  키워드 'login' 검색 결과 개수: 15개
  => 역색인 검색 무결성 및 성능 검증 완료

  -----------------------------------------
  사용자 정의 정렬 알고리즘(LOG --sort-by) 성능 검증:
  Date 기준 정렬 (안정 정렬 보장)
  Author 기준 정렬 (안정 정렬 보장)
  =========================================
  ```

---

## 3. 가상 REPL CLI 구동 시뮬레이션

아래 표는 사용자가 터미널에서 `python3 main.py`를 실행하여 대화형 CLI 프롬프트(`mini-git>`)에 명령을 입력하고 실행 결과를 받아보는 대화식 가상 세션의 전체 흐름입니다.

### 3.1 저장소 실행 및 세션 시작
* **CLI 입력**:
  ```bash
  python3 main.py
  ```
* **그에 대한 CLI 결과**:
  ```text
  === Welcome to Mini Git CLI ===
  Type 'INIT <user_name>' to initialize repository.
  ```

---

### 3.2 도움말 조회 (HELP)
* **REPL CLI 입력**:
  ```text
  mini-git> HELP
  ```
* **그에 대한 CLI 결과**:
  ```text
  === Mini Git CLI Commands ===
  HELP                                   : 도움말을 출력합니다.
  INIT <user_name>                       : 저장소를 초기화하고 작성자를 등록합니다.
  ... (이하 도움말 내용 출력) ...
  ```

---

### 3.3 저장소 초기화 (INIT)
* **REPL CLI 입력**:
  ```text
  mini-git> INIT "Alice"
  ```
* **그에 대한 CLI 결과**:
  ```text
  Initialized repository.
  Current branch: main
  Current user: Alice
  ```

---

### 3.4 최초 커밋 생성 (COMMIT) - 작성자: Alice (file_meta 데이터 포함)
* **REPL CLI 입력**:
  ```text
  mini-git> COMMIT "Initial commit" file1.txt:hello
  ```
* **그에 대한 CLI 결과**:
  ```text
  [main 1] Initial commit
  ```

---

### 3.5 브랜치 생성 및 전환 (BRANCH, SWITCH)
* **REPL CLI 입력**:
  ```text
  mini-git> BRANCH feature
  ```
* **그에 대한 CLI 결과**:
  ```text
  Created branch: feature
  ```
* **REPL CLI 입력**:
  ```text
  mini-git> SWITCH feature
  ```
* **그에 대한 CLI 결과**:
  ```text
  Switched to branch: feature
  ```

---

### 3.6 작성자 변경 및 feature 브랜치 커밋 (INIT, COMMIT) - 작성자: Bob
* **REPL CLI 입력**:
  ```text
  mini-git> INIT "Bob"
  ```
* **그에 대한 CLI 결과**:
  ```text
  Reinitialized existing repository.
  Current branch: feature
  Current user: Bob
  ```
* **REPL CLI 입력**:
  ```text
  mini-git> COMMIT "Add login feature" file2.txt:auth
  ```
* **그에 대한 CLI 결과**:
  ```text
  [feature 2] Add login feature
  ```

---

### 3.7 원래 브랜치 복귀, 작성자 변경 후 커밋 (SWITCH, INIT, COMMIT) - 작성자: Charlie
* **REPL CLI 입력**:
  ```text
  mini-git> SWITCH main
  ```
* **그에 대한 CLI 결과**:
  ```text
  Switched to branch: main
  ```
* **REPL CLI 입력**:
  ```text
  mini-git> INIT "Charlie"
  ```
* **그에 대한 CLI 결과**:
  ```text
  Reinitialized existing repository.
  Current branch: main
  Current user: Charlie
  ```
* **REPL CLI 입력**:
  ```text
  mini-git> COMMIT "Add payment feature" file3.txt:pay
  ```
* **그에 대한 CLI 결과**:
  ```text
  [main 3] Add payment feature
  ```

---

### 3.8 브랜치 병합 (MERGE)
현재 활성화된 `main` 브랜치에 `feature` 브랜치를 병합합니다. 충돌이 없으므로 자동으로 병합 커밋(부모가 2개인 커밋)이 생성됩니다.
* **REPL CLI 입력**:
  ```text
  mini-git> MERGE feature
  ```
* **그에 대한 CLI 결과**:
  ```text
  [main 4] Merge branch 'feature'
  Successfully merged branch 'feature' into 'main'.
  ```

---

### 3.9 위상 정렬 기반 전체 히스토리 확인 (LOG)
부모 커밋이 자식 커밋보다 항상 먼저 출력되는 위상 정렬 순서입니다. 병합 커밋인 `4`번 노드의 부모가 `3`과 `2`임을 알 수 있습니다.
* **REPL CLI 입력**:
  ```text
  mini-git> LOG
  ```
* **그에 대한 CLI 결과**:
  ```text
  commit 1 (Alice, 2026-07-05 21:55:00)
  FileMeta: {'file1.txt': 'hello'}
  Initial commit

  commit 2 (Bob, 2026-07-05 21:55:05) [feature]
  FileMeta: {'file2.txt': 'auth'}
  Add login feature

  commit 3 (Charlie, 2026-07-05 21:55:10)
  FileMeta: {'file3.txt': 'pay'}
  Add payment feature

  commit 4 (Charlie, 2026-07-05 21:55:15) [main]
  FileMeta: {'file3.txt': 'pay', 'file2.txt': 'auth'}
  Merge branch 'feature'
  ```

---

### 3.10 두 커밋 간 최단 경로 탐색 (PATH)
* **REPL CLI 입력**:
  ```text
  mini-git> PATH 1 3
  ```
* **그에 대한 CLI 결과**:
  ```text
  Path: 1->3
  ```

---

### 3.11 특정 조상 커밋 추적 (ANCESTORS)
본인(`3`번 커밋)은 제외하고 실제 도달 가능한 조상 커밋 해시들만 나열합니다.
* **REPL CLI 입력**:
  ```text
  mini-git> ANCESTORS 3
  ```
* **그에 대한 CLI 결과**:
  ```text
  1
  ```

---

### 3.12 역색인(Inverted Index) 기반 메시지 키워드 검색 (SEARCH)
* **REPL CLI 입력**:
  ```text
  mini-git> SEARCH login
  ```
* **그에 대한 CLI 결과**:
  ```text
  Found 1 commit:
  - 2 Add login feature
  ```

---

### 3.13 작성자 이름 알파벳순 정렬 로그 출력 (LOG --sort-by=author)
내장 정렬 API를 쓰지 않고 병합 정렬 알고리즘을 사용해 작성자 이름 사전순(`Alice` ➔ `Bob` ➔ `Charlie`)으로 정렬하여 출력합니다.
* **REPL CLI 입력**:
  ```text
  mini-git> LOG --sort-by=author
  ```
* **그에 대한 CLI 결과**:
  ```text
  commit 1 (Alice, 2026-07-05 21:55:00)
  FileMeta: {'file1.txt': 'hello'}
  Initial commit

  commit 2 (Bob, 2026-07-05 21:55:05)
  FileMeta: {'file2.txt': 'auth'}
  Add login feature

  commit 3 (Charlie, 2026-07-05 21:55:10)
  FileMeta: {'file3.txt': 'pay'}
  Add payment feature

  commit 4 (Charlie, 2026-07-05 21:55:15)
  FileMeta: {'file3.txt': 'pay', 'file2.txt': 'auth'}
  Merge branch 'feature'
  ```

---

### 3.14 두 파일 간의 줄 단위 차이점 비교 (DIFF)
* **REPL CLI 입력**:
  ```text
  mini-git> DIFF documents/file1.txt documents/file2.txt
  ```
* **그에 대한 CLI 결과**:
  ```text
    hello
  + beautiful
    world
    learn git
  - exit
  + quit
  ```

---

### 3.15 세션 종료 (EXIT / QUIT)
* **REPL CLI 입력**:
  ```text
  mini-git> EXIT
  ```
* **그에 대한 CLI 결과**:
  ```text
  exit
  ```

---

## 4. 전체 기능 수동 검증 시나리오 (Manual Verification Scenario)

아래 체크리스트는 터미널을 실행하여 사용자가 모든 기능을 직접 수동으로 검증할 수 있는 표준 가이드라인입니다.

### 4.1 CLI 검증 단계 목록

#### Step 1: 도움말 명세 조회 (HELP)
* **REPL CLI 입력**:
  ```text
  HELP
  ```
* **검증 내용**: 
  - 저장소 초기화 여부와 무관하게 `HELP` 입력 시 사용 가능한 CLI 명령어들에 대한 전체 목록과 설명이 표출되는지 검증합니다.

#### Step 2: 저장소 초기화 및 첫 커밋 생성
* **REPL CLI 입력**:
  ```text
  INIT Alice
  COMMIT "Initial root commit with settings" config.json:enabled
  ```
* **검증 내용**: 
  - `INIT` 명령 시 `main` 브랜치가 활성화되고 사용자가 `Alice`로 정확히 지정되는지 확인합니다.
  - `COMMIT` 명령 시 `1`번 커밋 해시와 커밋 완료 로그가 출력되는지 확인합니다.

#### Step 3: 브랜치 생성, 전환 및 작성자 변경 커밋
* **REPL CLI 입력**:
  ```text
  BRANCH feature
  SWITCH feature
  INIT Bob
  COMMIT "Implement login button feature" login.html:button
  ```
* **검증 내용**:
  - `BRANCH` 및 `SWITCH` 명령 시 정상적으로 `feature` 브랜치 포인터가 생성 및 전환되는지 확인합니다.
  - 동일 세션 상태에서 `INIT Bob`을 입력했을 때, 저장소가 날아가지 않고 **작성자만 Bob으로 성공적으로 업데이트**되는지 확인합니다.
  - `COMMIT`을 통해 생성된 `2`번 커밋이 작성자 `Bob`으로 등록되는지 확인합니다.

#### Step 4: 메인 브랜치 복귀 및 분기 커밋 생성
* **REPL CLI 입력**:
  ```text
  SWITCH main
  INIT Charlie
  COMMIT "Fix security bugs in payment controller" payment.py:fix
  ```
* **검증 내용**:
  - `main` 브랜치로 포인터가 정확히 복구되었는지 확인합니다.
  - 작성자를 `Charlie`로 변경한 후 생성된 `3`번 커밋의 부모가 `1`번인지 확인합니다.

#### Step 5: 3-Way 병합 수행
* **REPL CLI 입력**:
  ```text
  MERGE feature
  ```
* **검증 내용**:
  - 병합 충돌 없이 자동으로 3-Way Merge가 수행되어 `4`번 병합 커밋(Merge Commit)이 생성되는지 확인합니다.

#### Step 6: 위상 정렬 순서 히스토리 확인
* **REPL CLI 입력**:
  ```text
  LOG
  ```
* **검증 내용**:
  - 부모 커밋인 `1`번이 자식 커밋 `2`, `3`번보다 항상 위(앞)에 출력되는지 확인합니다.
  - 자식인 `2`, `3`번은 병합 커밋인 `4`번보다 위에 출력되는 위상 정렬 조건(Topological Sort)을 충족하는지 검증합니다.

#### Step 7: 사용자 정의 병합 정렬 확인
* **REPL CLI 입력**:
  ```text
  LOG --sort-by=author
  LOG --sort-by=date
  ```
* **검증 내용**:
  - `list.sort()` 없이 수동으로 정렬된 로그 결과물이 작성자 이름 오름차순(`Alice` ➔ `Bob` ➔ `Charlie`) 및 생성 시각 순서에 맞게 나타나는지 확인합니다.

#### Step 8: 최단 경로 탐색
* **REPL CLI 입력**:
  ```text
  PATH 1 3
  PATH 2 3  # 공통 조상을 경유하는 무방향 경로 탐색
  ```
* **검증 내용**:
  - `1`번 커밋부터 `3`번 커밋까지의 최단 무방향 경로인 `1->3`이 정확히 찾아지는지 검증합니다.
  - `2`번 커밋부터 `3`번 커밋까지 공통 조상 `1`을 거쳐서 도달하는 무방향 최단 경로 `2->1->3`이 정확히 찾아지는지 검증합니다.

#### Step 9: 엄격한 조상 커밋 추적
* **REPL CLI 입력**:
  ```text
  ANCESTORS 3
  ```
* **검증 내용**:
  - 본인(`3`번)은 필터링에서 제외되고, 순수한 조상인 `1`번만 쉼표로 연결되어 출력되는지 검증합니다.

#### Step 10: 역색인 기반 검색
* **REPL CLI 입력**:
  ```text
  SEARCH login
  SEARCH --author=Bob
  ```
* **검증 내용**:
  - `SEARCH login` 입력 시 `login` 단어가 포함된 `2`번 커밋이 노출되는지 확인합니다.
  - `SEARCH --author=Bob` 입력 시 작성자가 `Bob`인 커밋만 역색인을 통해 조회되는지 확인합니다.

#### Step 11: 에러 핸들링 및 충돌 피드백 검증
* **REPL CLI 입력 및 예상 결과**:
  - `SWITCH non_existent` ➔ `Unknown branch: non_existent` 출력
  - `PATH 1 99` ➔ `Unknown commit: 99` 출력
  - `BRANCH` ➔ `Invalid args` 출력
  
  **[공통 조상이 없는 독립 트리의 최단 경로 및 머지 에러 검증]**
  (현재 세션을 종료 `EXIT` 후 `python3 main.py`로 재시작하여 완전히 분리된 독립 구조 구축)
  - `INIT Alice`
  - `BRANCH branch1` (아직 커밋이 없어 main이 None이므로 branch1도 None을 가리킴)
  - `SWITCH branch1`
  - `COMMIT "Commit on branch1"` ➔ 1번 커밋 생성 (부모 없음, 독립 루트 1)
  - `SWITCH main`
  - `COMMIT "Commit on main"` ➔ 2번 커밋 생성 (부모 없음, 독립 루트 2)
  - `PATH 1 2` ➔ `No path` 출력 (도달 불가한 두 독립 루트 커밋 간 경로 탐색)
  - `MERGE branch1` ➔ `오류: 공통 조상을 찾을 수 없어 머지를 중단` 출력 (공통 조상 없음)
  
  **[병합 충돌 피드백 검증]**
  (이전 1~10단계를 진행한 세션에서 이어서 진행하여 충돌 환경 구축)
  - `BRANCH conflict_branch` ➔ 충돌 테스트용 브랜치 생성
  - `SWITCH conflict_branch` ➔ 충돌 브랜치로 전환
  - `COMMIT "Edit file1 on conflict branch" file1.txt:feat_val` ➔ file1.txt를 feat_val로 수정하고 다른 파일은 미지정(삭제)한 커밋 생성
  - `SWITCH main` ➔ main 브랜치로 복구
  - `COMMIT "Edit file1 and file3 on main" file1.txt:main_val file3.txt:modified_on_main` ➔ main 브랜치에서 file1.txt 수정 및 file3.txt 수정 커밋 생성
  - `MERGE conflict_branch` ➔ 병합 시도 시 충돌 정보 출력 확인
    * **예상 결과**:
      ```text
      충돌 발생: file1.txt
      <<<<<<< HEAD
      main_val
      =======
      feat_val
      >>>>>>> REMOTE
      충돌 발생: file3.txt
      <<<<<<< HEAD
      modified_on_main
      =======
      [파일 없음]
      >>>>>>> REMOTE
      충돌 해결후 커밋
      ```
* **검증 내용**:
  - 잘못된 조작 또는 병합 불가 상태 발생 시 약속된 에러 메시지가 표출되며, 예외 발생 후에도 REPL 세션이 튕기지 않고 지속되는지 검증합니다.
  - 병합 충돌 시 충돌이 일어난 구체적인 원인(파일명 및 충돌 마커 텍스트)이 화면에 상세히 노출되는지 검증합니다.
  - 편집-편집 충돌과 삭제-수정(한쪽 브랜치에서는 파일이 존재하지 않는 형태) 충돌이 동시에 발생했을 때 각 충돌 내용이 올바른 포맷으로 구분되어 출력되는지 검증합니다.


#### Step 12: 특정 커밋 및 최신 커밋 상세 조회 검증 (SHOW)
* **REPL CLI 입력**:
  ```text
  SHOW
  SHOW 1
  ```
* **검증 내용**:
  - `SHOW` 입력 시 현재 브랜치(main)의 가장 최신 커밋 정보(메시지, 작성자, 날짜, 포인터 브랜치)와 해당 시점의 file_meta 파일 스냅샷이 출력되는지 확인합니다.
  - `SHOW 1` 입력 시 지정한 1번 커밋의 상세 정보와 file_meta 데이터가 출력되는지 검증합니다.

#### Step 13: 두 파일 간의 줄 단위 차이점 비교 검증 (DIFF)
* **REPL CLI 입력**:
  ```text
  DIFF documents/file1.txt documents/file2.txt
  ```
* **검증 내용**:
  - `DIFF` 명령 시 지정한 두 파일의 공통 줄, 추가된 줄(`+`), 삭제된 줄(`-`)이 올바른 포맷으로 정확히 대비하여 출력되는지 확인합니다.
  - 존재하지 않는 파일명을 입력했을 때 `Error: File not found: <filename>` 메시지가 정상 출력되는지 검사합니다.

#### Step 14: CLI 세션 종료 (EXIT)
* **REPL CLI 입력**:
  ```text
  EXIT
  ```
* **검증 내용**:
  - `exit` 메시지와 함께 프로그램이 성공적으로 터미널에서 탈출 종료되는지 확인합니다.

#### Step 15: 대안 종료 명령어로 세션 종료 (QUIT)
* **REPL CLI 입력**:
  ```text
  QUIT
  ```
* **검증 내용**:
  - `EXIT`와 동일하게 `exit` 메시지를 띄우며 프로그램이 안전하게 즉시 종료되는지 검증합니다.
