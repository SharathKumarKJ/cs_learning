# pytest and Testing for Data Engineers (Detailed)

### 1. Why test data pipelines?
To catch regressions before they corrupt downstream tables, enforce data contracts, document expected behavior, and enable confident refactoring. Untested pipelines silently break — and a bad load can take hours to detect and days to backfill.

### 2. Types of tests.
**Unit**: pure functions with sample inputs. **Integration**: pipeline against real (or mocked) source/target — slow, fewer. **End-to-end**: full DAG against test fixtures. **Data quality**: assertions on production output (Great Expectations/Soda). **Contract**: schema/semantics agreement enforced in CI.

### 3. pytest fixtures.
Reusable setup/teardown helpers declared with `@pytest.fixture`. They support scoping (`function`, `module`, `session`), parametrization, and dependency injection: any test that accepts `spark` gets the fixture's value.

### 4. conftest.py.
A special file pytest auto-discovers for shared fixtures and hooks across a directory tree. Use it for SparkSession, temp directories, mock DB connections, and common factories.

### 5. Parametrize.
`@pytest.mark.parametrize("a,b,expected", [(1,1,2),(2,3,5)])` runs the test once per tuple, each with a distinct test ID. Perfect for boundary/edge cases (empty, nulls, leap year, timezone shifts).

### 6. Mocking.
`unittest.mock.patch` or `pytest-mock`'s `mocker` fixture replaces external calls (HTTP, S3, DB) during tests. Mock at the boundary nearest your code; assert on what you sent and how you handled the response.

### 7. Testing Spark code.
Create a session-scoped `SparkSession` fixture with `.master("local[1]")` (single core for determinism). Build small DataFrames inline, run the transformation, assert on `.collect()` or use `chispa` / `pyspark.testing.assertDataFrameEqual` for richer comparison.

### 8. Testing Airflow DAGs.
**Import test**: ensure the DAG parses (no top-level errors). **Structure tests**: assert expected `task_id`s, dependencies, retries, owner. **Logic tests**: extract task callables into a module and unit-test them separately. Use `dag_bag = DagBag()` and `assert not dag_bag.import_errors`.

### 9. Testing SQL.
For dbt: built-in generic tests (`unique`, `not_null`) + singular tests. For raw SQL pipelines: run transformations against fixtures in DuckDB or SQLite, snapshot expected output. **Great Expectations** and **Soda** add declarative DQ.

### 10. Property-based testing.
**Hypothesis** generates many random inputs satisfying a strategy and asserts invariants (e.g. "deduplication never adds rows"). Finds edge cases handwritten tests miss.

### 11. Snapshot testing.
Save a known-good output (CSV, JSON, golden file) and assert future runs produce the same. Useful for complex transformations where writing exhaustive assertions is impractical. Re-approve snapshots through explicit updates only.

### 12. Test data management.
Use **factories** (`factory_boy`) or simple builder functions to generate domain rows with sensible defaults. Keep fixtures small and focused; do not check in giant CSVs unless absolutely necessary.

### 13. Coverage.
`pytest --cov=src --cov-report=term-missing` shows which lines are not exercised. Coverage above ~80% is healthy; don't chase 100% — chase meaningful tests.

### 14. CI integration.
Run `pytest -q` on every PR. Cache pip and Spark to keep CI fast. Fail the build on test or coverage regression. Publish JUnit XML so the CI system shows per-test results.
