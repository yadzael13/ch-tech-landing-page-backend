from sqlalchemy import Column, ForeignKey, Table

from app.db.base import Base
from app.db.types import GUID

project_technologies = Table(
    "project_technologies",
    Base.metadata,
    Column("project_id", GUID(), ForeignKey("projects.id"), primary_key=True),
    Column(
        "technology_id",
        GUID(),
        ForeignKey("technologies.id"),
        primary_key=True,
    ),
)

article_technologies = Table(
    "article_technologies",
    Base.metadata,
    Column("article_id", GUID(), ForeignKey("articles.id"), primary_key=True),
    Column(
        "technology_id",
        GUID(),
        ForeignKey("technologies.id"),
        primary_key=True,
    ),
)
