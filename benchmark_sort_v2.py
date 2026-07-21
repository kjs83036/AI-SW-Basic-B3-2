"""
정렬 알고리즘 성능 비교 벤치마크 v2
- 병합 정렬 (Merge Sort) - 기존 구현
- 퀵 정렬 (Quick Sort) - 기존 리스트 컴프리헨션 방식
- 퀵 정렬 (Quick Sort) - 포인터 이동(In-place) 방식
- 파이썬 내장 정렬 (Timsort)
"""

import random
import time
import sys

sys.setrecursionlimit(20000)

# ── 기존 구현 임포트 ──────────────────────────────────────────
from mini_git import merge_sort, quick_sort


# ── 포인터 이동(In-place) 퀵소트 구현 ────────────────────────
def _partition(arr, low, high, key_func):
    """Lomuto 파티션 스킴: pivot을 마지막 원소로 선택하고 인덱스 이동으로 분할"""
    pivot_val = key_func(arr[high])
    i = low - 1
    for j in range(low, high):
        if key_func(arr[j]) <= pivot_val:
            i += 1
            arr[i], arr[j] = arr[j], arr[i]
    arr[i + 1], arr[high] = arr[high], arr[i + 1]
    return i + 1


def _quicksort_inplace(arr, low, high, key_func):
    """재귀적 In-place 퀵소트 (포인터/인덱스 이동 방식)"""
    if low < high:
        pi = _partition(arr, low, high, key_func)
        _quicksort_inplace(arr, low, pi - 1, key_func)
        _quicksort_inplace(arr, pi + 1, high, key_func)


def quick_sort_inplace(arr, key_func=lambda x: x):
    """포인터 이동(In-place) 방식 퀵소트 - 새 리스트를 만들지 않고 제자리 정렬"""
    result = list(arr)  # 원본 보존을 위해 복사본 사용
    if len(result) > 1:
        _quicksort_inplace(result, 0, len(result) - 1, key_func)
    return result


# ── Hoare 파티션 스킴 In-place 퀵소트 (추가 비교) ─────────────
def _partition_hoare(arr, low, high, key_func):
    """Hoare 파티션 스킴: 양쪽 포인터가 중앙으로 이동하며 교환"""
    pivot_val = key_func(arr[(low + high) // 2])
    i = low - 1
    j = high + 1
    while True:
        i += 1
        while key_func(arr[i]) < pivot_val:
            i += 1
        j -= 1
        while key_func(arr[j]) > pivot_val:
            j -= 1
        if i >= j:
            return j
        arr[i], arr[j] = arr[j], arr[i]


def _quicksort_hoare(arr, low, high, key_func):
    """Hoare 파티션 기반 In-place 퀵소트"""
    if low < high:
        pi = _partition_hoare(arr, low, high, key_func)
        _quicksort_hoare(arr, low, pi, key_func)
        _quicksort_hoare(arr, pi + 1, high, key_func)


def quick_sort_hoare(arr, key_func=lambda x: x):
    """Hoare 방식 In-place 퀵소트"""
    result = list(arr)
    if len(result) > 1:
        _quicksort_hoare(result, 0, len(result) - 1, key_func)
    return result


# ── 벤치마크 실행 ─────────────────────────────────────────────
def run_benchmark():
    sizes = [100, 500, 1000, 2000, 5000]
    random.seed(42)

    header = (
        f"{'N':<10}"
        f"{'Merge Sort':<16}"
        f"{'Quick(List)':<16}"
        f"{'Quick(Lomuto)':<16}"
        f"{'Quick(Hoare)':<16}"
        f"{'Timsort':<16}"
    )
    print("=" * 90)
    print(header)
    print("-" * 90)

    results = []

    for size in sizes:
        arr_base = [random.randint(-100000, 100000) for _ in range(size)]
        expected = sorted(arr_base)

        # 1. Merge Sort (기존 구현 - @measure_time 데코레이터 출력 포함)
        arr_m = list(arr_base)
        start = time.perf_counter()
        res_m = merge_sort(arr_m)
        t_merge = time.perf_counter() - start

        # 2. Quick Sort - 리스트 컴프리헨션 방식 (기존 구현)
        arr_q = list(arr_base)
        start = time.perf_counter()
        res_q = quick_sort(arr_q)
        t_quick_list = time.perf_counter() - start

        # 3. Quick Sort - Lomuto In-place 방식 (포인터 이동)
        arr_l = list(arr_base)
        start = time.perf_counter()
        res_l = quick_sort_inplace(arr_l)
        t_quick_lomuto = time.perf_counter() - start

        # 4. Quick Sort - Hoare In-place 방식 (포인터 이동)
        arr_h = list(arr_base)
        start = time.perf_counter()
        res_h = quick_sort_hoare(arr_h)
        t_quick_hoare = time.perf_counter() - start

        # 5. Python Built-in sorted (Timsort)
        arr_p = list(arr_base)
        start = time.perf_counter()
        res_p = sorted(arr_p)
        t_python = time.perf_counter() - start

        # 검증
        assert res_m == expected, "Merge sort failed"
        assert res_q == expected, "Quick sort (list) failed"
        assert res_l == expected, "Quick sort (Lomuto in-place) failed"
        assert res_h == expected, "Quick sort (Hoare in-place) failed"

        print(
            f"{size:<10}"
            f"{t_merge:<16.6f}"
            f"{t_quick_list:<16.6f}"
            f"{t_quick_lomuto:<16.6f}"
            f"{t_quick_hoare:<16.6f}"
            f"{t_python:<16.6f}"
        )
        results.append((size, t_merge, t_quick_list, t_quick_lomuto, t_quick_hoare, t_python))

    print("=" * 90)

    # 마크다운 표 출력
    print("\n### 마크다운 표 형식 결과:")
    print(
        "| 입력 크기 (N) | 병합 정렬 | 퀵 정렬 (리스트) | 퀵 정렬 (Lomuto In-place) | 퀵 정렬 (Hoare In-place) | Timsort |"
    )
    print("| :--- | :--- | :--- | :--- | :--- | :--- |")
    for size, tm, tql, tqlo, tqh, tp in results:
        print(
            f"| {size:,} | {tm:.6f}초 | {tql:.6f}초 | {tqlo:.6f}초 | {tqh:.6f}초 | {tp:.6f}초 |"
        )

    # 비율 분석 출력
    print("\n### 성능 비율 분석 (Merge Sort 대비):")
    print("| 입력 크기 (N) | Quick(List) / Merge | Quick(Lomuto) / Merge | Quick(Hoare) / Merge |")
    print("| :--- | :--- | :--- | :--- |")
    for size, tm, tql, tqlo, tqh, tp in results:
        r_list = tql / tm if tm > 0 else float('inf')
        r_lomuto = tqlo / tm if tm > 0 else float('inf')
        r_hoare = tqh / tm if tm > 0 else float('inf')
        print(f"| {size:,} | {r_list:.2f}x | {r_lomuto:.2f}x | {r_hoare:.2f}x |")


if __name__ == "__main__":
    run_benchmark()
