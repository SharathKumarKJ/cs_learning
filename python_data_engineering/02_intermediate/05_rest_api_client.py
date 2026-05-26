"""REST API client pattern with retry-ready structure (no external deps)."""
import json
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


def http_get_json(url: str, headers: dict | None = None, timeout: int = 10) -> dict:
    request = Request(url, headers=headers or {})
    try:
        with urlopen(request, timeout=timeout) as response:
            return json.loads(response.read().decode("utf-8"))
    except HTTPError as error:
        raise RuntimeError(f"HTTP {error.code} for {url}") from error
    except URLError as error:
        raise RuntimeError(f"Connection failed for {url}") from error


def main() -> None:
    # Replace URL with a real endpoint in real use.
    print("This is a template; call http_get_json(url) with a real endpoint.")


if __name__ == "__main__":
    main()
