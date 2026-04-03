from __future__ import annotations


class V2Error(Exception):
    def __init__(self, message: str, *, status_code: int = 400) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code


class NotFoundError(V2Error):
    def __init__(self, message: str) -> None:
        super().__init__(message, status_code=404)


class ConflictError(V2Error):
    def __init__(self, message: str) -> None:
        super().__init__(message, status_code=409)


class DependencyError(V2Error):
    def __init__(self, message: str) -> None:
        super().__init__(message, status_code=503)
