"""Strategy: swap algorithm at runtime."""
from __future__ import annotations
from typing import Protocol


class Compressor(Protocol):
    def compress(self, data: bytes) -> bytes: ...


class Gzip:
    def compress(self, data: bytes) -> bytes: return b"gz:" + data


class Zstd:
    def compress(self, data: bytes) -> bytes: return b"zstd:" + data


def save(data: bytes, c: Compressor) -> None:
    print(c.compress(data))


if __name__ == "__main__":
    save(b"hello", Gzip())
    save(b"hello", Zstd())
