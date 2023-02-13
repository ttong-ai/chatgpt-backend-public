from pydantic import BaseModel, Field
from typing import Optional, List


class ChatContext(BaseModel):
    message: str
    context: str
    instructions: Optional[str] = None
    metadata: Optional[dict] = None

    class Config:
        schema_extra = {
            "example": {
                "message": "User: How's the weather today?",
                "context": "User: Hello world\nAgent: Hello world",
            }
        }
