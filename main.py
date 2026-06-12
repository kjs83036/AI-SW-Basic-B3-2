import sys
import time
import datetime
import shlex

# ─────────────────────────────────────────────────────────
# 자료구조
# ─────────────────────────────────────────────────────────

class Commit:
    """커밋 노드: DAG의 단일 노드"""
    def __init__(self, hash_, message, author, timestamp, parents):
        self.hash = hash_
        self.message = message
        self.author = author
        self.timestamp = timestamp  # float (time.time())
        self.parents = parents      # list of hash strings


class Repository:
    """Mini Git 저장소: 커밋 그래프 + 역색인"""
    def __init__(self):
        self.commits = {}           # hash -> Commit (Python 3.7+ dict: 삽입 순서 보장)
        self.branches = {}          # branch_name -> commit_hash or None
        self.HEAD = None            # 현재 브랜치 이름
        self.current_user = None
        self.keyword_index = {}     # keyword(소문자) -> list of hashes
        self.author_index = {}      # author(소문자) -> list of hashes
        self._counter = 0

    def _gen_hash(self):
        """중복 없는 6자리 hex hash 생성 (카운터 기반 → 중복 불가 보장)"""
        self._counter += 1
        return format(self._counter, '06x')

    def _update_index(self, commit):
        """역색인 갱신: author 인덱스 + keyword 인덱스"""
        # author index (소문자 정규화: 대소문자 구분 없는 검색 지원)
        ak = commit.author.lower()
        if ak not in self.author_index:
            self.author_index[ak] = []
        self.author_index[ak].append(commit.hash)

        # keyword index: 메시지를 공백 기준 분리 후 소문자 정규화
        for token in commit.message.split():
            kw = token.lower()
            if kw not in self.keyword_index:
                self.keyword_index[kw] = []
            self.keyword_index[kw].append(commit.hash)


# ─────────────────────────────────────────────────────────
# 정렬 알고리즘 (sorted/list.sort 금지 → 직접 구현)
# ─────────────────────────────────────────────────────────

def merge_sort(arr, key_fn):
    """안정 병합 정렬 O(n log n). Python sorted/list.sort 미사용."""
    if len(arr) <= 1:
        return arr
    mid = len(arr) // 2
    left = merge_sort(arr[:mid], key_fn)
    right = merge_sort(arr[mid:], key_fn)
    return _merge(left, right, key_fn)


def _merge(left, right, key_fn):
    """병합 정렬 보조: 두 정렬된 리스트를 병합"""
    result = []
    i = j = 0
    while i < len(left) and j < len(right):
        if key_fn(left[i]) <= key_fn(right[j]):
            result.append(left[i])
            i += 1
        else:
            result.append(right[j])
            j += 1
    result.extend(left[i:])
    result.extend(right[j:])
    return result


# ─────────────────────────────────────────────────────────
# 그래프 탐색
# ─────────────────────────────────────────────────────────

def topological_sort(commits_dict):
    """
    Kahn's algorithm: 부모가 자식보다 먼저 출력되는 위상 정렬.
    큐를 commits_dict 삽입 순서(dict) 기준으로 초기화해 결정론적 출력 보장.
    """
    # 부모→자식 방향에서 각 자식의 in_degree 계산
    in_degree = {h: 0 for h in commits_dict}
    children = {h: [] for h in commits_dict}

    for commit in commits_dict.values():
        for ph in commit.parents:
            if ph in commits_dict:
                children[ph].append(commit.hash)
                in_degree[commit.hash] += 1

    # 루트(부모 없는 커밋)를 삽입 순서대로 큐에 추가
    queue = [h for h in commits_dict if in_degree[h] == 0]
    head = 0
    result = []

    while head < len(queue):
        h = queue[head]
        head += 1
        result.append(h)
        for child in children[h]:
            in_degree[child] -= 1
            if in_degree[child] == 0:
                queue.append(child)

    return result


def _build_adj(commits_dict):
    """무방향 인접 리스트 생성 (PATH 명령용)"""
    adj = {h: [] for h in commits_dict}
    for commit in commits_dict.values():
        for ph in commit.parents:
            if ph in adj:
                if ph not in adj[commit.hash]:
                    adj[commit.hash].append(ph)
                if commit.hash not in adj[ph]:
                    adj[ph].append(commit.hash)
    return adj


def bfs_shortest_path(commits_dict, src, dst):
    """
    BFS 최단 경로 (무방향 간선 기준).
    동일 길이 경로 여럿이면 사전순 최소 선택.
    고정 폭(6자리) hash이므로 노드별 greedy 최솟값 = 문자열 사전순 최솟값 보장.
    """
    if src not in commits_dict or dst not in commits_dict:
        return None
    if src == dst:
        return [src]

    adj = _build_adj(commits_dict)

    # dst에서 BFS → 각 노드의 dst까지 최단 거리 계산
    dist_to_dst = {dst: 0}
    queue = [dst]
    head = 0
    while head < len(queue):
        node = queue[head]
        head += 1
        for nb in adj[node]:
            if nb not in dist_to_dst:
                dist_to_dst[nb] = dist_to_dst[node] + 1
                queue.append(nb)

    if src not in dist_to_dst:
        return None

    # src → dst: 매 스텝 dist_to_dst가 줄어드는 이웃 중 hash 최솟값 선택
    path = [src]
    current = src
    while current != dst:
        d = dist_to_dst[current]
        candidates = [nb for nb in adj[current] if dist_to_dst.get(nb, -1) == d - 1]
        if not candidates:
            return None
        best = candidates[0]
        for c in candidates[1:]:
            if c < best:
                best = c
        path.append(best)
        current = best

    return path


def get_ancestors(commits_dict, start_hash):
    """DFS로 start_hash에서 도달 가능한 모든 조상 수집 (start_hash 제외)"""
    visited = set()
    stack = [start_hash]
    ancestors = []

    while stack:
        h = stack.pop()
        for ph in commits_dict[h].parents:
            if ph in commits_dict and ph not in visited:
                visited.add(ph)
                ancestors.append(ph)
                stack.append(ph)

    return ancestors


# ─────────────────────────────────────────────────────────
# 명령 파싱
# ─────────────────────────────────────────────────────────

def parse_line(line):
    """
    shlex로 따옴표 포함 토큰화 (shlex는 문자열 처리 표준 라이브러리).
    명령어는 대소문자 무시.
    """
    try:
        tokens = shlex.split(line)
    except ValueError:
        tokens = line.split()
    if not tokens:
        return None, []
    return tokens[0].upper(), tokens[1:]


# ─────────────────────────────────────────────────────────
# 커밋 출력 포맷
# ─────────────────────────────────────────────────────────

def _fmt_commit(commit):
    ts = datetime.datetime.fromtimestamp(commit.timestamp).strftime('%Y-%m-%d %H:%M:%S')
    return f"commit {commit.hash} ({commit.author}, {ts})\n{commit.message}"


# ─────────────────────────────────────────────────────────
# 명령 핸들러
# ─────────────────────────────────────────────────────────

def cmd_init(repo, args):
    if not args:
        return "Invalid args"
    repo.commits = {}
    repo.branches = {'main': None}
    repo.HEAD = 'main'
    repo.current_user = args[0]
    repo.keyword_index = {}
    repo.author_index = {}
    repo._counter = 0
    return f"Initialized repository.\nCurrent branch: main\nCurrent user: {args[0]}"


def cmd_branch(repo, args):
    if not args:
        return "Invalid args"
    if repo.HEAD is None:
        return "Repository not initialized"
    repo.branches[args[0]] = repo.branches.get(repo.HEAD)
    return f"Created branch: {args[0]}"


def cmd_switch(repo, args):
    if not args:
        return "Invalid args"
    if args[0] not in repo.branches:
        return f"Unknown branch: {args[0]}"
    repo.HEAD = args[0]
    return f"Switched to branch: {args[0]}"


def cmd_commit(repo, args):
    if not args:
        return "Invalid args"
    if repo.HEAD is None:
        return "Repository not initialized"
    # shlex가 따옴표 감싼 다중 단어 메시지를 단일 토큰으로 처리
    message = args[0]
    parent_hash = repo.branches.get(repo.HEAD)
    parents = [parent_hash] if parent_hash is not None else []
    h = repo._gen_hash()
    c = Commit(h, message, repo.current_user, time.time(), parents)
    repo.commits[h] = c
    repo.branches[repo.HEAD] = h
    repo._update_index(c)
    return f"[{repo.HEAD} {h}] {message}"


def cmd_log(repo, args):
    if not repo.commits:
        return "No commits yet"

    sort_by = None
    for arg in args:
        if arg.startswith('--sort-by='):
            sort_by = arg[len('--sort-by='):]

    if sort_by:
        commits = list(repo.commits.values())
        if sort_by == 'date':
            commits = merge_sort(commits, lambda c: c.timestamp)
        elif sort_by == 'author':
            commits = merge_sort(commits, lambda c: c.author.lower())
        else:
            return f"Unknown sort key: {sort_by}"
    else:
        # 위상 정렬: 부모가 자식보다 먼저
        ordered_hashes = topological_sort(repo.commits)
        commits = [repo.commits[h] for h in ordered_hashes]

    return '\n'.join(_fmt_commit(c) for c in commits)


def cmd_path(repo, args):
    if len(args) < 2:
        return "Invalid args"
    h1, h2 = args[0], args[1]
    if h1 not in repo.commits:
        return f"Unknown commit: {h1}"
    if h2 not in repo.commits:
        return f"Unknown commit: {h2}"
    path = bfs_shortest_path(repo.commits, h1, h2)
    if path is None:
        return "No path"
    return "Path: " + " -> ".join(path)


def cmd_ancestors(repo, args):
    if not args:
        return "Invalid args"
    h = args[0]
    if h not in repo.commits:
        return f"Unknown commit: {h}"
    ancestors = get_ancestors(repo.commits, h)
    if not ancestors:
        return "No ancestors"
    lines = [f"Ancestors of {h}:"]
    for ah in ancestors:
        c = repo.commits[ah]
        lines.append(f"- {ah} {c.message}")
    return '\n'.join(lines)


def cmd_search(repo, args):
    if not args:
        return "Invalid args"
    if args[0].startswith('--author='):
        name = args[0][len('--author='):]
        hashes = repo.author_index.get(name.lower(), [])
        if not hashes:
            return f"No commits by {name}"
        hashes = merge_sort(hashes, lambda x: x)
        lines = [f"Found {len(hashes)} commit(s) by {name}:"]
        for ah in hashes:
            lines.append(f"- {ah} {repo.commits[ah].message}")
        return '\n'.join(lines)
    else:
        kw = args[0].lower()
        hashes = repo.keyword_index.get(kw, [])
        if not hashes:
            return f"No commits matching '{kw}'"
        hashes = merge_sort(hashes, lambda x: x)
        lines = [f"Found {len(hashes)} commit(s):"]
        for ah in hashes:
            lines.append(f"- {ah} {repo.commits[ah].message}")
        return '\n'.join(lines)


# ─────────────────────────────────────────────────────────
# REPL 메인 루프
# ─────────────────────────────────────────────────────────

COMMANDS = {
    'INIT': cmd_init,
    'BRANCH': cmd_branch,
    'SWITCH': cmd_switch,
    'COMMIT': cmd_commit,
    'LOG': cmd_log,
    'PATH': cmd_path,
    'ANCESTORS': cmd_ancestors,
    'SEARCH': cmd_search,
}


def main():
    repo = Repository()
    print("Mini Git (exit/quit 으로 종료 | 공백 포함 메시지는 따옴표 사용: COMMIT \"my message\")")
    while True:
        try:
            line = input("mini-git> ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if not line:
            continue
        cmd, args = parse_line(line)
        if cmd is None:
            continue
        if cmd in ('EXIT', 'QUIT'):
            break
        handler = COMMANDS.get(cmd)
        if handler:
            print(handler(repo, args))
        else:
            print(f"Unknown command: {cmd}")


if __name__ == '__main__':
    main()
