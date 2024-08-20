from sqlalchemy import Index
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import mapped_column, Mapped

from cpvt_database_models.database.base import Base


class KVStore(Base):
    __tablename__ = "kv_store"

    key: Mapped[str] = mapped_column(primary_key=True)
    value: Mapped[dict] = mapped_column(JSONB)

    __table_args__ = (
        Index(
            "ix_kv_store_updated_at",
            "updated_at",
            # use BRIN since these will almost always be inserted in order
            postgresql_using="brin",
        ),
        {
            "comment": "Key-Value store for storing arbitrary data and caching"
            " API responses without needing to spin up Redis",
        },
    )


__all__ = ["KVStore"]
