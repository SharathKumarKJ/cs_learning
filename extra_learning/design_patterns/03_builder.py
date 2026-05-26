"""Builder with fluent interface."""
from __future__ import annotations
from dataclasses import dataclass, field


@dataclass
class Query:
    table: str
    columns: list[str] = field(default_factory=list)
    where: str | None = None
    limit: int | None = None


class QueryBuilder:
    def __init__(self, table: str) -> None:
        self._q = Query(table=table)

    def select(self, *cols: str) -> "QueryBuilder":
        self._q.columns = list(cols); return self

    def where(self, expr: str) -> "QueryBuilder":
        self._q.where = expr; return self

    def limit(self, n: int) -> "QueryBuilder":
        self._q.limit = n; return self

    def build(self) -> Query:
        return self._q


if __name__ == "__main__":
    q = QueryBuilder("orders").select("id", "amount").where("amount > 100").limit(10).build()
    print(q)
