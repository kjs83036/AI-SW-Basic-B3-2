import time
from dataclasses import dataclass, field


@dataclass(frozen=True)
class Commit:
    """
    Git의 개별 커밋 노드를 나타내는 클래스입니다.
    데이터 무결성 확보와 부작용 방지를 위해 @dataclass(frozen=True)로 구현되어 불변성을 보장합니다.
    """
    hash: str
    message: str
    author: str
    file_meta: dict
    parents: list = field(default_factory=list)
    timestamp: float = field(default_factory=time.time)


class CommitGraph:
    """
    DAG(방향성 비순환 그래프) 구조로 커밋 간의 연결 관계를 관리하고 탐색하는 클래스입니다.
    자식 탐색 캐시를 내장하여 O(1)의 탐색 속도를 지원하며, 위상 정렬과 LCA 등 핵심 그래프 연산을 최적화하여 처리합니다.
    """

    def __init__(self):
        """
        CommitGraph 객체를 초기화합니다.
        """
        self.commit_id_counter = 0  # 커밋 생성 시 순차적으로 ID를 부여하기 위한 카운터
        self.commit_dict = {}       # 커밋 ID를 키로 하여 Commit 객체를 보관하는 딕셔너리

        # 역색인(Inverted Index)을 위한 딕셔너리
        self.commit_word_dict = {}    # 메시지 단어별로 매핑된 커밋 ID 목록
        self.commit_author_dict = {}  # 소문자 작성자 이름별로 매핑된 커밋 ID 목록

        # 성능 최적화: 자식 노드(Children) 역색인 캐시
        self.children_dict = {}

    def add_commit(self, message, author, file_meta, parents):
        """
        새로운 커밋을 그래프에 추가하고, 메시지와 작성자 정보에 대한 역색인을 생성/갱신합니다.

        :param message: 커밋 메시지
        :param author: 작성자 이름
        :param file_meta: 파일 메타데이터 딕셔너리
        :param parents: 부모 커밋 ID 리스트
        :return: 신규 생성된 커밋 ID
        """
        self.commit_id_counter += 1
        str_commit_id = str(self.commit_id_counter)
        
        # 불변성(frozen) 객체 주입을 위해 부모 리스트가 None인 경우 빈 리스트로 보정
        parents_list = parents if parents is not None else []

        # Commit 객체 생성 및 딕셔너리에 등록
        commit = Commit(str_commit_id, message, author, file_meta, parents_list)
        self.commit_dict[str_commit_id] = commit

        # 자식 노드 역색인 캐싱
        for p in parents_list:
            if p not in self.children_dict:
                self.children_dict[p] = []
            self.children_dict[p].append(str_commit_id)

        # 1. 메시지 단어 역색인(Inverted Index) 갱신
        tokens = self.tokenizer(message)
        for t in set(tokens):
            if self.commit_word_dict.get(t) is None:
                self.commit_word_dict[t] = []
            self.commit_word_dict[t].append(str_commit_id)

        # 2. 작성자 이름 역색인(Inverted Index) 갱신 (대소문자 구분 없음)
        author_lower = author.lower()
        if self.commit_author_dict.get(author_lower) is None:
            self.commit_author_dict[author_lower] = []
        self.commit_author_dict[author_lower].append(str_commit_id)

        return str_commit_id

    def search_commit_author(self, author):
        """
        작성자 역색인 딕셔너리를 활용하여 특정 작성자가 작성한 커밋 ID 목록을 조회합니다.

        :param author: 검색할 작성자 이름
        :return: 작성자가 작성한 커밋 ID 리스트 (없을 시 빈 리스트)
        """
        return self.commit_author_dict.get(author.lower(), [])

    def search_commit_word(self, word):
        """
        단어 역색인 딕셔너리를 활용하여 메시지에 특정 단어가 포함된 커밋 ID 목록을 조회합니다.

        :param word: 검색할 단어 (소문자 표준화 권장)
        :return: 해당 단어를 포함하는 커밋 ID 리스트 (없을 시 빈 리스트)
        """
        return self.commit_word_dict.get(word, [])

    def tokenizer(self, string):
        """
        커밋 메시지를 단어 토큰 단위로 분리하고 소문자로 변환하여 정문화합니다.

        :param string: 분리할 문자열
        :return: 소문자로 변환된 단어 토큰 리스트
        """
        # 공백 문자 기준으로 분리하고 빈 토큰 제거 후 소문자 변환
        result = [token.lower() for token in string.split(" ") if token]
        return result

    def get_all_ancestors(self, commit_id, visited_set=None):
        """
        특정 커밋으로부터 도달 가능한 모든 조상 커밋(자기 자신 포함)을 깊이 우선 탐색(DFS) 방식으로 수집합니다.
        파이썬의 재귀 호출 제한(Stack Overflow) 문제를 방지하기 위해 명시적인 스택 자료구조를 사용하는
        반복적 DFS(Iterative DFS) 방식으로 구현되었습니다.
        의미론적으로 올바른 집합 자료구조(Set ADT)를 리턴하여 중복을 허용하지 않고 검출 속도를 O(1)로 가져갑니다.

        :param commit_id: 조상을 탐색할 기준 커밋 ID
        :param visited_set: 방문 여부를 기록할 집합 (visited_set = set())
        :return: 방문 마킹된 커밋 ID 집합
        """
        if visited_set is None:
            visited_set = set()

        if not commit_id or commit_id not in self.commit_dict:
            return visited_set

        # 탐색을 위한 스택 초기화 (시작 노드 투입)
        stack = [commit_id]

        while stack:
            curr = stack.pop()
            if curr not in visited_set:
                visited_set.add(curr)  # 방문 처리
                
                # 현재 노드의 부모들을 역순으로 스택에 추가 (DFS 순서 유지)
                parents = self.commit_dict[curr].parents
                for p in reversed(parents):
                    if p not in visited_set:
                        stack.append(p)

        return visited_set

    def find_common_ancestor(self, main_commit_id, feature_commit_id):
        """
        두 브랜치 커밋(main 및 feature)의 가장 가까운 공통 조상(Lowest Common Ancestor, LCA)을 찾습니다.
        첫 번째 커밋의 모든 조상들을 구한 뒤, 두 번째 커밋으로부터 역방향 너비 우선 탐색(BFS)을 진행하여
        가장 먼저 만나는 공통 분기점을 검출합니다. (3-Way Merge의 핵심 기반이 됩니다.)
        이전의 경로 복사 연산(history + [p])을 제거하고, 부모 포인터 테이블(parent_map)을 이용해 
        LCA 발견 시에만 단 1회 역추적하여 경로를 복구함으로써 시간 및 공간 복잡도를 O(V)로 최적화했습니다.

        :param main_commit_id: 첫 번째 브랜치(main 등)의 최신 커밋 ID
        :param feature_commit_id: 두 번째 브랜치(feature 등)의 최신 커밋 ID
        :return: (공통 조상 커밋 ID, feature에서 조상까지의 탐색 경로 역사) 튜플, 없을 시 None
        """
        # main 커밋의 모든 조상 집합을 먼저 수집
        main_ancestors = self.get_all_ancestors(main_commit_id)

        # BFS를 위한 큐 초기화 (인덱스 포인터를 활용한 O(1) 큐 동작 및 parent_map 부모 포인터 기록 적용)
        queue = [feature_commit_id]
        queue_point = 0
        visited = {feature_commit_id}
        parent_map = {}

        lca_id = None
        while queue_point < len(queue):
            current_id = queue[queue_point]
            queue_point += 1

            # main 조상 집합과 겹치는 지점을 가장 먼저 발견하면 그 노드가 LCA임
            if current_id in main_ancestors:
                lca_id = current_id
                break

            # 부모 방향으로 너비 우선 탐색 확장
            for p in self.commit_dict[current_id].parents:
                if p not in visited:
                    visited.add(p)
                    parent_map[p] = current_id  # p 노드에 도달하기 직전의 노드가 current_id임을 기입
                    queue.append(p)

        if lca_id is None:
            return None

        # LCA 노드부터 부모 포인터를 역추적하여 feature_commit_id까지 도달하는 탐색 경로(history)를 복원
        history = []
        curr = lca_id
        while curr != feature_commit_id:
            history.append(curr)
            curr = parent_map[curr]
        history.append(feature_commit_id)
        history.reverse()

        return lca_id, history

    def find_shortest_path(self, start_hash, end_hash):
        """
        두 커밋 사이의 최단 경로(경로상 간선 개수가 최소인 루트)를 BFS(너비 우선 탐색)로 탐색합니다.
        부모 방향과 자식 방향 모두 이동할 수 있는 무방향(Undirected) 간선으로 취급하여, 자식 방향 검색 시
        캐싱된 자식 노드 역색인 테이블(children_dict)을 조회하여 스캔 성능을 O(1)로 달성합니다.
        동일한 최단 길이를 가지는 다중 경로가 존재할 경우, 사전순(Lexicographical)으로 가장 앞서는 경로를 선택합니다.

        :param start_hash: 시작 커밋 ID
        :param end_hash: 대상 커밋 ID
        :return: 시작부터 끝까지의 커밋 ID 순차 리스트, 경로가 없는 경우 None
        """
        if start_hash not in self.commit_dict or end_hash not in self.commit_dict:
            return None

        if start_hash == end_hash:
            return [start_hash]

        # BFS를 위한 경로 저장용 큐
        paths_queue = [[start_hash]]
        visited = {start_hash}
        found_paths = []

        # 레벨 단위 BFS 수행
        while paths_queue and not found_paths:
            next_queue = []
            level_visited = set()

            for path in paths_queue:
                current = path[-1]

                # 무방향 간선 구성을 위해 부모 커밋들과 자식 커밋들을 합칩니다.
                parents = self.commit_dict[current].parents
                children = self.children_dict.get(current, [])
                neighbors = set(parents) | set(children)

                for neighbor in neighbors:
                    if neighbor == end_hash:
                        # 목적지 도달 시 후보 경로로 수집
                        found_paths.append(path + [neighbor])
                    elif neighbor not in visited:
                        next_queue.append(path + [neighbor])
                        level_visited.add(neighbor)
            
            # 같은 수준의 탐색이 완료되면 방문 처리를 업데이트하여 중복 탐색 차단
            visited.update(level_visited)
            paths_queue = next_queue

        if not found_paths:
            return None

        # 다중 최단 경로 발생 시 tie-breaker: 경로를 정수로 변환하여 비교
        best_path = None
        best_key = None
        for path in found_paths:
            path_key = tuple(int(x) for x in path)
            if best_key is None or path_key < best_key:
                best_key = path_key
                best_path = path

        return best_path

    def topological_sort(self):
        """
        전체 커밋 그래프의 위상 정렬(Topological Sort) 결과를 반환합니다.
        부모 커밋이 항상 자식 커밋보다 정렬 결과 상에서 앞서도록 배치합니다.
        Kahn의 진입 차수(In-degree) 감소 기반 알고리즘을 사용하며, 캐싱된 children_dict를 
        증분 계산(Incremental Computation)에 활용하여 연산 속도를 보장합니다.

        :return: 위상 정렬된 커밋 ID 목록
        """
        # 각 커밋의 진입 차수(In-degree)를 부모 개수로 설정 (루트 커밋은 0)
        in_degree = {c_hash: len(c_obj.parents) for c_hash, c_obj in self.commit_dict.items()}

        # 진입 차수가 0인 커밋들을 대기열에 삽입
        queue = [c_hash for c_hash, deg in in_degree.items() if deg == 0]

        result = []
        queue_point = 0

        # 대기열 순회하며 정렬 리스트 빌드
        while queue_point < len(queue):
            curr = queue[queue_point]
            queue_point += 1
            result.append(curr)

            # 인접 자식 노드들의 진입 차수를 하나씩 낮추며, 0이 되면 대기열 추가
            for child in self.children_dict.get(curr, []):
                in_degree[child] -= 1
                if in_degree[child] == 0:
                    queue.append(child)

        return result
