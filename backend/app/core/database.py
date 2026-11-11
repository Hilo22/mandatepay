import uuid
from datetime import datetime, timezone
from typing import Generator, Optional
from sqlalchemy import (
    String,
    Float,
    Boolean,
    DateTime,
    Text,
    ForeignKey,
    create_engine,
)
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    mapped_column,
    relationship,
    sessionmaker,
    Session,
)
from app.core.config import settings


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def generate_uuid() -> str:
    return str(uuid.uuid4())


class Base(DeclarativeBase):
    pass


class MandateORM(Base):
    __tablename__ = "Mandate"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    ownerEmail: Mapped[str] = mapped_column(String(255), nullable=False)
    totalBudgetLimit: Mapped[float] = mapped_column(Float, nullable=False)
    currentSpent: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    maxChargePerTxn: Mapped[float] = mapped_column(Float, nullable=False)
    allowedCategories: Mapped[str] = mapped_column(Text, nullable=False)  # Serialized JSON Array
    assertionSchema: Mapped[str] = mapped_column(Text, nullable=False)    # Serialized JSON Schema
    paypalOrderId: Mapped[Optional[str]] = mapped_column(String(128), unique=True, nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="AWAITING_PAYMENT", nullable=False)
    createdAt: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    updatedAt: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False
    )

    transactions: Mapped[list["TransactionORM"]] = relationship(
        "TransactionORM", back_populates="mandate", cascade="all, delete-orphan"
    )


class TransactionORM(Base):
    __tablename__ = "Transaction"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    mandateId: Mapped[str] = mapped_column(String(36), ForeignKey("Mandate.id"), nullable=False)
    buyerAgentId: Mapped[str] = mapped_column(String(128), nullable=False)
    sellerAgentId: Mapped[str] = mapped_column(String(128), nullable=False)
    sellerPaypalEmail: Mapped[str] = mapped_column(String(255), nullable=False)
    amount: Mapped[float] = mapped_column(Float, nullable=False)
    category: Mapped[str] = mapped_column(String(128), nullable=False)
    promptPayload: Mapped[str] = mapped_column(Text, nullable=False)
    deliverablePayload: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # Serialized JSON
    status: Mapped[str] = mapped_column(String(64), nullable=False)
    rejectionReason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    netted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    payoutBatchId: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    createdAt: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)

    mandate: Mapped["MandateORM"] = relationship("MandateORM", back_populates="transactions")
    auditLogs: Mapped[list["AuditLogORM"]] = relationship(
        "AuditLogORM", back_populates="transaction", cascade="all, delete-orphan"
    )


class AuditLogORM(Base):
    __tablename__ = "AuditLog"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    transactionId: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("Transaction.id"), nullable=True
    )
    eventType: Mapped[str] = mapped_column(String(64), nullable=False)
    actor: Mapped[str] = mapped_column(String(128), nullable=False)
    decision: Mapped[str] = mapped_column(String(64), nullable=False)
    detailJson: Mapped[str] = mapped_column(Text, nullable=False)
    createdAt: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)

    transaction: Mapped[Optional["TransactionORM"]] = relationship("TransactionORM", back_populates="auditLogs")


connect_args = {"check_same_thread": False} if settings.sqlalchemy_database_url.startswith("sqlite") else {}
engine = create_engine(settings.sqlalchemy_database_url, connect_args=connect_args, future=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine, future=True)


def init_db() -> None:
    Base.metadata.create_all(bind=engine)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

