"""Repository: hide persistence behind an interface."""
from __future__ import annotations
from dataclasses import dataclass
from typing import Protocol


@dataclass
class User:
    id: int
    name: str


class UserRepo(Protocol):
    def get(self, id: int) -> User | None: ...
    def save(self, u: User) -> None: ...


class InMemoryRepo:
    def __init__(self) -> None: self._store: dict[int, User] = {}
    def get(self, id: int) -> User | None: return self._store.get(id)
    def save(self, u: User) -> None: self._store[u.id] = u


class Service:
    def __init__(self, repo: UserRepo) -> None: self.repo = repo
    def welcome(self, id: int) -> str:
        u = self.repo.get(id)
        return f"welcome {u.name}" if u else "stranger"


if __name__ == "__main__":
    repo = InMemoryRepo(); repo.save(User(1, "Asha"))
    print(Service(repo).welcome(1))
    print(Service(repo).welcome(2))
