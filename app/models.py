from pydantic import BaseModel, HttpUrl
from typing import Literal


class AuditRequest(BaseModel):
    url: HttpUrl


class Issue(BaseModel):
    severity: Literal["error", "warning", "info", "pass"]
    message: str


class CategoryResult(BaseModel):
    name: str
    score: int
    issues: list[Issue]


class AuditResponse(BaseModel):
    url: str
    overall_score: int
    categories: list[CategoryResult]
