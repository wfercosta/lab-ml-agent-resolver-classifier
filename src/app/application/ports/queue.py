from dataclasses import dataclass
from typing import Protocol, List, Optional, Any


@dataclass(frozen=True)
class QueueMessage:
    message_id: str
    receipt_handle: str
    body: str
    attributes: dict[str, Any]


class QueuePort(Protocol):
    def receive(self, max_messages: int, wait_time_seconds: int, visibility_timeout: int) -> List[QueueMessage]:
        pass

    def delete(self, receipt_handle: str) -> None:
        pass

    def change_visibility(self, receipt_handle: str, timeout_seconds: int) -> None:
        pass
