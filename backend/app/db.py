from datetime import datetime, timezone

from sqlalchemy import Text, create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker

from app.core.config import DATABASE_URL

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {},
)
SessionLocal = sessionmaker(bind=engine, autoflush=False)


class Base(DeclarativeBase):
    pass


def _now():
    return datetime.now(timezone.utc)


class InvoiceRecord(Base):
    __tablename__ = "invoices"
    id: Mapped[int] = mapped_column(primary_key=True)
    original_name: Mapped[str]
    stored_name: Mapped[str]
    status: Mapped[str]
    data_json: Mapped[str | None] = mapped_column(Text, default=None)
    issues_json: Mapped[str] = mapped_column(Text, default="[]")
    repaired_json: Mapped[str] = mapped_column(Text, default="[]")
    created_at: Mapped[datetime] = mapped_column(default=_now)
    reviewed_at: Mapped[datetime | None] = mapped_column(default=None)


class PurchaseOrderRecord(Base):
    __tablename__ = "purchase_orders"
    po_number: Mapped[str] = mapped_column(primary_key=True)
    data_json: Mapped[str] = mapped_column(Text)


def init_db():
    Base.metadata.create_all(engine)


def get_db():
    with SessionLocal() as db:
        yield db