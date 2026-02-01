from pydantic import BaseModel, Field
from typing import Any, Dict, Optional


class WorkItem(BaseModel):
    correlation_id: str = Field(default_factory=str)
    input_text: str
    metadata: Dict[str, Any] = Field(default_factory=dict)


class WorkResult(BaseModel):
    correlation_id: str
    output_text: str
    details: Dict[str, Any] = Field(default_factory=dict)
    intent: Optional[str] = None
