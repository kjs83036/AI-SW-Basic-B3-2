# Mini Git 구축

## 개요

CLI 기반 Mini Git 구현. 커밋을 DAG로 관리하고 역색인(Inverted Index)으로 빠른 검색을 지원한다. 정렬은 직접 구현한 병합 정렬을 사용하며(Python sorted/list.sort 미사용), REPL 인터페이스로 10종 명령을 처리한다.

## 실행 방법

```bash
python main.py
```

Python 3.10 이상 필요. 외부 라이브러리 설치 불필요.

## 지원 명령어

| 명령 | 설명 |
|------|------|
| `INIT <user_name>` | 저장소 초기화, main 브랜치 생성 |
| `BRANCH <branch_name>` | 현재 HEAD에서 새 브랜치 생성 |
| `SWITCH <branch_name>` | 브랜치 전환 |
| `COMMIT <message>` | 새 커밋 생성 (공백 포함 메시지는 따옴표 필요) |
| `LOG` | 위상 정렬 순서로 커밋 목록 출력 (부모 먼저) |
| `LOG --sort-by=date\|author` | 날짜 또는 작성자 기준 정렬 출력 |
| `PATH <hash1> <hash2>` | 두 커밋 사이 최단 경로 출력 |
| `ANCESTORS <hash>` | 해당 커밋의 모든 조상 출력 |
| `SEARCH <keyword>` | 키워드 포함 커밋 검색 (역색인 기반) |
| `SEARCH --author=<name>` | 특정 작성자 커밋 검색 (역색인 기반) |
| `exit` / `quit` | 종료 |

## 파일

- `main.py` — 구현 (단일 파일)
- `architecture.md` — 전체 구조도 (mermaid)
- `EXPLANATION.md` — 코드리뷰 수준 통합 설명
- `MANUAL_VERIFICATION.md` — 수동 검증 가이드
- `README.md` — 본 문서

## 결과 요약

- 필수 명령 10종 모두 구현 (INIT/BRANCH/SWITCH/COMMIT/LOG/LOG --sort-by/PATH/ANCESTORS/SEARCH keyword/SEARCH --author)
- sorted()/list.sort() 미사용: 병합 정렬 직접 구현
- 역색인 2종(keyword/author)으로 O(1) 검색 후보 조회
- PATH: BFS + greedy 사전순 최소 경로 선택 (고정 폭 hash 활용)
