from typing import Optional
from pydantic import BaseModel

class AssistantRequest(BaseModel):
    message: str
    wound_id: Optional[int] = None
    patient_id: Optional[int] = None

class AssistantResponse(BaseModel):
    reply: str
    disclaimer: str = "This assistant is a decision-support demonstration tool and does not provide diagnostic or medical opinions."
