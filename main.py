import cmd
import shlex
from mini_git import Git, MergeConflictError, quick_sort
from functools import wraps
from datetime import datetime


def require_init(func):
    """저장소가 초기화되었는지(self.git이 생성되었는지) 확인하는 데코레이터"""

    @wraps(func)
    def wrapper(self, arg):
        if self.git is None:
            print("Error: Repository not initialized. Run 'INIT <user_name>' first.")
            return False
        return func(self, arg)

    wrapper.__doc__ = func.__doc__
    wrapper.__name__ = func.__name__
    return wrapper


def args_to_list(func):
    @wraps(func)
    def wrapper(self, arg):
        # 문자열을 리스트로 분리
        try:
            args_list = shlex.split(arg)
        except ValueError:
            print("Invalid args")
            return False
        # 실제 메서드에는 리스트를 넘겨줌
        return func(self, args_list)

    return wrapper


class GitShell(cmd.Cmd):
    prompt = "mini-git> "
    intro = '=== Welcome to Mini Git CLI ===\nType "HELP" to list commands.\n'

    def __init__(self):
        super().__init__()
        self.git:Git|None = None
        
    def _print_commits(self, commits):
        """커밋 리스트를 형식에 맞춰 출력하는 헬퍼 메서드"""
        for commit in commits:
            if self.git is not None:
                pointing_branches = [br for br, c_hash in self.git.branches.items() if c_hash == commit.hash]
            branch_str = f"[{', '.join(pointing_branches)}]" if pointing_branches else ""
            dt = datetime.fromtimestamp(commit.timestamp)
            date_str = dt.strftime("%Y-%m-%d %H:%M:%S")
            print(f"commit {commit.hash} ({commit.author}, {date_str}){branch_str}")
            print(f"FileMeta: {commit.file_meta}")
            print(commit.message)
            print()

    def custom_sort(self, arr):
        """
        내장 정렬(sorted(), list.sort())을 대체하기 위해 직접 구현한 퀵 정렬 함수입니다.
        """
        return quick_sort(arr)

    def do_EXIT(self, arg):
        """프로그램을 종료합니다."""
        print("exit")
        return True

    def do_QUIT(self, arg):
        """프로그램을 종료합니다."""
        return self.do_EXIT(arg)
    def do_EOF(self, arg):
        """Ctrl+D(EOF) 입력 시 프로그램을 안전하게 종료합니다."""
        print()  # 화면에 개행(줄바꿈)을 한 번 깔끔하게 넣어줍니다.
        return self.do_EXIT(arg)  # do_EXIT를 호출하여 종료(True 반환)시킵니다.

    def emptyline(self):
        """빈 줄(엔터)이 입력되었을 때 아무 동작도 하지 않도록 설정"""
        pass

    def precmd(self, line):
        strip_result = line.strip()
        if not strip_result:
            return strip_result
        parts = strip_result.split(maxsplit=1)
        parts[0] = parts[0].upper()
        return " ".join(parts)

    @args_to_list
    def do_INIT(self, arg):
        """INIT <user_name> : 저장소를 초기화하고 작성자를 등록합니다."""
        # arg = shlex.split(arg)
        if len(arg) != 1:
            print("Invalid args")
            return False
        user_name = arg[0]
        if self.git is None:
            self.git = Git(user_name)
            print("Initialized repository.")
        else:
            self.git.user = user_name
            self.git.users.add(user_name)
            print("Reinitialized existing repository.")
        print("Current branch:", self.git.current_branch)
        print(f"Current user: {user_name}")
        return False

    @require_init
    @args_to_list
    def do_USERLIST(self, arg):
        """USERLIST : 등록된 모든 유저 목록과 현재 활성 유저를 출력합니다."""
        if len(arg) > 0:
            print("Invalid args")
            return False
        if self.git is not None:
            print(f"Current user: {self.git.user}")
            users = set(self.git.users)

            for commit in self.git.graph.commit_dict.values():
                users.add(commit.author)
            print("Registered users:")

            for u in self.custom_sort(list(users)):
                if u == self.git.user:
                    print(f"* {u}")
                else:
                    print(f"  {u}")
            return False

    @require_init
    @args_to_list
    def do_BRANCH(self, arg):
        """BRANCH [branch_name] : 브랜치를 생성하거나 목록을 조회합니다."""
        if len(arg) == 0 or (len(arg) == 1 and arg[0].upper() == "LIST"):
            if self.git is not None:
                for br in self.custom_sort(list(self.git.branches.keys())):
                    if br == self.git.current_branch:
                        print(f"* {br}")
                    else:
                        print(f"  {br}")

            return False

        if len(arg) != 1:
            print("Invalid args")
            return False

        #self.git.add_branch(arg[0])
        try:
            if self.git is not None:
                self.git.add_branch(arg[0])
                print(f"Created branch: {arg[0]}")
        except ValueError as e:
            print(e)
        return False

    @require_init
    @args_to_list
    def do_SWITCH(self, arg):
        """SWITCH <branch_name> : 활성화된 브랜치를 변경합니다."""
        if len(arg) != 1:
            print("Invalid args")
            return False

        #self.git.switch_branch(arg[0])
        try:
            if self.git is not None:
                self.git.switch_branch(arg[0])
                print(f"Switched to branch: {arg[0]}")
        except ValueError as e:
            print(e)
        return False

    @require_init
    @args_to_list
    def do_COMMIT(self, arg):
        """COMMIT <message> [file_name:content ...] : 커밋을 생성합니다."""
        if len(arg) < 1:
            print("Invalid args")
            return False

        message = arg[0]
        file_meta = {}
        invalid = False
        for file_str in arg[1:]:
            if ":" not in file_str:
                invalid = True
                break
            file_name, content = file_str.split(":", 1)
            file_meta[file_name] = content

        if invalid:
            print("Invalid args")
            return False

        #self.git.commit(message, file_meta)
        if self.git is not None:
            commit_id = self.git.commit(message, file_meta)
            print(f"[{self.git.current_branch} {commit_id}] {message}")
        return False

    @require_init
    @args_to_list
    def do_LOG(self, arg):
        """LOG [--sort-by=date|author] : 커밋 히스토리를 출력합니다."""
        if self.git is not None:
            if len(arg) == 0:
                commits = self.git.log()
                if not commits:
                    print("No commit")
                else:
                    self._print_commits(commits)
            elif len(arg) == 1 and arg[0].startswith("--sort-by="):
                sort_criteria = arg[0].split("=")[1]
                try:
                    commits = self.git.log_sorted(sort_criteria)
                    if not commits:
                        print("No commit")
                    else:
                        self._print_commits(commits)
                except ValueError as e:
                    print(e)
                #self.git.log_sorted(sort_criteria)
            else:
                print("Invalid args")
            return False

    @require_init
    @args_to_list
    def do_SHOW(self, arg):
        """SHOW [commit_hash] : 커밋의 상세 정보와 file_meta를 출력합니다."""
        
        if len(arg) > 1:
            print("Invalid args")
            return False

        if self.git is not None:
                        
            if len(arg) == 0:
                
                target_commit_id = self.git.branches[self.git.current_branch]
                if target_commit_id is None:
                    print("No commit")
                    return False
            else:
                target_commit_id = arg[0]
                if target_commit_id not in self.git.graph.commit_dict:
                    print(f"Unknown commit: {target_commit_id}")
                    return False

            commit = self.git.graph.commit_dict[target_commit_id]
            dt = datetime.fromtimestamp(commit.timestamp)
            date_str = dt.strftime("%Y-%m-%d %H:%M:%S")
            poingting_branchs = [
                br for br, c_hash in self.git.branches.items() if c_hash == target_commit_id
            ]
            branch_str = f"[{', '.join(poingting_branchs)}]" if poingting_branchs else ""

            print(f"commit {commit.hash} ({commit.author}, {date_str}){branch_str}")
            print(f"FileMeta: {commit.file_meta}")
            print(f"Message: {commit.message}")
            return False

    @require_init
    @args_to_list
    def do_PATH(self, arg):
        """PATH <commit1> <commit2> : 두 커밋 사이의 최단 경로를 출력합니다."""
        if len(arg) != 2:
            print("Invalid args")
            return False
        commit_1, commit_2 = arg[0], arg[1]
        if self.git is not None:
                
            if commit_1 not in self.git.graph.commit_dict:
                print(f"Unknown commit: {commit_1}")
                return False
            if commit_2 not in self.git.graph.commit_dict:
                print(f"Unknown commit: {commit_2}")
                return False

            path_result = self.git.get_path(commit_1, commit_2)
        if path_result == "No path":
            print("No path")
        else:
            print(f"Path: {path_result}")
        return False

    @require_init
    @args_to_list
    def do_ANCESTORS(self, arg):
        """ANCESTORS <commit_hash> : 해당 커밋의 모든 조상 커밋 목록을 출력합니다."""
        if len(arg) != 1:
            print("Invalid args")
            return False
        commit_hash = arg[0]
        if self.git is not None:
            if commit_hash not in self.git.graph.commit_dict:
                print(f"Unknown commit: {commit_hash}")
                return False

            ancestors_dict = self.git.graph.get_all_ancestors(commit_hash)
            ancestors = [h for h in ancestors_dict if h != commit_hash]
            print(", ".join(ancestors))
        return False

    @require_init
    @args_to_list
    def do_SEARCH(self, arg):
        """SEARCH <keyword> | SEARCH --author=<name> : 커밋을 검색합니다."""
        if len(arg) != 1:
            print("Invalid args")
            return False

        search_arg = arg[0]
        if self.git is not None:
            if search_arg.startswith("--author="):
                author_name = search_arg.split("=")[1].strip("'\"")
                results = self.git.search_by_author(author_name)
            else:
                results = self.git.search_by_keyword(search_arg)

        if not results:
            print("Found 0 commits.")
        else:
            print(f"Found {len(results)} commit:")
            for c in results:
                print(f"- {c.hash} {c.message}")
        return False

    @require_init
    @args_to_list
    def do_MERGE(self, arg):
        """MERGE <branch_name> : 지정한 브랜치를 현재 브랜치에 병합합니다."""
        if len(arg) != 1:
            print("Invalid args")
            return False
        #self.git.merge(arg[0])
        target_branch = arg[0]
        try:
            if self.git is not None:
                self.git.merge(target_branch)
                print(f"Successfully merged branch '{target_branch}' into '{self.git.current_branch}'.")
        except ValueError as e:
            print(e)
        except MergeConflictError as e:
            for file_name, conflict_text in e.conflicts.items():
                print(f"충돌 발생: {file_name}")
                print(conflict_text)
            print("충돌 해결후 커밋")
        return False
        

    @require_init
    @args_to_list
    def do_DIFF(self, arg):
        """DIFF <file1> <file2> : 두 텍스트 파일을 줄 단위로 비교하여 차이점을 출력합니다."""
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

    def do_HELP(self, arg):
        """HELP [command] : 도움말 목록을 보거나 특정 명령어의 사용법을 봅니다."""
        super().do_help(arg.upper())
        
    def get_names(self):
        """도움말 명령어 목록을 가져올 때, 숨기고 싶은 명령어(EOF, 소문자 help)를 제외시킵니다."""
        # 1. 부모 클래스가 찾아낸 do_* 메서드 이름 목록을 가져옵니다.
        names = super().get_names()
        
        # 2. 숨기고 싶은 대상 정의 (do_접두사 포함)
        exclude = {'do_EOF', 'do_help'}
        
        # 3. 제외 대상들을 필터링하여 반환합니다.
        return [name for name in names if name not in exclude]


def main():
    try:
        GitShell().cmdloop()
    except KeyboardInterrupt:
        print("\nExiting...") 
    


if __name__ == "__main__":
    main()
