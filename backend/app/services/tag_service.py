from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.errors import AppError
from app.models.base import utcnow
from app.models.files import KnowledgeFile
from app.models.knowledge import KnowledgeUnit, Tag, TagBinding
from app.models.wiki import WikiPage

SUPPORTED_TAG_TARGETS = {
    "file": KnowledgeFile,
    "knowledge_unit": KnowledgeUnit,
    "wiki_page": WikiPage,
}


@dataclass(frozen=True)
class TagWithBindingCount:
    tag: Tag
    binding_count: int


class TagNotFoundError(AppError):
    def __init__(self) -> None:
        super().__init__(code="TAG_NOT_FOUND", message="Tag not found.", status_code=404)


class TagNameAlreadyExistsError(AppError):
    def __init__(self) -> None:
        super().__init__(
            code="TAG_NAME_ALREADY_EXISTS",
            message="Tag name already exists.",
            status_code=409,
        )


class TagInvalidTargetTypeError(AppError):
    def __init__(self) -> None:
        super().__init__(
            code="TAG_INVALID_TARGET_TYPE",
            message="Tag target_type is not supported.",
            status_code=400,
        )


class TagTargetNotFoundError(AppError):
    def __init__(self) -> None:
        super().__init__(
            code="TAG_TARGET_NOT_FOUND",
            message="Tag target was not found.",
            status_code=404,
        )


class TagBindingNotFoundError(AppError):
    def __init__(self) -> None:
        super().__init__(
            code="TAG_BINDING_NOT_FOUND",
            message="Tag binding was not found.",
            status_code=404,
        )


class TagService:
    def __init__(self, *, session: Session) -> None:
        self.session = session

    def create_tag(
        self,
        *,
        name: str,
        description: str | None = None,
        color: str | None = None,
    ) -> Tag:
        self._ensure_name_available(name)
        tag = Tag(name=name.strip(), description=description, color=color)
        self.session.add(tag)
        self._commit_or_duplicate_name()
        self.session.refresh(tag)
        return tag

    def list_tags(self) -> list[TagWithBindingCount]:
        statement = (
            select(Tag, func.count(TagBinding.id))
            .outerjoin(TagBinding, TagBinding.tag_id == Tag.id)
            .group_by(Tag.id)
            .order_by(Tag.name.asc())
        )
        return [
            TagWithBindingCount(tag=tag, binding_count=count)
            for tag, count in self.session.execute(statement).all()
        ]

    def get_tag(self, tag_id: UUID) -> Tag:
        tag = self.session.get(Tag, tag_id)
        if tag is None:
            raise TagNotFoundError()
        return tag

    def update_tag(
        self,
        tag_id: UUID,
        *,
        name: str,
        description: str | None = None,
        color: str | None = None,
    ) -> Tag:
        tag = self.get_tag(tag_id)
        normalized_name = name.strip()
        if normalized_name != tag.name:
            self._ensure_name_available(normalized_name)
        tag.name = normalized_name
        tag.description = description
        tag.color = color
        self.session.add(tag)
        self._commit_or_duplicate_name()
        self.session.refresh(tag)
        return tag

    def delete_tag(self, tag_id: UUID) -> None:
        tag = self.get_tag(tag_id)
        self.session.query(TagBinding).filter(TagBinding.tag_id == tag_id).delete()
        self.session.delete(tag)
        self.session.commit()

    def bind_tag(self, *, tag_id: UUID, target_type: str, target_id: UUID) -> TagBinding:
        self.get_tag(tag_id)
        self._validate_target(target_type, target_id)
        existing = self._find_binding(tag_id=tag_id, target_type=target_type, target_id=target_id)
        if existing is not None:
            return existing

        binding = TagBinding(
            tag_id=tag_id,
            target_type=target_type,
            target_id=target_id,
            created_at=utcnow(),
        )
        self.session.add(binding)
        try:
            self.session.commit()
        except IntegrityError:
            self.session.rollback()
            existing = self._find_binding(
                tag_id=tag_id,
                target_type=target_type,
                target_id=target_id,
            )
            if existing is None:
                raise
            return existing
        self.session.refresh(binding)
        return binding

    def remove_binding(self, *, tag_id: UUID, target_type: str, target_id: UUID) -> None:
        binding = self._find_binding(tag_id=tag_id, target_type=target_type, target_id=target_id)
        if binding is None:
            raise TagBindingNotFoundError()
        self.session.delete(binding)
        self.session.commit()

    def tag_ids_for_target(self, *, target_type: str, target_id: UUID) -> list[UUID]:
        statement = (
            select(TagBinding.tag_id)
            .where(TagBinding.target_type == target_type)
            .where(TagBinding.target_id == target_id)
            .order_by(TagBinding.created_at.asc())
        )
        return list(self.session.scalars(statement).all())

    def tags_for_target(self, *, target_type: str, target_id: UUID) -> list[Tag]:
        statement = (
            select(Tag)
            .join(TagBinding, TagBinding.tag_id == Tag.id)
            .where(TagBinding.target_type == target_type)
            .where(TagBinding.target_id == target_id)
            .order_by(Tag.name.asc())
        )
        return list(self.session.scalars(statement).all())

    def replace_target_tags(self, *, target_type: str, target_id: UUID, tag_ids: list[UUID]) -> None:
        self._validate_target(target_type, target_id)
        for tag_id in tag_ids:
            self.get_tag(tag_id)
        self.session.query(TagBinding).filter(
            TagBinding.target_type == target_type,
            TagBinding.target_id == target_id,
        ).delete()
        for tag_id in tag_ids:
            self.session.add(
                TagBinding(
                    tag_id=tag_id,
                    target_type=target_type,
                    target_id=target_id,
                    created_at=utcnow(),
                )
            )
        self.session.commit()

    def _ensure_name_available(self, name: str) -> None:
        statement = select(Tag).where(Tag.name == name.strip()).limit(1)
        if self.session.scalar(statement) is not None:
            raise TagNameAlreadyExistsError()

    def _commit_or_duplicate_name(self) -> None:
        try:
            self.session.commit()
        except IntegrityError as exc:
            self.session.rollback()
            if "tags" in str(exc).lower():
                raise TagNameAlreadyExistsError() from exc
            raise

    def _validate_target(self, target_type: str, target_id: UUID) -> None:
        model = SUPPORTED_TAG_TARGETS.get(target_type)
        if model is None:
            raise TagInvalidTargetTypeError()
        if self.session.get(model, target_id) is None:
            raise TagTargetNotFoundError()

    def _find_binding(
        self,
        *,
        tag_id: UUID,
        target_type: str,
        target_id: UUID,
    ) -> TagBinding | None:
        statement = (
            select(TagBinding)
            .where(TagBinding.tag_id == tag_id)
            .where(TagBinding.target_type == target_type)
            .where(TagBinding.target_id == target_id)
            .limit(1)
        )
        return self.session.scalar(statement)
