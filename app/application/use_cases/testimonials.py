"""Testimonial use cases (ADR-0012, Fase 6).

Create/Update depend on ClientRepository and ProjectRepository too — a
testimonial's client_id/project_id are optional, but when supplied must
reference something real, same reasoning as case_studies validating
project_id (Fase 4).
"""

import uuid
from dataclasses import dataclass

from app.application.ports.client_repository import ClientRepository
from app.application.ports.project_repository import ProjectRepository
from app.application.ports.testimonial_repository import (
    TestimonialInput,
    TestimonialRepository,
)
from app.core.errors import ResourceNotFoundError
from app.domain.testimonial import Testimonial


@dataclass(slots=True)
class ListTestimonials:
    repository: TestimonialRepository

    async def execute(self) -> list[Testimonial]:
        return await self.repository.list()


async def _validate_references(
    data: TestimonialInput,
    *,
    client_repository: ClientRepository,
    project_repository: ProjectRepository,
) -> None:
    if (
        data.client_id is not None
        and await client_repository.get_by_id(data.client_id) is None
    ):
        raise ResourceNotFoundError("Client not found")
    if (
        data.project_id is not None
        and await project_repository.get_by_id(data.project_id) is None
    ):
        raise ResourceNotFoundError("Project not found")


@dataclass(slots=True)
class CreateTestimonial:
    repository: TestimonialRepository
    client_repository: ClientRepository
    project_repository: ProjectRepository

    async def execute(self, data: TestimonialInput) -> Testimonial:
        await _validate_references(
            data,
            client_repository=self.client_repository,
            project_repository=self.project_repository,
        )
        return await self.repository.create(data)


@dataclass(slots=True)
class UpdateTestimonial:
    repository: TestimonialRepository
    client_repository: ClientRepository
    project_repository: ProjectRepository

    async def execute(
        self, testimonial_id: uuid.UUID, data: TestimonialInput
    ) -> Testimonial:
        await _validate_references(
            data,
            client_repository=self.client_repository,
            project_repository=self.project_repository,
        )
        result = await self.repository.update(testimonial_id, data)
        if result is None:
            raise ResourceNotFoundError("Testimonial not found")
        return result


@dataclass(slots=True)
class DeleteTestimonial:
    repository: TestimonialRepository

    async def execute(self, testimonial_id: uuid.UUID) -> None:
        deleted = await self.repository.delete(testimonial_id)
        if not deleted:
            raise ResourceNotFoundError("Testimonial not found")
