from __future__ import annotations

from app.repositories.event_repository import EventRepository


class EventService:
    def __init__(self) -> None:
        self.repository = EventRepository()

    def publish(
        self,
        task_id: str,
        event_type: str,
        message: str,
        *,
        level: str = "info",
        sub_task_id: str | None = None,
        payload: dict | None = None,
    ) -> int:
        return self.repository.append(
            task_id=task_id,
            event_type=event_type,
            message=message,
            level=level,
            sub_task_id=sub_task_id,
            payload=payload,
        )


event_service = EventService()

