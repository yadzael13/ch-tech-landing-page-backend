"""CaseStudyRepository port (ADR-0012, ARCHITECTURE.md, Fase 4)."""

import uuid
from dataclasses import dataclass
from typing import Any, Protocol

from app.domain.case_study import CaseStudy


@dataclass(slots=True)
class CaseStudyInput:
    project_id: uuid.UUID
    challenge: str | None
    solution: str | None
    architecture: str | None
    lessons_learned: str | None
    metrics: dict[str, Any] | None


class CaseStudyRepository(Protocol):
    async def list(self, *, public_only: bool) -> list[CaseStudy]: ...

    async def get_by_id(
        self, case_study_id: uuid.UUID, *, public_only: bool
    ) -> CaseStudy | None: ...

    async def create(self, data: CaseStudyInput) -> CaseStudy: ...

    async def update(
        self, case_study_id: uuid.UUID, data: CaseStudyInput
    ) -> CaseStudy | None: ...

    async def delete(self, case_study_id: uuid.UUID) -> bool: ...
