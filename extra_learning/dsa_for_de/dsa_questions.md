# DSA Questions for Data Engineering Interviews (Detailed)

Focus areas: arrays, strings, hashmaps, sorting, heaps, sliding window, graphs (light), recursion. Most DE interviews ask 1-2 DSA problems at medium difficulty plus practical "data engineering flavored" problems.

## Classic problems

### 1. Two Sum.
Given an array and a target, return indices of two numbers summing to target. O(n) with a hashmap mapping `value -> index`: iterate once, for each `x` check if `target - x` is already seen. Common follow-up: handle duplicates, sorted variant with two pointers (O(n) without extra memory).

### 2. Group anagrams.
Group strings that are anagrams of each other. Use a hashmap keyed by the canonical form — either sorted string `"".join(sorted(s))` (O(k log k) per word) or a tuple of 26 letter counts (O(k) per word). The counts approach is faster for long words.

### 3. Longest substring without repeating characters.
Sliding window: expand right, track last seen index per character; on a repeat, jump left to `max(left, last_seen + 1)`. O(n) time, O(charset) space. Foundation pattern for many "longest substring with constraint X" problems.

### 4. Top K frequent elements.
Count frequencies with `Counter`, then either (a) heap of size K — O(n log K), or (b) bucket sort by frequency — O(n) but uses more memory. The heap approach mirrors classic streaming top-K and ranks well in interviews.

### 5. Merge intervals.
Sort by start, then iterate merging when `current.start <= last.end`. O(n log n). Variants: insert one new interval into a sorted list (O(n)), interval intersection of two lists, meeting-room scheduling.

### 6. Find duplicates in an array.
With a hashset: O(n) time, O(n) space. With sort + adjacent comparison: O(n log n), O(1) extra. With Floyd's cycle detection on `[1..n]` range arrays: O(n) time, O(1) extra — the elegant trick that often impresses interviewers.

### 7. Find missing number.
For `[0..n]` missing one: use `n*(n+1)/2 - sum(arr)` for O(n) O(1). For sorted arrays use binary search on `arr[mid] != mid`. For arrays of `[1..n]` with one missing and one duplicate, use XOR or signed marking.

### 8. Move zeros to end.
Two pointers: `write` and `read`. Walk `read`; when non-zero, copy to `write` and increment `write`. After the pass, fill `[write:]` with zeros. O(n), in-place, preserves order.

### 9. Rotate array.
Reverse trick: rotating right by k is reverse-all + reverse-first-k + reverse-rest. O(n) time, O(1) extra. Remember `k %= n` to handle large k.

### 10. Valid parentheses.
Stack: push open brackets, on close pop and check match. Empty stack at end = valid. Generalizes to expression parsers and balancing problems.

### 11. Implement LRU cache.
`OrderedDict`: `move_to_end` on access, `popitem(last=False)` to evict. O(1) get and put. Alternative: hashmap + doubly linked list — the "from scratch" answer that interviewers sometimes want.

### 12. Word frequency counter.
`Counter(words)` is the one-liner. From scratch: dict of `word -> count` with `dict.get(w, 0) + 1`. This is the mental model for MapReduce/Spark word-count and a great place to discuss partitioning and combiners.

### 13. K closest points to origin.
Max-heap of size K (push, pop when size > K) keyed by negative distance — O(n log K). Quickselect is O(n) average but trickier to code; usually heap is the safer interview answer.

### 14. Median of a stream.
Two heaps: max-heap of the lower half, min-heap of the upper half. Keep sizes balanced (`abs(diff) <= 1`). Median is the top of whichever heap is bigger, or the average of both tops. O(log n) per insertion.

### 15. Sort logs by key.
Custom key with `sorted(logs, key=lambda l: (l.timestamp, l.source))`. Discuss stability, secondary keys, and external sort for files that don't fit in memory.

### 16. Detect cycle in linked list.
Floyd's tortoise and hare: two pointers, one step vs two steps; they meet iff a cycle exists. O(n) time, O(1) extra. To find the cycle start, reset one pointer to head and advance both one-by-one.

### 17. Reverse a linked list.
Iterative with three pointers (`prev`, `curr`, `next`): O(n) time, O(1) extra. Recursive version is elegant but uses O(n) stack. Foundational pointer-manipulation problem.

### 18. Binary search variants.
Master the template: `while lo < hi: mid = (lo+hi)//2; if check(mid): hi = mid else: lo = mid + 1`. Variants: first occurrence, last occurrence, rotated array, search-in-2D, binary-search-on-answer (e.g. "minimum capacity to ship in D days").

### 19. Subset and permutation generation.
Backtracking with a `path` list, `start` index, and `chosen` set. Subsets: include/exclude at each index. Permutations: pick each remaining element. Discuss pruning and memoization for combinatorial-heavy variants.

### 20. Sliding window maximum.
Monotonic deque storing indices in decreasing order of values: pop from back while smaller, append; pop from front when out of window. O(n) total. Classic and shows up in streaming aggregations.

## Data engineering flavored

### 21. In-memory message queue.
`collections.deque` with `append`/`popleft` is O(1) and thread-safe under GIL for single producer/consumer. Discuss bounded capacity (`maxlen` or condition vars), multi-consumer with `queue.Queue`, persistence, and how Kafka generalizes the idea across machines.

### 22. Token bucket rate limiter.
Track `tokens` and `last_refill_time`. On each request, refill tokens proportional to elapsed time up to capacity; if `tokens >= 1`, decrement and allow. O(1) per check. Discuss burstiness vs steady-rate, leaky-bucket alternative, and distributed rate limiting with Redis.

### 23. Deduplication on a stream.
Set of seen IDs with a TTL or fixed-size eviction (e.g. LRU). For unbounded streams, switch to a **Bloom filter** (probabilistic, allows false positives, no false negatives) or HyperLogLog for cardinality. Discuss exactly-once vs at-least-once trade-offs.

### 24. Sessionization in pure Python.
Sort events per user by timestamp; iterate and start a new session whenever the gap from the previous event exceeds threshold. Output `(user, session_id, start, end, count)`. The same logic in SQL/Spark uses LAG + cumulative sum; explaining both shows breadth.

### 25. Top-N over a stream.
Maintain a min-heap of size N keyed by count; on each new event update its count in a hashmap, push to heap if not present, pop when size > N. Approximate alternative: **Count-Min Sketch + heap** for very high cardinality.

### 26. Simple LRU cache for lookups.
Same as classic LRU — useful in DE for caching small dim tables, API responses, or expensive transformations. Discuss thread-safety and how Spark's broadcast variables or driver-side caches generalize this.

### 27. External merge join of two sorted files.
Two file pointers, advance the smaller side; on equal keys, emit the join and advance both. O(n+m) IO, constant memory — the canonical "data doesn't fit in RAM" technique. Generalizes to Spark sort-merge join.

### 28. Word count without `Counter`.
`d = {}; for w in words: d[w] = d.get(w, 0) + 1`. Discuss why this is the canonical MapReduce example, how combiners reduce shuffle, and partitioning by hash(word) for parallelism.

### 29. Streaming median.
Two-heap pattern as in #14, but emphasize processing one event at a time and emitting the running median. Discuss memory bounds and exponentially-decaying variants for "median over the last hour."

### 30. Bloom filter (conceptual).
Bit array of size m + k independent hash functions. To add x, set bits at `h_i(x) % m` for i=1..k. To test, check all bits — all 1 means "probably present," any 0 means "definitely absent." Tunable false-positive rate via m and k; great for "have I seen this URL before?" at huge scale.
