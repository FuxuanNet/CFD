from collections.abc import Callable
from typing import TypeVar

from fastapi import HTTPException


T = TypeVar("T")


def as_http_error(action: str, fn: Callable[[], T]) -> T:
    try:
        return fn()
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=f"{action} failed: {exc}") from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except SystemExit as exc:
        raise HTTPException(status_code=500, detail=f"{action} failed: third-party library aborted with code {exc.code}") from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"{action} failed: {exc}") from exc
