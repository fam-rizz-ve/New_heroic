"""SQLAlchemy model for Library."""

from __future__ import annotations

from datetime import datetime
from uuid import uuid4

from sqlalchemy import DateTime, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.core.domain.enums import StoreSource
from app.core.domain.library import Library as DomainLibrary
from app.core.domain.value_objects import LibraryId


class LibraryModel(Base):
    """SQLAlchemy model matching the Library domain entity."""

    __tablename__ = "libraries"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid4())
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    store_source: Mapped[str] = mapped_column(String(50), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    def to_domain(self) -> DomainLibrary:
        """Convert ORM model to domain Library."""
        return DomainLibrary(
            id=LibraryId.from_str(self.id),
            name=self.name,
            store_source=StoreSource(self.store_source),
            created_at=self.created_at,
            updated_at=self.updated_at,
        )

    @classmethod
    def from_domain(cls, library: DomainLibrary) -> LibraryModel:
        """Create ORM model from domain Library."""
        return cls(
            id=str(library.id.value),
            name=library.name,
            store_source=library.store_source.value,
            created_at=library.created_at,
            updated_at=library.updated_at,
        )

    def update_from_domain(self, library: DomainLibrary) -> None:
        """Update ORM model fields from domain Library."""
        self.name = library.name
        self.store_source = library.store_source.value
        self.updated_at = library.updated_at
