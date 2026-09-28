from pydantic import BaseModel
from app.domain.errors import ErrorCode


class ErrorResponse(BaseModel):
    code: ErrorCode
    message: str