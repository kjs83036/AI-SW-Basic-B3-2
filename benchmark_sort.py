import random
import time
import sys
from mini_git import merge_sort, quick_sort

# 재귀 깊이 제한 확장 (재귀 퀵소트/머지소트 실행 시 안전 확보)
sys.setrecursionlimit(20000)

def run_benchmark():
    sizes = [100, 500, 1000, 2000, 5000]
    random.seed(42)  # 재현 가능성을 위해 시드 고정
    
    print("=" * 60)
    print(f"{'Input Size (N)':<15}{'Merge Sort (s)':<18}{'Quick Sort (s)':<18}{'Python sorted() (s)':<18}")
    print("-" * 60)
    
    results = []
    
    for size in sizes:
        # 동일한 난수 배열 생성
        arr_base = [random.randint(-100000, 100000) for _ in range(size)]
        
        # 1. Merge Sort
        arr_m = list(arr_base)
        start = time.perf_counter()
        merge_sort(arr_m)
        t_merge = time.perf_counter() - start
        
        # 2. Quick Sort
        arr_q = list(arr_base)
        start = time.perf_counter()
        quick_sort(arr_q)
        t_quick = time.perf_counter() - start
        
        # 3. Python Built-in sorted (Timsort)
        arr_p = list(arr_base)
        start = time.perf_counter()
        sorted(arr_p)
        t_python = time.perf_counter() - start
        
        # 검증 (정렬이 정상적으로 완료되었는지 확인)
        assert sorted(arr_base) == merge_sort(arr_base), "Merge sort failed verification"
        assert sorted(arr_base) == quick_sort(arr_base), "Quick sort failed verification"
        
        print(f"{size:<15}{t_merge:<18.6f}{t_quick:<18.6f}{t_python:<18.6f}")
        results.append((size, t_merge, t_quick, t_python))
        
    print("=" * 60)
    
    # README에 붙여넣을 마크다운 표 생성 출력
    print("\n### 마크다운 표 형식 결과:")
    print("| 입력 크기 (N) | 병합 정렬 (Merge Sort) | 퀵 정렬 (Quick Sort) | 파이썬 내장 (Timsort) |")
    print("| :--- | :--- | :--- | :--- |")
    for size, tm, tq, tp in results:
        print(f"| {size:,} | {tm:.6f}초 | {tq:.6f}초 | {tp:.6f}초 |")

if __name__ == "__main__":
    run_benchmark()
