"""CaseStudy use cases (ADR-0012, Fase 4).

Create/Update depend on ProjectRepository too — a case study must reference
an existing project (API.md, _assert_project_exists in the pre-migration
router), reusing the port the projects pilot (Fase 3) already established
instead of duplicating an existence check.
"""

import uuid
from dataclasses import dataclass

from app.application.ports.case_study_repository import (
    CaseStudyInput,
    CaseStudyRepository,
)
from app.application.ports.project_repository import ProjectRepository
from app.core.errors import ResourceNotFoundError
from app.domain.case_study import CaseStudy


@dataclass(slots=True)
class ListCaseStudies:
    repository: CaseStudyRepository

    async def execute(self, *, public_only: bool) -> list[CaseStudy]:
        return await self.repository.list(public_only=public_only)


@dataclass(slots=True)
class GetCaseStudyById:
    repository: CaseStudyRepository

    async def execute(
        self, case_study_id: uuid.UUID, *, public_only: bool
    ) -> CaseStudy:
        result = await self.repository.get_by_id(case_study_id, public_only=public_only)
        if result is None:
            raise ResourceNotFoundError("Case study not found")
        return result


@dataclass(slots=True)
class CreateCaseStudy:
    repository: CaseStudyRepository
    project_repository: ProjectRepository

    async def execute(self, data: CaseStudyInput) -> CaseStudy:
        if await self.project_repository.get_by_id(data.project_id) is None:
            raise ResourceNotFoundError("Project not found")
        return await self.repository.create(data)


@dataclass(slots=True)
class UpdateCaseStudy:
    repository: CaseStudyRepository
    project_repository: ProjectRepository

    async def execute(
        self, case_study_id: uuid.UUID, data: CaseStudyInput
    ) -> CaseStudy:
        if await self.repository.get_by_id(case_study_id, public_only=False) is None:
            raise ResourceNotFoundError("Case study not found")
        if await self.project_repository.get_by_id(data.project_id) is None:
            raise ResourceNotFoundError("Project not found")

        result = await self.repository.update(case_study_id, data)
        if result is None:
            raise ResourceNotFoundError("Case study not found")
        return result


@dataclass(slots=True)
class DeleteCaseStudy:
    repository: CaseStudyRepository

    async def execute(self, case_study_id: uuid.UUID) -> None:
        deleted = await self.repository.delete(case_study_id)
        if not deleted:
            raise ResourceNotFoundError("Case study not found")
