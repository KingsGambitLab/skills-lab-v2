"""Canonical algorithm-pattern library for Creator (L5, 2026-04-22).

When a code_exercise step matches a known pattern (sliding window, two pointers,
binary search, topological sort, union-find, BFS/DFS, etc.), the Creator can
pull the starter/solution/test skeleton from here instead of asking the LLM
to synthesize it from scratch. LLM then ONLY fills in:
  - scenario framing (company name, business context)
  - the specific problem statement (what `nums` represents in this scenario)
  - variable names if the domain suggests different ones

This makes generation near-zero-rejection-rate on covered patterns.

Callsite: `_llm_generate_step_content` checks `step_title + step_description`
against each pattern's trigger phrases; if a match, inject the triple into the
Creator prompt as "USE THIS CANONICAL STRUCTURE" rather than hoping the LLM
synthesizes one from scratch.
"""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class AlgorithmPattern:
    id: str
    label: str
    # Lowercase trigger phrases — if the step title/description contains any,
    # this pattern is a candidate.
    triggers: list[str]
    # Canonical broken starter (LangGraph-invariant compliant — raises NotImpl).
    starter: str
    # Canonical working solution.
    solution: str
    # 4-6 pytest tests that pass against the solution + fail against the starter.
    tests: str
    language: str = "python"


PATTERN_REGISTRY: dict[str, AlgorithmPattern] = {}


def register(p: AlgorithmPattern) -> AlgorithmPattern:
    PATTERN_REGISTRY[p.id] = p
    return p


def find_match(step_title: str, step_description: str = "") -> AlgorithmPattern | None:
    """Return the first pattern whose triggers match the step title/desc."""
    blob = f"{step_title} {step_description}".lower()
    for p in PATTERN_REGISTRY.values():
        if any(t in blob for t in p.triggers):
            return p
    return None


# ═══════════════════════════════════════════════════════════════════════════
# Patterns
# ═══════════════════════════════════════════════════════════════════════════

register(AlgorithmPattern(
    id="sliding_window_max_sum",
    label="Sliding window — max sum of k consecutive",
    triggers=["sliding window", "max sum of k", "max_sum_k", "window of size k"],
    starter='''from typing import List

def max_sum_k(nums: List[int], k: int) -> int:
    """Return the maximum sum of `k` consecutive elements in `nums`.
    Window slides left-to-right; after the first window is summed, each step
    adds the next element and drops the leftmost — no re-summing.
    """
    raise NotImplementedError("TODO: sliding-window max sum")
''',
    solution='''from typing import List

def max_sum_k(nums: List[int], k: int) -> int:
    if not nums or k <= 0 or k > len(nums):
        return 0
    cur = sum(nums[:k])
    best = cur
    for i in range(k, len(nums)):
        cur += nums[i] - nums[i-k]
        if cur > best:
            best = cur
    return best
''',
    tests='''from solution import max_sum_k

def test_basic():
    assert max_sum_k([1, 2, 3, 4, 5], 2) == 9  # 4+5

def test_k_eq_len():
    assert max_sum_k([1, 2, 3], 3) == 6

def test_empty():
    assert max_sum_k([], 3) == 0

def test_k_zero():
    assert max_sum_k([1, 2, 3], 0) == 0

def test_negatives():
    assert max_sum_k([-1, -2, -3, -4], 2) == -3  # -1 + -2
''',
))

register(AlgorithmPattern(
    id="two_pointers_dedup",
    label="Two pointers — in-place dedup of sorted array",
    triggers=["two pointer", "remove_duplicates", "in-place dedup", "in place dedup", "remove duplicates"],
    starter='''from typing import List

def remove_duplicates(nums: List[int]) -> int:
    """Remove duplicates in-place from the sorted list `nums`.
    Mutate `nums` so that `nums[:k]` contains only unique values (original order).
    Return integer `k` = count of unique values. O(n) time, O(1) extra space.
    """
    raise NotImplementedError("TODO: two-pointer in-place dedup")
''',
    solution='''from typing import List

def remove_duplicates(nums: List[int]) -> int:
    if not nums:
        return 0
    k = 1
    for i in range(1, len(nums)):
        if nums[i] != nums[k-1]:
            nums[k] = nums[i]
            k += 1
    return k
''',
    tests='''from solution import remove_duplicates

def test_basic():
    nums = [1, 1, 2, 2, 3]
    k = remove_duplicates(nums)
    assert k == 3
    assert nums[:k] == [1, 2, 3]

def test_empty():
    nums = []
    assert remove_duplicates(nums) == 0

def test_all_unique():
    nums = [1, 2, 3]
    k = remove_duplicates(nums)
    assert k == 3
    assert nums[:k] == [1, 2, 3]

def test_all_same():
    nums = [5, 5, 5]
    k = remove_duplicates(nums)
    assert k == 1
    assert nums[0] == 5

def test_no_rebind():
    nums = [1, 1, 2]
    orig = id(nums)
    remove_duplicates(nums)
    assert id(nums) == orig  # must mutate in place
''',
))

register(AlgorithmPattern(
    id="binary_search_first_true",
    label="Binary search — first True of monotonic predicate",
    triggers=["binary search", "first_true", "first true", "monotonic predicate", "first value where"],
    starter='''from typing import Callable

def first_true(lo: int, hi: int, predicate: Callable[[int], bool]) -> int:
    """Return the smallest x in [lo, hi] where predicate(x) is True.
    Assumes predicate is monotonic (False...False True...True). If no True, return hi + 1.
    """
    raise NotImplementedError("TODO: binary search")
''',
    solution='''from typing import Callable

def first_true(lo: int, hi: int, predicate: Callable[[int], bool]) -> int:
    while lo < hi:
        mid = (lo + hi) // 2
        if predicate(mid):
            hi = mid
        else:
            lo = mid + 1
    return lo if predicate(lo) else hi + 1
''',
    tests='''from solution import first_true

def test_basic():
    assert first_true(0, 10, lambda x: x >= 5) == 5

def test_first_is_true():
    assert first_true(0, 10, lambda x: x >= 0) == 0

def test_none_true():
    assert first_true(0, 5, lambda x: x > 100) == 6

def test_boundary():
    assert first_true(0, 10, lambda x: x >= 10) == 10

def test_single_element():
    assert first_true(5, 5, lambda x: x >= 5) == 5
''',
))

register(AlgorithmPattern(
    id="topo_sort_kahn",
    label="Topological sort — Kahn's algorithm",
    triggers=["topological sort", "topo sort", "course_order", "find_order", "kahn's algorithm", "course schedule"],
    starter='''from typing import List, Tuple
from collections import defaultdict, deque

def course_order(num_courses: int, prerequisites: List[Tuple[int, int]]) -> List[int]:
    """Return a course order that respects prerequisites, or [] if a cycle exists.
    prerequisites[i] = (course, prereq) means `course` depends on `prereq`.
    """
    raise NotImplementedError("TODO: Kahn's algorithm with in-degrees")
''',
    solution='''from typing import List, Tuple
from collections import defaultdict, deque

def course_order(num_courses: int, prerequisites: List[Tuple[int, int]]) -> List[int]:
    indeg = [0] * num_courses
    graph = defaultdict(list)
    for course, pre in prerequisites:
        graph[pre].append(course)
        indeg[course] += 1
    q = deque([i for i in range(num_courses) if indeg[i] == 0])
    order = []
    while q:
        n = q.popleft()
        order.append(n)
        for m in graph[n]:
            indeg[m] -= 1
            if indeg[m] == 0:
                q.append(m)
    return order if len(order) == num_courses else []
''',
    tests='''from solution import course_order

def test_basic():
    r = course_order(4, [(1, 0), (2, 0), (3, 1), (3, 2)])
    assert len(r) == 4
    assert r.index(0) < r.index(1) and r.index(0) < r.index(2)
    assert r.index(1) < r.index(3) and r.index(2) < r.index(3)

def test_no_prereqs():
    r = course_order(3, [])
    assert sorted(r) == [0, 1, 2]

def test_cycle():
    assert course_order(2, [(1, 0), (0, 1)]) == []

def test_single_course():
    assert course_order(1, []) == [0]

def test_disconnected():
    r = course_order(4, [(1, 0)])
    assert len(r) == 4 and r.index(0) < r.index(1)
''',
))

register(AlgorithmPattern(
    id="union_find_components",
    label="Union-Find — connected components",
    triggers=["union-find", "union find", "dsu", "disjoint set", "count_components", "connected components"],
    starter='''from typing import List, Tuple

def count_components(n: int, edges: List[Tuple[int, int]]) -> int:
    """Return the number of connected components in an n-node undirected graph."""
    raise NotImplementedError("TODO: union-find with path compression + union by rank")
''',
    solution='''from typing import List, Tuple

def count_components(n: int, edges: List[Tuple[int, int]]) -> int:
    parent = list(range(n))
    rank = [0] * n
    def find(x: int) -> int:
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x
    def union(a: int, b: int) -> None:
        ra, rb = find(a), find(b)
        if ra == rb: return
        if rank[ra] < rank[rb]: ra, rb = rb, ra
        parent[rb] = ra
        if rank[ra] == rank[rb]: rank[ra] += 1
    for a, b in edges:
        union(a, b)
    return len({find(i) for i in range(n)})
''',
    tests='''from solution import count_components

def test_basic():
    assert count_components(5, [(0,1), (1,2), (3,4)]) == 2

def test_no_edges():
    assert count_components(3, []) == 3

def test_full_connected():
    assert count_components(4, [(0,1), (1,2), (2,3)]) == 1

def test_empty():
    assert count_components(0, []) == 0

def test_self_loops():
    assert count_components(3, [(0,0), (1,1)]) == 3
''',
))


def describe_pattern_for_prompt(pattern: AlgorithmPattern) -> str:
    """Render a pattern as a prompt block the Creator can embed."""
    return (
        f"### L5 CANONICAL PATTERN — {pattern.label} (id={pattern.id})\n"
        f"Use this exact structure for the starter + solution_code + hidden_tests fields. "
        f"The LangGraph invariant has been pre-verified against this triple — it PASSES.\n\n"
        f"**starter:**\n```python\n{pattern.starter}\n```\n\n"
        f"**solution_code:**\n```python\n{pattern.solution}\n```\n\n"
        f"**hidden_tests:**\n```python\n{pattern.tests}\n```\n\n"
        f"When adapting: keep the function signature + raise NotImplementedError line "
        f"verbatim in the starter. Keep the solution working. You MAY rename `nums` to "
        f"domain-specific names (e.g. `server_ids`, `event_times`) if the step's scenario "
        f"calls for it — but change the same name across starter/solution/tests.\n"
    )
