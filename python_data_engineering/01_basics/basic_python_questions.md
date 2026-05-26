# Python Basic Interview Questions for Data Engineers (Detailed)

### 1. List vs tuple vs set?
**List**: mutable, ordered, allows duplicates, O(n) lookup. **Tuple**: immutable, ordered, allows duplicates, slightly faster, hashable so usable as dict key. **Set**: mutable, unordered, no duplicates, O(1) membership test backed by a hash table. Use set for dedup and fast `in` checks.

### 2. `is` vs `==`?
`==` compares values (calls `__eq__`). `is` compares object identity (memory address). `None`, `True`, `False`, and small ints (-5..256) are cached, so `is` works coincidentally — but always use `==` for value comparisons and `is` only for sentinels like `None`.

### 3. Why is dict lookup O(1)?
Python dicts are hash tables: the key is hashed, the hash is reduced modulo the table size to find a bucket, and collisions are resolved by open addressing. Amortized lookup, insert, and delete are O(1). Worst case is O(n) on pathological hash collisions.

### 4. List comprehension?
A concise expression that builds a list: `[x*2 for x in nums if x > 0]`. Faster than equivalent `for` + `append` because the loop runs in C. Same syntax exists for sets, dicts, and generators (with `()`).

### 5. Shallow vs deep copy?
`copy.copy(obj)` copies the outer container but shares nested references; modifying a nested list still affects the original. `copy.deepcopy(obj)` recursively copies everything. Deep copy is slower and can fail on circular references without care.

### 6. *args and **kwargs?
`*args` collects extra positional arguments into a tuple; `**kwargs` collects extra keyword arguments into a dict. Used to forward arbitrary arguments to wrapped functions (decorators, factories).

### 7. Lambda functions?
Single-expression anonymous functions: `lambda x: x * 2`. Useful for short callbacks (`sorted(items, key=lambda x: x[1])`). For anything multi-line or named, use a regular `def` — it is more readable and debuggable.

### 8. Python memory and GC.
CPython uses reference counting for immediate cleanup plus a generational garbage collector for cycles. Most objects are freed when their refcount hits zero. Use `gc.collect()` manually only in rare cases; usually trust the runtime.

### 9. Mutable vs immutable types.
**Immutable**: int, float, str, tuple, frozenset, bytes — modifications create new objects. **Mutable**: list, dict, set, bytearray, custom classes — modified in place. Common bug: mutable default arguments (`def f(x=[]):`) share state across calls.

### 10. Read a file line by line efficiently.
`for line in open(path):` iterates lazily without loading the whole file. For text files, prefer `with open(path) as f: for line in f:` so the handle closes automatically. For very large CSVs, also consider `csv.reader` or pandas with `chunksize`.

### 11. The `with` statement?
A context manager that guarantees setup/cleanup via `__enter__`/`__exit__`, even on exceptions. Standard for files, DB connections, locks. Create your own with `@contextmanager` from `contextlib`.

### 12. append vs extend?
`list.append(x)` adds one element (which can itself be a list, nested). `list.extend(iterable)` adds each element of an iterable to the list. `a.extend(b)` is equivalent to `a += list(b)`.

### 13. What is the GIL?
The Global Interpreter Lock allows only one Python bytecode-executing thread at a time per process. CPU-bound code does not scale with threads in CPython; use multiprocessing or native libraries (numpy, Spark) that release the GIL. I/O-bound code benefits from threads or asyncio.

### 14. map / filter / reduce?
`map(fn, iterable)` and `filter(fn, iterable)` return lazy iterators. `functools.reduce(fn, iterable, init)` folds an iterable into a single value. List comprehensions and generator expressions are usually more Pythonic.

### 15. Exception handling.
`try / except [SpecificError] / else / finally`. Catch the narrowest exception class possible; never bare-`except` (it swallows `KeyboardInterrupt`/`SystemExit`). Use `raise ... from err` to preserve the cause chain.

### 16. What is `__init__`?
The constructor method called when an instance is created. It receives the new instance as `self` and initializes attributes. The actual instance creation is done by `__new__` before `__init__`.

### 17. Classmethod vs staticmethod vs instance method.
**Instance method**: receives `self`, accesses instance state. **Classmethod** (`@classmethod`): receives `cls`, useful for alternative constructors. **Staticmethod** (`@staticmethod`): receives neither, just a function namespaced inside the class — usually a code-smell, prefer a module function.

### 18. Decorators.
Functions that wrap another function to add behavior (logging, timing, retry, caching) without modifying it. Implemented with closures: `def deco(fn): def wrapper(*a, **k): ...; return wrapper`. Use `functools.wraps` to preserve the original metadata.

### 19. Generators and why use them in ETL?
Functions with `yield` that produce values lazily, holding only one item in memory at a time. Critical for ETL on large files/streams — you can process billion-row inputs with constant memory.

### 20. What is `yield`?
A keyword that suspends a function and returns a value to the caller, resuming on the next `next()` call. Multiple yields produce a sequence; `yield from` delegates to another iterable. `yield` also supports two-way communication (`send`) for coroutines.

### 21. Iterator vs iterable.
**Iterable** implements `__iter__` and can produce an iterator (lists, dicts, files). **Iterator** implements both `__iter__` (returns self) and `__next__` (returns next value or raises `StopIteration`). All iterators are iterables, but not vice versa.

### 22. `enumerate`?
`enumerate(iterable, start=0)` yields `(index, value)` pairs lazily. Cleaner than `for i in range(len(items))` and works on any iterable, not just sequences.

### 23. `zip`?
`zip(a, b, c)` yields tuples by pairing items from each iterable, stopping at the shortest. `itertools.zip_longest` fills missing values with a fill value. Unzip with `zip(*pairs)`.

### 24. Merge two dicts?
Python 3.9+: `d1 | d2` (right wins on conflicts). Older: `{**d1, **d2}` or `d1.update(d2)` (mutates d1). For deep merges, write a recursive helper.

### 25. `collections` essentials.
**Counter**: count occurrences, supports `most_common(n)`. **defaultdict**: provides a default value for missing keys, perfect for grouping. **namedtuple**: lightweight immutable record with named fields. **deque**: O(1) append/pop from both ends, good for sliding windows.

### 26. json.load vs json.loads?
`json.load(file_handle)` reads from a file-like object. `json.loads(string)` parses a string. Mirror functions: `json.dump(obj, file)` and `json.dumps(obj)`.

### 27. Read large CSV without loading into memory.
Use `csv.reader(file)` in a loop, or `pandas.read_csv(path, chunksize=100_000)` which yields DataFrames. For typed schemas and full pushdown, use `pyarrow.csv` or convert to Parquet first.

### 28. Pickle and its risks.
`pickle` serializes Python objects to bytes for storage or IPC. Major risk: **never unpickle untrusted data** — it can execute arbitrary code. Prefer JSON, MessagePack, or Avro for data exchange across systems.

### 29. Threading vs multiprocessing.
**Threading**: shared memory, limited by GIL for CPU work, good for I/O concurrency. **Multiprocessing**: separate processes (no GIL), good for CPU-bound parallelism, higher startup cost and IPC overhead. For data engineering, prefer libraries (Spark, Dask, Ray) that handle this for you.

### 30. When to use asyncio?
For I/O-bound concurrency with many concurrent connections (HTTP APIs, sockets, async DB drivers). Single-threaded, cooperative scheduling — no thread overhead. Not useful for CPU-bound work and requires `async`/`await` all the way down ("async colored functions" problem).
