# 수동 검증 가이드

이 문서를 위에서 아래로 따라가면 모든 검증을 직접 재현할 수 있다.

## 0. 사전 준비

- 작업 폴더: `E:\codyssey_claude\B3-2-2\output_MiniGit구축`
- 실행 환경: Python 3.10 이상
- 외부 라이브러리: 불필요

```bash
cd E:\codyssey_claude\B3-2-2\output_MiniGit구축
python --version   # 3.10 이상 확인
python main.py
```

---

## 1. 구현 실행 검증

### 1-1. 기본 시나리오 (INIT → COMMIT → BRANCH → SWITCH → LOG)

- 목적: 저장소 초기화, 커밋 생성, 브랜치 생성/전환, 위상 정렬 로그 확인
- 실행: `python main.py` 후 아래 명령 순서대로 입력

```
init "Alice"
commit "Initial commit"
branch feature
switch feature
commit "Add login feature"
switch main
commit "Add payment feature"
log
exit
```

- 기대 출력:

```
Initialized repository.
Current branch: main
Current user: Alice

[main 000001] Initial commit

Created branch: feature

Switched to branch: feature

[feature 000002] Add login feature

Switched to branch: main

[main 000003] Add payment feature

commit 000001 (Alice, ...)
Initial commit
commit 000002 (Alice, ...)
Add login feature
commit 000003 (Alice, ...)
Add payment feature
```

- 확인 포인트: LOG 출력이 000001 → 000002 → 000003 순서(부모가 자식보다 먼저)이면 위상 정렬 통과.

---

### 1-2. PATH 검증

- 목적: 두 커밋 사이 최단 경로 및 `No path` 처리 확인
- 실행: 1-1 시나리오 상태에서 계속

```
path 000001 000003
path 000001 000002
path 000002 000099
exit
```

- 기대 출력:

```
Path: 000001 -> 000003
Path: 000001 -> 000002
Unknown commit: 000099
```

- 확인 포인트: 000001→000003은 직접 연결(000001이 000003의 조상). 000002는 feature 브랜치 소속이나 000001의 자식이므로 경로 존재.

---

### 1-3. SEARCH 검증

- 목적: 역색인 기반 키워드/작성자 검색 확인
- 실행: 1-1 시나리오 상태에서 계속

```
search login
search --author=Alice
search notexist
exit
```

- 기대 출력:

```
Found 1 commit(s):
- 000002 Add login feature

Found 3 commit(s) by Alice:
- 000001 Initial commit
- 000002 Add login feature
- 000003 Add payment feature

No commits matching 'notexist'
```

- 확인 포인트: "login" 검색 결과가 000002 단 1건인지 확인. Alice 검색 결과가 3건인지 확인.

---

### 1-4. ANCESTORS 검증

- 목적: 특정 커밋의 모든 조상 탐색 확인
- 실행: 1-1 시나리오 상태에서 계속

```
ancestors 000003
ancestors 000001
exit
```

- 기대 출력:

```
Ancestors of 000003:
- 000001 Initial commit

No ancestors
```

- 확인 포인트: 000003의 조상은 000001 단 1개(000002는 별도 브랜치). 000001은 루트이므로 조상 없음.

---

### 1-5. LOG --sort-by 검증

- 목적: 병합 정렬 기반 날짜/작성자 정렬 확인
- 실행: 1-1 시나리오 상태에서 계속

```
log --sort-by=date
log --sort-by=author
exit
```

- 기대 출력: 두 명령 모두 커밋 3개를 hash 순서대로 출력 (타임스탬프 및 작성자 모두 동일하므로 삽입 순서 보존)
- 확인 포인트: 출력이 오류 없이 3개 커밋을 반환하면 통과. 정렬 기준이 다른 경우 순서 달라짐 확인 가능.

---

### 1-6. 대소문자 무시 및 에러 처리 검증

- 목적: 명령어 대소문자 무시, 잘못된 입력 에러 메시지 확인

```
INIT "Bob"
Commit "First"
LOG
switch nonexistent
exit
```

- 기대 출력:

```
Initialized repository.
Current branch: main
Current user: Bob

[main 000001] First

commit 000001 (Bob, ...)
First

Unknown branch: nonexistent
```

- 확인 포인트: `Commit`(소문자 시작)이 `COMMIT`과 동일하게 처리되면 통과. `switch nonexistent`가 에러 메시지를 반환하면 통과.

---

## 2. 제약 충족 수동 확인

| PDF 제약 | 확인 방법 | 위치 |
|----------|-----------|------|
| sorted()/list.sort() 금지 | `grep -n "sorted\|list.sort" main.py` 결과 0건 | - |
| 그래프 전용 라이브러리 금지 | `grep -n "^import\|^from" main.py` 확인: sys/time/datetime/shlex만 | main.py:1-4 |
| 커밋 노드 필수 필드 | Commit 클래스 필드 직접 확인 | main.py:11-17 |
| DAG 구조 | Repository.commits에 싸이클 생성 경로 없음 확인 | main.py:구조 |
| hash O(1) 조회 | `self.commits = {}` — dict 사용 확인 | main.py:25 |
| 역색인 2종 | keyword_index, author_index 선언 확인 | main.py:28-29 |
| 알고리즘 독립 분리 | merge_sort, topological_sort, bfs_shortest_path, get_ancestors가 독립 함수인지 확인 | main.py:36-156 |

```bash
# sorted/list.sort 미사용 확인
python -c "
import ast, sys
with open('main.py') as f:
    src = f.read()
if 'sorted(' in src or 'list.sort' in src or '.sort(' in src:
    print('제약 위반 발견')
else:
    print('제약 충족: sorted/list.sort 미사용')
"
```

---

## 3. 산출물 정합성 확인

- [ ] `main.py` 존재 및 `python main.py` 실행 가능
- [ ] `architecture.md` mermaid 블록 포함 확인
- [ ] `README.md` 실행법(`python main.py`) 그대로 동작
- [ ] `EXPLANATION.md` 제약-코드 매핑 표 전수 확인
- [ ] `EXPLANATION.md` 선택과제 미수행 명시 확인
- [ ] 모든 산출물 한국어

---

## 4. codereview 결과 요약 (Step 6)

pal codereview (gemini-2.5-flash) 수행 완료.

| 지적 | 심각도 | 채택 여부 | 사유 |
|------|--------|-----------|------|
| COMMIT 공백 포함 메시지 따옴표 필요 안내 | LOW | 채택 | REPL 시작 메시지에 안내 문구 추가 |

---

## 5. 종합 판정

모든 항목 통과 시 과제 완료로 본다.

| 검증 항목 | 상태 |
|-----------|------|
| 필수 명령 10종 구현 | ✓ |
| sorted()/list.sort() 미사용 | ✓ |
| 그래프 전용 라이브러리 미사용 | ✓ |
| LOG 위상 정렬 (부모 먼저) | ✓ |
| PATH 최단 경로 + 사전순 최소 | ✓ |
| ANCESTORS 전체 조상 탐색 | ✓ |
| 역색인 2종 (keyword/author) | ✓ |
| 명령어 대소문자 무시 | ✓ |
| REPL exit/quit 종료 | ✓ |
| 선택과제 미수행 | ✓ |
| 산출물 4종 + MANUAL 생성 | ✓ |
| 모든 산출물 한국어 | ✓ |
