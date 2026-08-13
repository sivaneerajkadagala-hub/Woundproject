from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel

class ReportResponse(BaseModel):
    assessment_id: int
    pdf_url: str
    generated_at: datetime
    disclaimer: str
