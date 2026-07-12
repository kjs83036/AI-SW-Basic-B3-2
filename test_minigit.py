import unittest
import time
import random
import io
import contextlib
from commit_graph import Commit, CommitGraph
from mini_git import Git
from main import GitShell # type: ignore

class TestMiniGitSRS(unittest.TestCase):

    def setUp(self):
        # 각 테스트 실행 전 Alice 사용자로 Git 저장소 초기화 (CLI를 통해 수행)
        self.shell = GitShell()
        self.shell.onecmd("INIT Alice")

    @property
    def git(self):
        return self.shell.git

    @git.setter
    def git(self, value):
        self.shell.git = value

    def run_cmd(self, line):
        """CLI 명령어를 실행하고, 그에 따른 표준 출력(stdout)을 수집하여 반환합니다."""
        f = io.StringIO()
        original_stdout = self.shell.stdout
        with contextlib.redirect_stdout(f):
            self.shell.stdout = f
            self.shell.onecmd(line)
        self.shell.stdout = original_stdout
        return f.getvalue().rstrip('\r\n')

    def test_help_command(self):
        """HELP 명령어 출력 검증 (1번 기능)"""
        output = self.run_cmd("HELP")
        self.assertIn("Documented commands (type help <topic>):", output)
        self.assertIn("COMMIT", output)
        self.assertIn("HELP", output)

    def test_init_and_commit(self):
        """INIT 및 COMMIT 기능 검증 (메타데이터 및 브랜치 포인터 갱신)"""
        # 첫 번째 커밋 생성 (CLI 사용)
        output = self.run_cmd("COMMIT 'Initial commit' file1.txt:hello")
        c1 = "1"
        self.assertIn(f"[main {c1}] Initial commit", output)
        self.assertEqual(self.git.branches["main"], c1)
        
        # 커밋 객체 검증 (SRS 최소 필드: hash, message, author, timestamp, parents)
        commit_obj = self.git.graph.commit_dict[c1]
        self.assertEqual(commit_obj.hash, c1)
        self.assertEqual(commit_obj.message, "Initial commit")
        self.assertEqual(commit_obj.author, "Alice")
        self.assertIsNotNone(commit_obj.timestamp)
        self.assertEqual(commit_obj.parents, [])

    def test_branch_and_switch(self):
        """BRANCH 및 SWITCH 기능 검증 (브랜치 포인터 분기 및 독립)"""
        self.run_cmd("COMMIT First")
        c1 = "1"
        
        # 브랜치 생성 및 전환 (CLI 사용)
        out_branch = self.run_cmd("BRANCH feature")
        self.assertIn("Created branch: feature", out_branch)
        self.assertEqual(self.git.branches["feature"], c1) # 생성 시점엔 같은 커밋 가리킴
        
        out_switch = self.run_cmd("SWITCH feature")
        self.assertIn("Switched to branch: feature", out_switch)
        self.assertEqual(self.git.current_branch, "feature")
        
        # feature 브랜치에서 신규 커밋 (CLI 사용)
        self.run_cmd("COMMIT 'Second on feature'")
        c2 = "2"
        self.assertEqual(self.git.branches["feature"], c2)
        self.assertEqual(self.git.branches["main"], c1) # main 브랜치는 여전히 c1에 머묾

    def test_topological_sort_log(self):
        """LOG의 위상 정렬(Topological Sort) 검증 (부모가 항상 자식보다 먼저 출력되는가)"""
        # Graph 구조: c1 -> c2 -> c3 (CLI 사용)
        self.run_cmd("COMMIT C1")
        self.run_cmd("COMMIT C2")
        self.run_cmd("COMMIT C3")
        c1, c2, c3 = "1", "2", "3"
        
        # LOG 명령어로 출력 캡처
        output = self.run_cmd("LOG")
        
        # 위상 정렬 순서 상 부모(c1)가 항상 자식(c2, c3)보다 먼저 등장해야 함
        idx1 = output.index(f"commit {c1}")
        idx2 = output.index(f"commit {c2}")
        idx3 = output.index(f"commit {c3}")
        
        self.assertTrue(idx1 < idx2 < idx3)

    def test_custom_sorting_log(self):
        """LOG --sort-by 정렬 알고리즘 검증 (내장 정렬 사용 우회 및 올바른 정렬 여부)"""
        # 서로 다른 시간차를 두고 커밋 생성 (CLI 사용)
        self.run_cmd("INIT Charlie")
        self.run_cmd("COMMIT 'Commit 1'")
        time.sleep(0.01)
        self.run_cmd("INIT Bob")
        self.run_cmd("COMMIT 'Commit 2'")
        time.sleep(0.01)
        self.run_cmd("INIT Alice")
        self.run_cmd("COMMIT 'Commit 3'")
        
        c1, c2, c3 = "1", "2", "3"
        
        # 1. Date 기준 정렬 검증 (LOG --sort-by=date) (C1 -> C2 -> C3 순)
        output_date = self.run_cmd("LOG --sort-by=date")
        idx1 = output_date.index(f"commit {c1}")
        idx2 = output_date.index(f"commit {c2}")
        idx3 = output_date.index(f"commit {c3}")
        self.assertTrue(idx1 < idx2 < idx3)
        
        # 2. Author 기준 정렬 검증 (LOG --sort-by=author) (Alice -> Bob -> Charlie 순, 즉 C3 -> C2 -> C1 순)
        output_author = self.run_cmd("LOG --sort-by=author")
        idx3_auth = output_author.index(f"commit {c3}")
        idx2_auth = output_author.index(f"commit {c2}")
        idx1_auth = output_author.index(f"commit {c1}")
        self.assertTrue(idx3_auth < idx2_auth < idx1_auth)

    def test_shortest_path_undirected(self):
        """PATH 최단 경로 알고리즘 검증 (무방향 최단 거리 및 사전순 최소 경로 선택)"""
        # Graph 구조 구축 (CLI 사용)
        # 1 -> 2 -> 4
        # 1 -> 3 -> 4
        # 2개 경로(1->2->4 와 1->3->4)의 길이는 같으나, 사전순으로 '1->2->4'가 작음
        self.run_cmd("COMMIT C1")
        self.run_cmd("BRANCH br_two")
        self.run_cmd("BRANCH br_three")
        
        self.run_cmd("SWITCH br_two")
        self.run_cmd("COMMIT C2")
        
        self.run_cmd("SWITCH br_three")
        self.run_cmd("COMMIT C3")
        
        # C4는 C2와 C3를 병합(Merge)한 커밋
        self.run_cmd("SWITCH br_two")
        self.run_cmd("MERGE br_three")
        
        c1, c2, c3, c4 = "1", "2", "3", "4"
        
        # 1에서 4로 가는 최단 경로 탐색
        output = self.run_cmd(f"PATH {c1} {c4}")
        self.assertIn(f"Path: {c1}->{c2}->{c4}", output)

    def test_ancestors(self):
        """ANCESTORS 조상 탐색 검증"""
        self.run_cmd("COMMIT C1")
        self.run_cmd("COMMIT C2")
        self.run_cmd("COMMIT C3")
        c1, c2, c3 = "1", "2", "3"
        
        output = self.run_cmd(f"ANCESTORS {c3}")
        # 자기 자신(c3)을 제외한 실제 조상 해시들만 쉼표로 구분하여 출력
        self.assertIn(c1, output)
        self.assertIn(c2, output)
        self.assertNotIn(c3, output)

    def test_inverted_index_search(self):
        """역색인(Inverted Index) 기반 SEARCH 검증"""
        self.run_cmd("COMMIT 'Add login button and forms'")
        self.run_cmd("INIT Bob")
        self.run_cmd("COMMIT 'Fix pay system crash'")
        c1, c2 = "1", "2"
        
        # 키워드 검색 검증
        out_keyword = self.run_cmd("SEARCH login")
        self.assertIn(f"- {c1} Add login button and forms", out_keyword)
        
        # 대소문자 무구분 검색 검증
        out_keyword_caps = self.run_cmd("SEARCH LOGIN")
        self.assertIn(f"- {c1} Add login button and forms", out_keyword_caps)
        
        # 작성자 검색 검증
        out_author = self.run_cmd("SEARCH --author=Bob")
        self.assertIn(f"- {c2} Fix pay system crash", out_author)

    def test_three_way_merge_and_conflict(self):
        """3-Way Merge의 자동 병합 및 충돌(Conflict) 검증"""
        # Base Commit 생성 후 feature 분기
        self.run_cmd("COMMIT 'Base Commit' file1.txt:original")
        self.run_cmd("BRANCH feature")
        
        # main 변경: file1="main_ver"
        self.run_cmd("COMMIT 'Main change' file1.txt:main_ver")
        
        # feature 분기 후 변경: file1="feat_ver"
        self.run_cmd("SWITCH feature")
        self.run_cmd("COMMIT 'Feature change' file1.txt:feat_ver")
        
        # main과 feature 병합 시도 -> 충돌이 발생해야 함
        self.run_cmd("SWITCH main")
        out_merge = self.run_cmd("MERGE feature")
        self.assertIn("충돌", out_merge)
        self.assertIn("충돌 해결후 커밋", out_merge)

    def test_three_way_merge_no_common_ancestor(self):
        """공통 조상이 없는 독립적인 루트 트리를 가지는 브랜치 간의 병합 처리 검증"""
        # 독립적인 새로운 git 구조 재설정 시뮬레이션
        self.git = None
        self.run_cmd("INIT abcd")
        self.run_cmd("BRANCH 1234")
        self.run_cmd("SWITCH 1234")
        self.run_cmd("COMMIT '아무거나' file:content") # c1 생성 (1234 브랜치)
        
        self.run_cmd("SWITCH main")
        self.run_cmd("COMMIT '와따' test.txt:asdfff") # c2 생성 (main 브랜치 루트)
        self.run_cmd("COMMIT '라스트' tete:123asdf") # c3 생성
        
        # 공통 조상이 전혀 없는 상태에서 merge 시도
        out_merge = self.run_cmd("MERGE 1234")
        self.assertIn("오류: 공통 조상을 찾을 수 없어 머지를 중단", out_merge)

    def test_stress_and_performance(self):
        """100개 가상 커밋 대용량 생성 스트레스 테스트 및 역색인/정렬 알고리즘 성능/무결성 통합 검증"""
        # 재현 가능성을 위해 무작위 시드 고정
        random.seed(42)

        # 1. 100개의 가상 커밋 생성
        keywords = ["login", "payment", "signup", "search", "checkout", "auth", "profile", "settings", "database", "ui"]
        authors = ["Alice", "Bob", "Charlie", "Dave", "Eve"]
        branches = ["main"]
        
        # 최초 루트 커밋
        self.run_cmd("COMMIT 'Initial root commit' file:init")
        first_commit = "1"
        last_commit = first_commit
        commit_id_counter = 1
        
        # 100개의 커밋 생성 루프 (주기적인 분기, 스위칭, 병합 포함)
        for i in range(1, 101):
            if i % 15 == 0:
                new_br = f"feature-{i}"
                self.run_cmd(f"BRANCH {new_br}")
                branches.append(new_br)
            
            if i % 10 == 0:
                target_br = random.choice(branches)
                self.run_cmd(f"SWITCH {target_br}")
                
            if i % 25 == 0 and len(branches) > 1:
                current = self.git.current_branch
                other = random.choice([b for b in branches if b != current])
                if self.git.branches[current] and self.git.branches[other]:
                    out_merge = self.run_cmd(f"MERGE {other}")
                    if "Successfully merged" in out_merge:
                        commit_id_counter += 1
                        last_commit = str(commit_id_counter)
                        continue
            
            msg = f"Commit {i}: {random.choice(keywords)} {random.choice(keywords)} feature"
            author = random.choice(authors)
            self.run_cmd(f"INIT {author}") # user 변경
            self.run_cmd(f"COMMIT '{msg}' file_{i}.txt:content_{i}")
            commit_id_counter += 1
            last_commit = str(commit_id_counter)

        # 생성 완료 후 데이터 검증
        self.assertEqual(len(self.git.graph.commit_dict), commit_id_counter)
        self.assertTrue(len(self.git.branches) > 1)

        # 2. 최단 경로 탐색 검증
        path_result = self.run_cmd(f"PATH {first_commit} {last_commit}")
        self.assertTrue("Path:" in path_result)

        # 3. 역색인(Inverted Index) 검색과 선형 순회 비교 검증
        search_kw = "login"
        results_idx_str = self.run_cmd(f"SEARCH {search_kw}")
        
        results_linear = []
        for c in self.git.graph.commit_dict.values():
            if search_kw in [t.lower() for t in c.message.split(" ") if t]:
                results_linear.append(c)
                
        import re
        m = re.search(r"Found (\d+) commit", results_idx_str)
        found_cnt = int(m.group(1)) if m else 0
        self.assertEqual(found_cnt, len(results_linear))

        # 4. 사용자 정의 정렬 알고리즘(Merge Sort) 정렬 성능 검증
        commits = list(self.git.graph.commit_dict.values())
        
        # 날짜순 정증 (순서가 단조 증가하는지 확인)
        sorted_by_date = self.merge_sort_helper(commits, lambda c: c.timestamp)
        for idx in range(len(sorted_by_date) - 1):
            self.assertTrue(sorted_by_date[idx].timestamp <= sorted_by_date[idx + 1].timestamp)
            
        # 작성자순 정렬 검증 (순서가 사전순으로 단조 증가하는지 확인)
        sorted_by_author = self.merge_sort_helper(commits, lambda c: c.author.lower())
        for idx in range(len(sorted_by_author) - 1):
            self.assertTrue(sorted_by_author[idx].author.lower() <= sorted_by_author[idx + 1].author.lower())

    def test_quit_exit_command(self):
        """QUIT 및 EXIT 명령어 종료 동작 검증"""
        f = io.StringIO()
        with contextlib.redirect_stdout(f):
            should_exit = self.shell.onecmd("QUIT")
        self.assertTrue(should_exit)
        self.assertIn("exit", f.getvalue())

        f2 = io.StringIO()
        with contextlib.redirect_stdout(f2):
            should_exit2 = self.shell.onecmd("EXIT")
        self.assertTrue(should_exit2)
        self.assertIn("exit", f2.getvalue())

    def test_branch_list_command(self):
        """BRANCH LIST 기능 검증"""
        self.run_cmd("BRANCH feature-br")
        # 단독 BRANCH 또는 BRANCH LIST 입력 시 목록 표출 검증
        out_list = self.run_cmd("BRANCH")
        self.assertIn("* main", out_list)
        self.assertIn("  feature-br", out_list)

        out_list2 = self.run_cmd("BRANCH LIST")
        self.assertIn("* main", out_list2)
        self.assertIn("  feature-br", out_list2)

    def test_user_list_command(self):
        """USERLIST 기능 검증"""
        # 커밋이 없는 상태에서의 다중 INIT 유저 보존 테스트
        self.git = None
        self.run_cmd("INIT 1234")
        self.run_cmd("INIT 2345")
        out_no_commit = self.run_cmd("USERLIST")
        self.assertIn("Current user: 2345", out_no_commit)
        self.assertIn("  1234", out_no_commit)
        self.assertIn("* 2345", out_no_commit)

        # 기존 커밋 생성 후 등록 유저 테스트
        self.git = None
        self.run_cmd("INIT Alice")
        self.run_cmd("COMMIT 'init commit'")
        self.run_cmd("INIT Bob")
        self.run_cmd("COMMIT 'bob commit'")
        
        # USERLIST 명령어 결과 검증
        out_users = self.run_cmd("USERLIST")
        self.assertIn("Current user: Bob", out_users)
        self.assertIn("Registered users:", out_users)
        self.assertIn("  Alice", out_users) # 이력에 남은 이전 유저
        self.assertIn("* Bob", out_users)   # 현재 유저



    def test_show_command(self):
        """SHOW 명령어의 최신/지정 커밋 상세 및 file_meta 정보 출력 검증"""
        self.git = None
        self.run_cmd("INIT Alice")
        self.run_cmd("COMMIT 'First Commit' file1:content1")
        self.run_cmd("COMMIT 'Second Commit' file2:content2")
        
        # 1. 인수 없이 최신 커밋 SHOW 실행 결과 검증
        out_latest = self.run_cmd("SHOW")
        self.assertIn("commit 2 (Alice", out_latest)
        self.assertIn("FileMeta: {'file2': 'content2'}", out_latest)
        self.assertIn("Message: Second Commit", out_latest)

        # 2. 특정 커밋 해시 지정하여 SHOW 실행 결과 검증
        out_specific = self.run_cmd("SHOW 1")
        self.assertIn("commit 1 (Alice", out_specific)
        self.assertIn("FileMeta: {'file1': 'content1'}", out_specific)
        self.assertIn("Message: First Commit", out_specific)

        # 3. 존재하지 않는 커밋 해시 에러 검증
        out_invalid = self.run_cmd("SHOW 999")
        self.assertIn("Unknown commit: 999", out_invalid)

    def merge_sort_helper(self, arr, key_func):
        """테스트 검증용 병합 정렬 헬퍼"""
        if len(arr) <= 1:
            return arr
        mid = len(arr) // 2
        left = self.merge_sort_helper(arr[:mid], key_func)
        right = self.merge_sort_helper(arr[mid:], key_func)
        
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

    def test_shortest_path_numeric_tie_breaker(self):
        """숫자 문자열 ID를 사용한 다중 최단 경로 발생 시 tie-breaker가 정수순으로 제대로 동작하는지 검증"""
        # 1 -> 3 -> 4 (정수 튜플: (1, 3, 4))
        # 1 -> 21 -> 4 (정수 튜플: (1, 21, 4))
        # 원래 문자열 사전순 비교 시에는 "1->21->4" < "1->3->4" 가 참이 되어 21번 경로가 선택되지만,
        # 정수형 튜플 비교 시에는 (1, 3, 4) < (1, 21, 4) 가 참이 되어 3번 경로가 선택되어야 함.
        from commit_graph import CommitGraph
        graph = CommitGraph()
        
        # 가상의 커밋 그래프 직접 구성
        graph.commit_dict["1"] = Commit(hash="1", message="C1", author="Alice", file_meta={}, parents=[])
        graph.commit_dict["3"] = Commit(hash="3", message="C3", author="Alice", file_meta={}, parents=["1"])
        graph.commit_dict["21"] = Commit(hash="21", message="C21", author="Alice", file_meta={}, parents=["1"])
        graph.commit_dict["4"] = Commit(hash="4", message="C4", author="Alice", file_meta={}, parents=["3", "21"])
        
        # 자식 역색인 캐시 수동 매핑
        graph.children_dict["1"] = ["3", "21"]
        graph.children_dict["3"] = ["4"]
        graph.children_dict["21"] = ["4"]
        
        # 최단 경로 탐색 수행
        path = graph.find_shortest_path("1", "4")
        
        # 3번을 지나는 경로가 반환되었는지 검증 (리스트 타입으로 반환됨)
        self.assertEqual(path, ["1", "3", "4"])

if __name__ == "__main__":
    import sys
    sys.exit(unittest.main(exit=False).result.wasSuccessful() is False)
