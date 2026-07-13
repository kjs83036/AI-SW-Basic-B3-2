from commit_graph import Commit, CommitGraph
from datetime import datetime
import time
from functools import wraps


def measure_time(func):
    """실행 시간을 측정하는 데코레이터"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.perf_counter()
        result = func(*args, **kwargs)
        end_time = time.perf_counter()
        print(f"[Time] {func.__name__} took {end_time - start_time:.8f} seconds")
        return result
    return wrapper


def _merge_sort_recursive(arr, key_func):
    if len(arr) <= 1:
        return arr
    mid = len(arr) // 2
    left = _merge_sort_recursive(arr[:mid], key_func)
    right = _merge_sort_recursive(arr[mid:], key_func)

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


@measure_time
def merge_sort(arr, key_func=lambda x: x):
    """외부 함수로 분리된 병합 정렬 (Stable Sort, O(N log N))"""
    return _merge_sort_recursive(arr, key_func)


def _quick_sort_recursive(arr, key_func):
    if len(arr) <= 1:
        return arr
    pivot = arr[len(arr) // 2]
    left = [x for x in arr if key_func(x) < key_func(pivot)]
    middle = [x for x in arr if key_func(x) == key_func(pivot)]
    right = [x for x in arr if key_func(x) > key_func(pivot)]
    return _quick_sort_recursive(left, key_func) + middle + _quick_sort_recursive(right, key_func)


@measure_time
def quick_sort(arr, key_func=lambda x: x):
    """외부 함수로 분리된 퀵 정렬 (O(N log N) 평균)"""
    return _quick_sort_recursive(arr, key_func)


class MergeConflictError(Exception):
    """3방향 병합 과정에서 충돌이 발생했음을 나타내는 예외 클래스입니다."""

    def __init__(self, conflicts):
        super().__init__("Merge conflict occurred")
        self.conflicts = conflicts


class Git:
    """
    Git의 고수준 버전 관리 명령을 구현하고 제공하는 메인 컨트롤러 클래스입니다.
    브랜치 관리, 커밋 생성, 위상 정렬 기반 로그 출력, 최단 경로 질의,
    3-Way Merge 및 사용자 정의 병합 정렬 기능을 담당합니다.
    """

    def __init__(self, user):
        """
        Git 객체를 초기화합니다.

        :param user: 현재 세션의 기본 작성자(사용자) 이름
        """
        self.user = user
        self.users = {user}  # 등록된 전체 유저 목록 관리
        self.graph = CommitGraph()  # 공용 커밋 그래프(DAG) 인스턴스 생성
        self.branches: dict[str, str | None] = {
            "main": None
        }  # 브랜치별 매핑 사전 (브랜치명: 가리키는 커밋 ID)
        self.current_branch = "main"  # 현재 활성화된 브랜치 (HEAD)

    def add_branch(self, branch_name):
        """
        현재 HEAD(활성화된 브랜치)가 가리키는 동일한 커밋에 새 브랜치 포인터를 생성합니다.

        :param branch_name: 신규 생성할 브랜치 이름
        """
        if branch_name in self.branches:
            raise ValueError(f"이미존재{branch_name}")
        current_commit = self.branches[self.current_branch]
        self.branches[branch_name] = current_commit

    def switch_branch(self, branch_name):
        """
        활성화된 브랜치(현재 세션의 브랜치)를 대상 브랜치로 전환합니다. (HEAD 변경)

        :param branch_name: 전환할 대상 브랜치 이름
        """
        if branch_name not in self.branches:
            raise ValueError(f"Unknown branch: {branch_name}")

        self.current_branch = branch_name

    def commit(self, message, file_meta, parents=None):
        """
        새로운 커밋을 만들고 현재 브랜치의 포인터를 갱신합니다.
        부모 커밋 목록을 지정하지 않으면 자동으로 현재 브랜치가 가리키던 이전 커밋을 부모로 사용합니다.

        :param message: 커밋 메시지
        :param file_meta: 저장할 파일 메타데이터 딕셔너리 (파일명: 파일내용)
        :param parents: 명시적인 부모 커밋 ID 리스트 (생략 시 현재 활성 브랜치의 최신 커밋을 부모로 지정)
        :return: 새로 생성된 커밋의 고유 ID
        """
        if parents is None:
            current_commit_id = self.branches[self.current_branch]
            if current_commit_id is not None:
                parents = [current_commit_id]
            else:
                parents = []  # 부모가 없는 최초 커밋(Root Commit)

        str_commit_id = self.graph.add_commit(message, self.user, file_meta, parents)
        self.branches[self.current_branch] = (
            str_commit_id  # 현재 브랜치가 최신 커밋을 가리키도록 갱신
        )

        #print(f"[{self.current_branch} {str_commit_id}] {message}")
        return str_commit_id

    def log(self):
        """
        현재 저장소의 모든 커밋 히스토리를 위상 정렬 순서(부모가 항상 자식보다 먼저 출력되는 순서)로 출력합니다.
        """
        sorted_hashes = self.graph.topological_sort()
        if not sorted_hashes:
            #print("No commit")
            return []

        commits = [
            self.graph.commit_dict[h]
            for h in sorted_hashes
            if h in self.graph.commit_dict
        ]
        #self._print_commit_logs(commits)
        return commits

    def three_way_merge(self, main_commit_id, feature_commit_id):
        """
        두 커밋(main 및 feature) 간의 파일 변경 사항에 대해 3방향 병합(3-Way Merge)을 시도합니다.
        두 커밋의 가장 가까운 공통 조상(Base Commit)을 찾아 변경 상태를 판별하며, 충돌 발생 시 conflict 마커를 삽입합니다.

        :param main_commit_id: 현재 활성 브랜치의 최신 커밋 ID
        :param feature_commit_id: 병합할 대상 브랜치의 최신 커밋 ID
        :return: (충돌 유무 플래그, 병합이 완료된 file_meta 결과 딕셔너리) 튜플
        """
        # 1. 두 브랜치의 공통 조상(LCA) 탐색
        ancestor_res = self.graph.find_common_ancestor(
            main_commit_id, feature_commit_id
        )

        if ancestor_res is None:
            raise ValueError("오류: 공통 조상을 찾을 수 없어 머지를 중단")

        base_commit_id, _ = ancestor_res

        # 각 커밋에서의 파일 메타데이터(file_meta) 가져오기
        base_file_meta = self.graph.commit_dict[base_commit_id].file_meta
        main_file_meta = self.graph.commit_dict[main_commit_id].file_meta
        feature_file_meta = self.graph.commit_dict[feature_commit_id].file_meta

        # 세 버전의 파일 목록 전체 수집
        all_files = (
            set(base_file_meta.keys()) | set(main_file_meta.keys()) | set(feature_file_meta.keys())
        )

        merged_file_meta = {}
        conflicts = {}
        has_conflict = False

        # 각 파일에 대해 3방향 상태 판별 알고리즘 수행
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

            # Case D: 양쪽 브랜치가 다르게 변경한 경우 -> 충돌(Conflict) 처리
            else:
                main_val = main_content if main_content is not None else "[파일 없음]"
                feat_val = (
                    feature_content if feature_content is not None else "[파일 없음]"
                )
                conflict_text = (
                    f"<<<<<<< HEAD\n{main_val}\n=======\n{feat_val}\n>>>>>>> REMOTE"
                )
                print(conflict_text)
                merged_file_meta[file_name] = conflict_text
                conflicts[file_name] = conflict_text
                has_conflict = True

        return has_conflict, merged_file_meta, conflicts

    def finalize_merge(self, main_commit_id, feature_commit_id, message="Merge branch"):
        """
        3-Way Merge of success/fail checks, and if there are no conflicts, automatically receives the merged result to create a Merge commit pointing to two parents.

        :param main_commit_id: 현재 활성 브랜치의 최신 커밋 ID
        :param feature_commit_id: 병합할 대상 브랜치의 최신 커밋 ID
        :param message: 병합 커밋 메시지
        :return: 생성된 병합 커밋 ID, 충돌이 있거나 오류 발생 시 None
        """
        merge_result = self.three_way_merge(main_commit_id, feature_commit_id)
        has_conflict, merged_file_meta, conflicts = merge_result
        
        if has_conflict:
            raise MergeConflictError(conflicts)

        # if has_conflict:
        #     print("충돌 해결후 커밋")
        #     return None

        # 두 부모(main_commit_id, feature_commit_id)를 지정하여 병합 커밋 완료
        str_commit_id = self.commit(
            message, merged_file_meta, [main_commit_id, feature_commit_id]
        )

        return str_commit_id

    def merge(self, target_branch):
        """
        현재 활성화된 브랜치에 대상 브랜치(`target_branch`)의 변경 사항을 가져와 병합합니다. (CLI용 래퍼)

        :param target_branch: 가져올 대상 브랜치 이름
        """
        if target_branch not in self.branches:
            #print(f"Unknown branch: {target_branch}")
            raise ValueError(f"Unknown branch: {target_branch}") 

        current_commit = self.branches[self.current_branch]
        target_commit = self.branches[target_branch]

        if current_commit is None or target_commit is None:
            raise ValueError("병합할 커밋이 양쪽 브랜치에 모두 존재해야 합니다.")
            

        merge_commit_id = self.finalize_merge(
            current_commit, target_commit, f"Merge branch '{target_branch}'"
        )
        # if merge_commit_id:
        #     print(
        #         f"Successfully merged branch '{target_branch}' into '{self.current_branch}'."
        #     )
        return merge_commit_id

    def search_by_keyword(self, keyword):
        """
        단어 역색인을 사용하여 커밋 메시지에 키워드가 포함된 커밋들을 빠르게 조회합니다.

        :param keyword: 검색할 키워드 문자열
        :return: 검색 매칭된 Commit 객체 리스트
        """
        commit_hashes = self.graph.search_commit_word(keyword.lower())
        return [
            self.graph.commit_dict[h]
            for h in commit_hashes
            if h in self.graph.commit_dict
        ]

    def search_by_author(self, author):
        """
        작성자 이름 역색인을 사용하여 특정 작성자가 작성한 커밋들을 빠르게 조회합니다.

        :param author: 검색할 작성자 이름
        :return: 작성자가 일치하는 Commit 객체 리스트
        """
        commit_hashes = self.graph.search_commit_author(author.lower())
        return [
            self.graph.commit_dict[h]
            for h in commit_hashes
            if h in self.graph.commit_dict
        ]

    def get_path(self, commit1, commit2):
        """
        두 커밋 사이의 무방향 최단 경로를 구하고 문자열 포맷("1->2->4")으로 가공해 반환합니다.

        :param commit1: 출발지 커밋 ID
        :param commit2: 도착지 커밋 ID
        :return: 화살표로 이은 경로 문자열, 경로가 존재하지 않으면 "No path"
        """
        path = self.graph.find_shortest_path(commit1, commit2)
        if path is None:
            return "No path"
        return "->".join(path)

    def log_sorted(self, sort_by):
        """
        사용자 정의 비교 조건에 따라 커밋 목록을 안정 정렬된 순서로 출력합니다.
        정렬 알고리즘은 내장 API를 배제하고 직접 구현한 병합 정렬(Merge Sort, O(N log N))을 사용합니다.

        :param sort_by: 정렬 기준 ('date' 또는 'author')
        """
        commits = list(self.graph.commit_dict.values())
        if not commits:
            #print("No commit")
            return []

        # 정렬 기준 함수(key_func) 세팅
        if sort_by == "date":
            key_func = lambda c: c.timestamp
        elif sort_by == "author":
            key_func = lambda c: c.author.lower()
        else:
            #print(f"Unknown sort option:{sort_by}")
            raise ValueError(f"Unknown sort option:{sort_by}")
            return

        return merge_sort(commits, key_func)

    def diff(self, file1_path, file2_path):
        """
        두 텍스트 파일을 읽어 줄 단위로 비교하고 추가/삭제/공통 줄을 구분해 반환합니다.
        [이론 20] LCS (Longest Common Subsequence) 알고리즘이 적용되었습니다.
        
        :param file1_path: 첫 번째 파일 경로
        :param file2_path: 두 번째 파일 경로
        :return: 각 라인의 비교 결과를 담은 문자열 리스트
        """
        try:
            with open(file1_path, 'r', encoding='utf-8') as f1:
                lines1 = [line.rstrip('\r\n') for line in f1.readlines()]
        except FileNotFoundError:
            raise FileNotFoundError(f"File not found: {file1_path}")
        except Exception as e:
            raise IOError(f"Error reading {file1_path}: {str(e)}")

        try:
            with open(file2_path, 'r', encoding='utf-8') as f2:
                lines2 = [line.rstrip('\r\n') for line in f2.readlines()]
        except FileNotFoundError:
            raise FileNotFoundError(f"File not found: {file2_path}")
        except Exception as e:
            raise IOError(f"Error reading {file2_path}: {str(e)}")

        # DP 기반 최장 공통 부분 수열(LCS) 계산
        m, n = len(lines1), len(lines2)
        dp = [[0] * (n + 1) for _ in range(m + 1)]

        for i in range(1, m + 1):
            for j in range(1, n + 1):
                if lines1[i - 1] == lines2[j - 1]:
                    dp[i][j] = dp[i - 1][j - 1] + 1
                else:
                    dp[i][j] = max(dp[i - 1][j], dp[i][j - 1])

        # 역추적(Backtracking)하여 Diff 조립
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

