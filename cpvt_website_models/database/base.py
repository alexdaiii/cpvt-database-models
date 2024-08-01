import datetime
from typing import Any, TYPE_CHECKING

from sqlalchemy import DateTime, MetaData, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


meta = MetaData(
    naming_convention={
        "ix": "ix_%(column_0_label)s",
        "uq": "uq_%(table_name)s_%(column_0_name)s",
        "ck": "ck_%(table_name)s_%(constraint_name)s",
        "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
        "pk": "pk_%(table_name)s",
    }
)


class CreatedAtMixin:
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), onupdate=func.now(), server_default=func.now()
    )


class BaseBase(DeclarativeBase):
    metadata = meta

    def __str__(self):
        return str(self.to_dict())

    def __repr__(self):
        return str(self)

    def to_dict(self, include_relationships: bool = False) -> dict[str, Any]:
        keys = self.__dict__.keys()
        relationship_keys = {rel.key for rel in self.__mapper__.relationships}

        exclude = {"_sa_instance_state"}
        if not include_relationships:
            exclude |= relationship_keys

        return {
            # if its an object, recurse
            c: (getattr(self, c))
            for c in keys
            if c not in exclude and not c.startswith("_")
        }


class Base(BaseBase, CreatedAtMixin):
    __abstract__ = True

    ...


class PgBase(Base, DeclarativeBase):
    ...


class RdbBase(Base, DeclarativeBase):
    ...


__all__ = ["Base", "PgBase", "RdbBase", "BaseBase"]
