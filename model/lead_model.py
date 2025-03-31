from pydantic import BaseModel, EmailStr
from typing import Optional

class Lead(BaseModel):
    id: Optional[int] = None
    first_name: str
    last_name: str
    email: EmailStr
    resume: str
    state: Optional[str] = "PENDING"
