# Mini Git (`last_minigit`) 소스 코드 & CS 이론 매핑 가이드 (주석 임베디드 버젼)

이 가이드는 `last_minigit` 프로젝트의 실제 파이썬 소스 코드 내부에 **컴퓨터 사이언스(CS) 이론이 적용된 지점을 주석(`# [이론 X] ...`) 형태로 표시**하고, 코드를 펼치기 전인 **접기 상태의 요약 라인(`<summary>`)에서도 어떤 이론이 사용되었는지 한눈에 파악**할 수 있도록 구성했습니다.

상세한 이론 설명(v3/v5에서 확장된 핵심 개념 포함)은 이미 [cs_theory_report_v5.md](cs_theory_report_v5.md) 문서에 완전하게 정리되어 있으므로 이 파일에서는 생략했습니다.

---

## 1. `commit_graph.py` 소스 코드 매핑

### 📂 [commit_graph.py](../commit_graph.py)

#### 1) `Commit` 클래스 (커밋 정점 자료구조)
* <details>
  <summary>Commit 클래스 소스 코드 보기 (적용 이론: [이론 1] DAG, [이론 14] 유닉스 시간과 타임스탬프)</summary>

  ```python
  @dataclass(frozen=True)
  class Commit:
      """
      Git의 개별 커밋 노드를 나타내는 클래스입니다.
      데이터 무결성 확보와 부작용 방지를 위해 @dataclass(frozen=True)로 구현되어 불변성을 보장합니다.
      """
      # [이론 1] DAG - 커밋의 식별 해시 및 부모 커밋 목록을 저장하여 노드 계보 설계
      hash: str
      message: str
      author: str
      file_meta: dict
      parents: list = field(default_factory=list)
      # [이론 14] 유닉스 시간과 타임스탬프 - 커밋 생성 시간을 실수형 타임스탬프로 기록
      timestamp: float = field(default_factory=time.time)
  ```
  </details>

#### 2) `CommitGraph` 클래스 생성자 (`__init__`)
* <details>
  <summary>CommitGraph.__init__ 소스 코드 보기 (적용 이론: [이론 7] 해시 테이블 및 해싱, [이론 6] 역색인)</summary>

  ```python
      def __init__(self):
          """
          CommitGraph 객체를 초기화합니다.
          """
          self.commit_id_counter = 0  # 커밋 생성 시 순차적으로 ID를 부여하기 위한 카운터
          # [이론 7] 해시 테이블 및 해싱 - 상수 시간 O(1) 조회를 지원하는 dict(해시맵) 데이터 보관함 초기화
          self.commit_dict = {}       # 커밋 ID를 키로 하여 Commit 객체를 보관하는 딕셔너리

          # [이론 6] 역색인 - 고속 검색을 위해 뒤집힌 색인 사전용 dict(해시맵) 마련
          self.commit_word_dict = {}    # 메시지 단어별로 매핑된 커밋 ID 목록
          self.commit_author_dict = {}  # 소문자 작성자 이름별로 매핑된 커밋 ID 목록

          # 성능 최적화: 자식 노드(Children) 역색인 캐시
          self.children_dict = {}
  ```
  </details>

#### 3) `CommitGraph.add_commit` 메서드 (커밋 적재 및 역색인 빌드)
* <details>
  <summary>CommitGraph.add_commit 소스 코드 보기 (적용 이론: [이론 7] 해시 테이블, [이론 1] DAG, [이론 8] REPL 파싱, [이론 6] 역색인)</summary>

  ```python
      def add_commit(self, message, author, file_meta, parents):
          # [이론 7] 해시 테이블 - 순차 카운터를 사용하여 고유 Key 준비
          self.commit_id_counter += 1
          str_commit_id = str(self.commit_id_counter)

          # 불변성(frozen) 객체 주입을 위해 부모 리스트가 None인 경우 빈 리스트로 보정
          parents_list = parents if parents is not None else []

          # [이론 1] DAG - Commit 객체를 생성하여 부모 노드들과 연결 관계 형성
          commit = Commit(str_commit_id, message, author, file_meta, parents_list)
          # [이론 7] 해시 테이블 - dict에 커밋 ID를 Key로 객체 등록
          self.commit_dict[str_commit_id] = commit

          # 자식 노드 역색인 캐싱
          for p in parents_list:
              if p not in self.children_dict:
                  self.children_dict[p] = []
              self.children_dict[p].append(str_commit_id)

          # [이론 8] REPL 파싱과 어휘 분석 - tokenizer를 통해 메시지 단어 분해
          tokens = self.tokenizer(message)
          # [이론 6] 역색인 - 단어를 Key로 하여 커밋 ID를 매핑하는 사전 역색인 구축
          for t in set(tokens):
              if self.commit_word_dict.get(t) is None:
                  self.commit_word_dict[t] = []
              self.commit_word_dict[t].append(str_commit_id)

          # [이론 6] 역색인 - 작성자 이름을 Key로 하는 사전 역색인 구축 (소문자 표준화)
          author_lower = author.lower()
          if self.commit_author_dict.get(author_lower) is None:
              self.commit_author_dict[author_lower] = []
          self.commit_author_dict[author_lower].append(str_commit_id)

          return str_commit_id
  ```
  </details>

#### 4) `CommitGraph.search_commit_author` 및 `search_commit_word` 메서드 (역색인 조회)
* <details>
  <summary>CommitGraph.search_commit_author / word 소스 코드 보기 (적용 이론: [이론 6] 역색인)</summary>

  ```python
      def search_commit_author(self, author):
          # [이론 6] 역색인 - 미리 구축된 역색인 사전 테이블에서 단번에 O(1)로 결과 추출
          return self.commit_author_dict.get(author.lower(), [])

      def search_commit_word(self, word):
          # [이론 6] 역색인 - 미리 구축된 역색인 사전 테이블에서 단번에 O(1)로 결과 추출
          return self.commit_word_dict.get(word, [])
  ```
  </details>

#### 5) `CommitGraph.tokenizer` 메서드
* <details>
  <summary>CommitGraph.tokenizer 소스 코드 보기 (적용 이론: [이론 8] REPL 파싱과 어휘 분석)</summary>

  ```python
      def tokenizer(self, string):
          # [이론 8] REPL 파싱과 어휘 분석 - 입력 문자열을 공백 분리하여 단어 조각(Token)으로 분해
          result = [token.lower() for token in string.split(" ") if token]
          return result
  ```
  </details>

#### 6) `CommitGraph.get_all_ancestors` 메서드 (스택 기반 반복 DFS 조상 탐색)
* <details>
  <summary>CommitGraph.get_all_ancestors 소스 코드 보기 (적용 이론: [이론 10] 스택 Stack, [이론 4] DFS 순회, [이론 12] 재귀 회피, [이론 7] 해시 테이블)</summary>

  ```python
      def get_all_ancestors(self, commit_id, visited_set=None):
          if visited_set is None:
              visited_set = set()

          if not commit_id or commit_id not in self.commit_dict:
              return visited_set

          # [이론 10] 자료구조 기초 (스택 Stack) - DFS 탐색용 명시적 스택(LIFO) 선언 및 초기화
          stack = [commit_id]

          # [이론 4] 그래프 순회 및 조상 탐색 (DFS) - 깊이 우선 방식으로 계보 순회
          # [이론 12] 재귀와 콜 스택(Stack Overflow 방지) - 재귀 대신 반복문(while) 및 힙 메모리 스택 사용
          while stack:
              curr = stack.pop()
              if curr not in visited_set:
                  # [이론 7] 해시 테이블 - 중복 방문을 막기 위한 방문 처리 기록 (Set ADT 활용)
                  visited_set.add(curr)
                  
                  # [이론 4] 그래프 순회 및 조상 탐색 (DFS) - 부모 노드들을 스택의 맨 위에 추가 (DFS 순서 유지)
                  parents = self.commit_dict[curr].parents
                  for p in reversed(parents):
                      if p not in visited_set:
                          stack.append(p)

          return visited_set
  ```
  </details>

#### 7) `CommitGraph.find_common_ancestor` 메서드 (LCA 및 역방향 BFS 탐색)
* <details>
  <summary>CommitGraph.find_common_ancestor 소스 코드 보기 (적용 이론: [이론 4] DFS 순회, [이론 10] 큐 Queue, [이론 3] BFS 탐색, [이론 9] 3-Way Merge 및 LCA)</summary>

  ```python
      def find_common_ancestor(self, main_commit_id, feature_commit_id):
          # [이론 4] 그래프 순회 및 조상 탐색 (DFS) - 첫 번째 브랜치의 모든 조상 집합을 먼저 수집
          main_ancestors = self.get_all_ancestors(main_commit_id)

          # [이론 10] 자료구조 기초 (큐 Queue) - BFS를 위한 O(1) 포인터 큐 및 parent_map 부모 포인터 기록 초기설정
          queue = [feature_commit_id]
          queue_point = 0
          visited = {feature_commit_id}
          parent_map = {}

          lca_id = None
          # [이론 3] 최단 경로 알고리즘 (BFS) - 두 번째 브랜치부터 넓게 퍼져나가며 역방향 수색
          # [이론 9] 3-Way Merge 및 LCA 탐색 - 가장 가깝고 첫 번째로 겹치는 공통 분기점(LCA) 발견 시 루프 중단
          while queue_point < len(queue):
              current_id = queue[queue_point]
              queue_point += 1

              if current_id in main_ancestors:
                  lca_id = current_id
                  break

              for p in self.commit_dict[current_id].parents:
                  if p not in visited:
                      visited.add(p)
                      parent_map[p] = current_id  # p 노드에 도달하기 직전의 노드가 current_id임을 기입
                      queue.append(p)

          if lca_id is None:
              return None

          # [이론 9] 3-Way Merge 및 LCA - LCA 노드부터 부모 포인터를 역추적하여 feature_commit_id까지 도달하는 탐색 경로(history)를 복원
          history = []
          curr = lca_id
          while curr != feature_commit_id:
              history.append(curr)
              curr = parent_map[curr]
          history.append(feature_commit_id)
          history.reverse()

          return lca_id, history
  ```
  </details>

#### 8) `CommitGraph.find_shortest_path` 메서드 (최단 경로 BFS 탐색)
* <details>
  <summary>CommitGraph.find_shortest_path 소스 코드 보기 (적용 이론: [이론 10] 큐 Queue, [이론 3] BFS 최단 경로 탐색 및 사전순 비교)</summary>

  ```python
      def find_shortest_path(self, start_hash, end_hash):
          if start_hash not in self.commit_dict or end_hash not in self.commit_dict:
              return None

          if start_hash == end_hash:
              return [start_hash]

          # [이론 10] 자료구조 기초 (큐 Queue) - BFS 레벨 탐색용 경로 대기열 초기설정
          paths_queue = [[start_hash]]
          visited = {start_hash}
          found_paths = []

          # [이론 3] 최단 경로 알고리즘 (BFS) - 최소 연결 거리를 구하기 위해 단계별로 넓게 탐색 전개
          while paths_queue and not found_paths:
              next_queue = []
              level_visited = set()

              for path in paths_queue:
                  current = path[-1]

                  # [이론 3] 최단 경로 알고리즘 (BFS) - 무방향 간선 취급을 위한 이웃(부모 + 자식) 합산
                  parents = self.commit_dict[current].parents
                  # 캐싱된 자식 노드 역색인 테이블(children_dict)을 조회하여 스캔 성능 최적화
                  children = self.children_dict.get(current, [])
                  neighbors = set(parents) | set(children)

                  for neighbor in neighbors:
                      if neighbor == end_hash:
                          found_paths.append(path + [neighbor])
                      elif neighbor not in visited:
                          next_queue.append(path + [neighbor])
                          level_visited.add(neighbor)
              
              visited.update(level_visited)
              paths_queue = next_queue

          if not found_paths:
              return None

          # [이론 3] 최단 경로 알고리즘 - 최단 경로가 여러 개일 때 정수 변환 비교 후 사전순(Lexicographical)으로 단일 최적 루트 선정
          best_path = None
          best_key = None
          for path in found_paths:
              path_key = tuple(int(x) for x in path)
              if best_key is None or path_key < best_key:
                  best_key = path_key
                  best_path = path

          return best_path
  ```
  </details>

#### 9) `CommitGraph.topological_sort` 메서드 (Kahn 위상 정렬)
* <details>
  <summary>CommitGraph.topological_sort 소스 코드 보기 (적용 이론: [이론 2] 위상 정렬 Kahn 알고리즘, [이론 10] 큐 Queue)</summary>

  ```python
      def topological_sort(self):
          # [이론 2] 위상 정렬 - 부모 개수를 카운트하여 선수 조건인 진입 차수(In-degree) 계산
          in_degree = {c_hash: len(c_obj.parents) for c_hash, c_obj in self.commit_dict.items()}

          # [이론 10] 자료구조 기초 (큐 Queue) - 진입 차수 0(선수 조건 없음) 노드를 대기 큐에 진입
          queue = [c_hash for c_hash, deg in in_degree.items() if deg == 0]

          result = []
          queue_point = 0

          # [이론 2] 위상 정렬 - Kahn 알고리즘 핵심 루프
          while queue_point < len(queue):
              curr = queue[queue_point]
              queue_point += 1
              result.append(curr)

              # [이론 2] 위상 정렬 - 캐싱된 children_dict를 사용해 자식 노드들의 진입 차수를 깎아 조건 만족 노드(차수=0)를 큐에 수집
              for child in self.children_dict.get(curr, []):
                  in_degree[child] -= 1
                  if in_degree[child] == 0:
                      queue.append(child)

          return result
  ```
  </details>

---

## 2. `mini_git.py` 소스 코드 매핑

### 📂 [mini_git.py](../mini_git.py)

#### 1) `Git` 클래스 생성자 (`__init__`)
* <details>
  <summary>Git.__init__ 소스 코드 보기 (적용 이론: [이론 1] DAG, [이론 13] Git 참조와 HEAD 포인터)</summary>

  ```python
  class Git:
      def __init__(self, user):
          self.user = user
          self.users = {user}
          # [이론 1] DAG - 공용 커밋 그래프 인스턴스 소유
          self.graph = CommitGraph()
          # [이론 13] Git 참조(References)와 HEAD 포인터 - 브랜치 이름과 가리키는 커밋 ID 간 참조 사전 초기화
          self.branches: dict[str, str | None] = {
              "main": None
          }
          self.current_branch = "main"         # [이론 13] HEAD 포인터 초기설정
  ```
  </details>

#### 2) `Git.add_branch` 및 `switch_branch` 메서드 (브랜치 포인터 연산)
* <details>
  <summary>Git.add_branch / switch_branch 소스 코드 보기 (적용 이론: [이론 13] Git 참조와 HEAD 포인터)</summary>

  ```python
      def add_branch(self, branch_name):
          # [이론 13] Git 참조(References) - 이미 존재하는 브랜치에 대해 예외 발생
          if branch_name in self.branches:
              raise ValueError(f"이미존재{branch_name}")
          current_commit = self.branches[self.current_branch]
          self.branches[branch_name] = current_commit

      def switch_branch(self, branch_name):
          # [이론 13] Git 참조(References)와 HEAD - 존재하지 않는 브랜치 접근 시 예외 발생
          if branch_name not in self.branches:
              raise ValueError(f"Unknown branch: {branch_name}")

          self.current_branch = branch_name
  ```
  </details>

#### 3) `Git.commit` 메서드 (커밋 작성 및 참조 이동)
* <details>
  <summary>Git.commit 소스 코드 보기 (적용 이론: [이론 13] Git 참조와 HEAD, [이론 1] DAG)</summary>

  ```python
      def commit(self, message, file_meta, parents=None):
          if parents is None:
              # [이론 13] Git 참조와 HEAD - 부모 생략 시 HEAD가 가리키고 있던 최신 커밋을 부모로 자동 연계
              current_commit_id = self.branches[self.current_branch]
              if current_commit_id is not None:
                  parents = [current_commit_id]
              else:
                  parents = []  # 부모가 없는 최초 커밋(Root Commit)
          
          # [이론 1] DAG - 그래프에 정점(Commit)을 영구 등록
          str_commit_id = self.graph.add_commit(message, self.user, file_meta, parents)
          # [이론 13] Git 참조와 HEAD - 현재 활성 브랜치의 참조 꼬리표를 방금 만든 커밋 번호로 이동
          self.branches[self.current_branch] = str_commit_id

          # print(f"[{self.current_branch} {str_commit_id}] {message}")
          return str_commit_id
  ```
  </details>

#### 4) `Git.log` 메서드
* <details>
  <summary>Git.log 소스 코드 보기 (적용 이론: [이론 2] 위상 정렬)</summary>

  ```python
      def log(self):
          # [이론 2] 위상 정렬 - 부모가 자식보다 늘 위에 오도록 선후 정렬된 히스토리 획득
          sorted_hashes = self.graph.topological_sort()
          if not sorted_hashes:
              return []

          commits = [
              self.graph.commit_dict[h]
              for h in sorted_hashes
              if h in self.graph.commit_dict
          ]
          return commits
  ```
  </details>

#### 5) `Git.three_way_merge` 및 `finalize_merge` 메서드 (3-Way Merge 연산)
* <details>
  <summary>Git.three_way_merge / finalize_merge 소스 코드 보기 (적용 이론: [이론 9] 3-Way Merge 및 LCA, [이론 1] DAG)</summary>

  ```python
      def three_way_merge(self, main_commit_id, feature_commit_id):
          # [이론 9] 3-Way Merge 및 LCA 탐색 - 두 브랜치가 갈라져 나온 가장 가까운 공통 조상(Base) 검출
          ancestor_res = self.graph.find_common_ancestor(main_commit_id, feature_commit_id)

          if ancestor_res is None:
              raise ValueError("오류: 공통 조상을 찾을 수 없어 머지를 중단")
          
          base_commit_id, _ = ancestor_res
          
          base_file_meta = self.graph.commit_dict[base_commit_id].file_meta
          main_file_meta = self.graph.commit_dict[main_commit_id].file_meta
          feature_file_meta = self.graph.commit_dict[feature_commit_id].file_meta

          all_files = set(base_file_meta.keys()) | set(main_file_meta.keys()) | set(feature_file_meta.keys())

          merged_file_meta = {}
          conflicts = {}
          has_conflict = False

          # [이론 9] 3-Way Merge - Base 스냅샷 대비 Mine(내꺼)과 Theirs(상대방)의 수정 방향을 3방향 대조 판별
          for file_name in all_files:
              base_content = base_file_meta.get(file_name)
              main_content = main_file_meta.get(file_name)
              feature_content = feature_file_meta.get(file_name)

              # 1. 양쪽 동일 변경 (동일 내용 수정 또는 미수정, 동일한 삭제 포함)
              if main_content == feature_content:
                  if main_content is not None:
                      merged_file_meta[file_name] = main_content
              # 2. 한쪽만 변경 (main만 변경되고 feature는 base와 동일한 경우)
              elif feature_content == base_content:
                  if main_content is not None:
                      merged_file_meta[file_name] = main_content
              # 3. 한쪽만 변경 (feature만 변경되고 main은 base와 동일한 경우)
              elif main_content == base_content:
                  if feature_content is not None:
                      merged_file_meta[file_name] = feature_content

              # 양쪽 브랜치가 같은 파일을 서로 다르게 고친 경우 충돌 마커 기입
              else:
                  main_val = main_content if main_content is not None else "[파일 없음]"
                  feat_val = feature_content if feature_content is not None else "[파일 없음]"
                  conflict_text = f"<<<<<<< HEAD\n{main_val}\n=======\n{feat_val}\n>>>>>>> REMOTE"
                  print(conflict_text)
                  merged_file_meta[file_name] = conflict_text
                  conflicts[file_name] = conflict_text
                  has_conflict = True

          return has_conflict, merged_file_meta, conflicts
      
      def finalize_merge(self, main_commit_id, feature_commit_id, message="Merge branch"):
          merge_result = self.three_way_merge(main_commit_id, feature_commit_id)
          has_conflict, merged_file_meta, conflicts = merge_result
          
          # [이론 9] 3-Way Merge - 충돌 발생 시 MergeConflictError 예외 발생
          if has_conflict:
              raise MergeConflictError(conflicts)
          
          # [이론 1] DAG (Merge Commit) - 두 개의 부모 커밋 ID를 리스트형 인자로 주입하여 다중 부모 노드를 DAG 상에 조립
          str_commit_id = self.commit(message, merged_file_meta, [main_commit_id, feature_commit_id])

          return str_commit_id
  ```
  </details>

#### 6) `Git.log_sorted` 메서드 (커스텀 병합 정렬)
* <details>
  <summary>Git.log_sorted 소스 코드 보기 (적용 이론: [이론 5] 정렬 알고리즘 병합 정렬/안정 정렬, [이론 12] 재귀 함수)</summary>

  ```python
      def log_sorted(self, sort_by):
          commits = list(self.graph.commit_dict.values())
          if not commits:
              return []
          
          # [이론 5] 정렬 알고리즘 - 타임스탬프 비교 또는 대소문자 무시 작성자명을 비교 기준으로 람다식 설정
          if sort_by == "date":
              key_func = lambda c: c.timestamp
          elif sort_by == "author":
              key_func = lambda c: c.author.lower()
          else:
              raise ValueError(f"Unknown sort option:{sort_by}")

          # [이론 5] 정렬 알고리즘 (병합 정렬) - 반씩 나누어 정렬하고 재조합하는 분할 정복 병합정렬 수행
          # [이론 12] 재귀 함수 - merge_sort가 스스로를 다시 호출하는 재귀 설계 구조
          def merge_sort(arr):
              if len(arr) <= 1:
                  return arr
              mid = len(arr) // 2
              left = merge_sort(arr[:mid])
              right = merge_sort(arr[mid:])
              return _merge_sorted_arrays(left, right)
          
          # [이론 5] 정렬 알고리즘 (안정 정렬) - 동점 조건 시 '<=' 부등호를 사용하여 원래의 순서 상태 보존
          def _merge_sorted_arrays(left, right):
              result = []
              i = j = 0
              while i < len(left) and j < len(right):
                  if key_func(left[i]) <= key_func(right[j]):
                      result.append(left[i])
                      i += 1
                  else:
                      result.append(right[j])
                      j += 1
              result.extend(left[i:])
              result.extend(right[j:])
              return result
          
          return merge_sort(commits)
  ```
  </details>

#### 7) `Git.diff` 메서드 (LCS 기반 파일 비교)
* <details>
  <summary>Git.diff 소스 코드 보기 (적용 이론: [이론 20] LCS 최장 공통 부분 수열)</summary>

  ```python
      def diff(self, file1_path, file2_path):
          # [이론 20] LCS - 최장 공통 부분 수열을 추적하여 줄 단위 파일 차이점 계산
          try:
              with open(file1_path, 'r', encoding='utf-8') as f1:
                  lines1 = [line.rstrip('\r\n') for line in f1.readlines()]
          except FileNotFoundError:
              raise FileNotFoundError(f"File not found: {file1_path}")
          ...
          
          m, n = len(lines1), len(lines2)
          dp = [[0] * (n + 1) for _ in range(m + 1)]

          # DP 테이블 갱신
          for i in range(1, m + 1):
              for j in range(1, n + 1):
                  if lines1[i - 1] == lines2[j - 1]:
                      dp[i][j] = dp[i - 1][j - 1] + 1
                  else:
                      dp[i][j] = max(dp[i - 1][j], dp[i][j - 1])

          # 역추적(Backtracking)으로 +, -, 공통 마커 설정
          diff_result = []
          i, j = m, n
          while i > 0 or j > 0:
              if i > 0 and j > 0 and lines1[i - 1] == lines2[j - 1]:
                  diff_result.append(f"  {lines1[i - 1]}")
                  i -= 1
                  j -= 1
              elif j > 0 and (i == 0 or dp[i][j - 1] >= dp[i - 1][j]):
                  diff_result.append(f"+ {lines2[j - 1]}")
                  j -= 1
              elif i > 0 and (j == 0 or dp[i][j - 1] < dp[i - 1][j]):
                  diff_result.append(f"- {lines1[i - 1]}")
                  i -= 1

          diff_result.reverse()
          return diff_result
  ```
  </details>

---

## 3. `main.py` 소스 코드 매핑

### 📂 [main.py](../main.py)

#### 1) 데코레이터 구조 (`require_init`, `args_to_list`)
* <details>
  <summary>require_init / args_to_list 소스 코드 보기 (적용 이론: [이론 8] REPL 파싱과 어휘 분석, [이론 13] Git 참조와 HEAD)</summary>

  ```python
  # [이론 13] Git 참조와 HEAD - 명령어 실행 전 저장소가 초기화되었는지 검사하는 데코레이터
  def require_init(func):
      @wraps(func)
      def wrapper(self, arg):
          if self.git is None:
              print("Error: Repository not initialized. Run 'INIT <user_name>' first.")
              return False
          return func(self, arg)
      return wrapper

  # [이론 8] REPL 파싱과 어휘 분석 - 사용자 명령어 라인을 shlex.split()을 이용해 파싱하는 데코레이터
  def args_to_list(func):
      @wraps(func)
      def wrapper(self, arg):
          try:
              args_list = shlex.split(arg)
          except ValueError:
              print("Invalid args")
              return False
          return func(self, args_list)
      return wrapper
  ```
  </details>

#### 2) `custom_sort` 메서드 (퀵 정렬 구현)
* <details>
  <summary>custom_sort 소스 코드 보기 (적용 이론: [이론 5] 정렬 알고리즘, [이론 11] 퀵 정렬, [이론 12] 재귀 함수)</summary>

  ```python
      # [이론 5] 정렬 알고리즘 - 유저/브랜치 목록 정렬을 위해 퀵 정렬 구현
      # [이론 11] 퀵 정렬 - 기준점(Pivot)을 토대로 작고 큰 원소 그룹을 분리해 조립
      # [이론 12] 재귀 함수 - 쪼개진 무리 내에서 custom_sort를 재차 호출하는 구조
      def custom_sort(self, arr):
          if len(arr) <= 1:
              return arr
          pivot = arr[len(arr) // 2]
          left = [x for x in arr if x < pivot]
          middle = [x for x in arr if x == pivot]
          right = [x for x in arr if x > pivot]
          return self.custom_sort(left) + middle + self.custom_sort(right)
  ```
  </details>

#### 3) `precmd` 및 `do_EOF` 메서드 (REPL 명령어 전처리 및 종료)
* <details>
  <summary>precmd / do_EOF 소스 코드 보기 (적용 이론: [이론 8] REPL 파싱과 어휘 분석 REPL 루프)</summary>

  ```python
      # [이론 8] REPL 파싱과 어휘 분석 - 입력받은 명령어의 첫 토큰을 대문자로 자동 대치하여 대소문자 구분 배제
      def precmd(self, line):
          strip_result = line.strip()
          if not strip_result:
              return strip_result
          parts = strip_result.split(maxsplit=1)
          parts[0] = parts[0].upper()
          return " ".join(parts)

      # [이론 8] REPL 루프 - Ctrl+D(EOF) 입력 시 깔끔한 UX로 프로그램을 안전하게 종료하도록 지원
      def do_EOF(self, arg):
          print()
          return self.do_EXIT(arg)
  ```
  </details>

#### 4) `do_DIFF` 메서드 (LCS 기반 두 파일 비교 셸 명령어)
* <details>
  <summary>do_DIFF 소스 코드 보기 (적용 이론: [이론 20] LCS 최장 공통 부분 수열)</summary>

  ```python
      @require_init
      @args_to_list
      def do_DIFF(self, arg):
          # [이론 20] LCS - 최장 공통 부분 수열을 추적하여 줄 단위 파일 차이점 계산 및 출력
          if len(arg) != 2:
              print("Invalid args")
              return False

          file1, file2 = arg[0], arg[1]
          try:
              if self.git is not None:
                  diff_result = self.git.diff(file1, file2)
                  for line in diff_result:
                      print(line)
          except FileNotFoundError as e:
              print(f"Error: {str(e)}")
          except IOError as e:
              print(f"Error: {str(e)}")
          except Exception as e:
              print(f"Error: {str(e)}")
          return False
  ```
  </details>

#### 5) `main` 함수 (cmdloop REPL 구동)
* <details>
  <summary>main 소스 코드 보기 (적용 이론: [이론 8] REPL 파싱과 어휘 분석 REPL 루프)</summary>

  ```python
  def main():
      try:
          # [이론 8] REPL 파싱과 어휘 분석 - cmd.Cmd of cmdloop를 작동시켜 대화형 쉘 프롬프트 구동
          GitShell().cmdloop()
      except KeyboardInterrupt:
          print("\nExiting...")
  ```
  </details>
