from __future__ import annotations

import re


def _to_error_code(name: str) -> str:
    # Convert class names like ConflictError into CONFLICT_ERROR.
    return re.sub(r"(?<!^)(?=[A-Z])", "_", name).upper()


class V2Error(Exception):
    def __init__(self, message: str, *, status_code: int = 400, code: str | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.code = code or _to_error_code(self.__class__.__name__)


class NotFoundError(V2Error):
    def __init__(self, message: str, *, code: str | None = None) -> None:
        super().__init__(message, status_code=404, code=code)


class ConflictError(V2Error):
    def __init__(self, message: str, *, code: str | None = None) -> None:
        super().__init__(message, status_code=409, code=code)


class DependencyError(V2Error):
    def __init__(self, message: str, *, code: str | None = None) -> None:
        super().__init__(message, status_code=503, code=code)
