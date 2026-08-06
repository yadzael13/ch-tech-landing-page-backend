"""TestimonialRepository port (ADR-0012, ARCHITECTURE.md, Fase 6)."""

import uuid
from dataclasses import dataclass
from typing import Protocol

from app.domain.testimonial import Testimonial


@dataclass(slots=True)
class TestimonialInput:
    author_name: str
    author_role: str | None
    client_id: uuid.UUID | None
    project_id: uuid.UUID | None
    content: str
    rating: int | None
    featured: bool = False


class TestimonialRepository(Protocol):
    async def list(self) -> list[Testimonial]: ...

    async def create(self, data: TestimonialInput) -> Testimonial: ...

    async def update(
        self, testimonial_id: uuid.UUID, data: TestimonialInput
    ) -> Testimonial | None: ...

    async def delete(self, testimonial_id: uuid.UUID) -> bool: ...
