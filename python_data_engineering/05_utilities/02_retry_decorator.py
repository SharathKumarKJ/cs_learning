from collections.abc import Callable
from functools import wraps
from time import sleep
from typing import Optional, TypeVar


T = TypeVar("T")


def retry(times: int, delay_seconds: float = 0.0) -> Callable[[Callable[..., T]], Callable[..., T]]:
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args: object, **kwargs: object) -> T:
            last_error: Optional[Exception] = None
            for _ in range(times):
                try:
                    return func(*args, **kwargs)
                except Exception as error:
                    last_error = error
                    sleep(delay_seconds)
            raise RuntimeError("All retry attempts failed") from last_error
        return wrapper
    return decorator


attempts = {"count": 0}


@retry(times=3)
def unstable_job() -> str:
    attempts["count"] += 1
    if attempts["count"] < 3:
        raise ValueError("Temporary failure")
    return "success"


def main() -> None:
    print(unstable_job())


if __name__ == "__main__":
    main()
