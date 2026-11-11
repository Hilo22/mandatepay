from datetime import datetime
from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, EmailStr, ConfigDict


class DeliverableFormat(str, Enum):
    JSON = "json"
    TEXT = "text"
    BINARY = "binary"


class MandateStatus(str, Enum):
    AWAITING_PAYMENT = "AWAITING_PAYMENT"
    ACTIVE = "ACTIVE"
    EXHAUSTED = "EXHAUSTED"
    SUSPENDED = "SUSPENDED"


class TxnStatus(str, Enum):
    APPROVED = "APPROVED"
    BLOCKED_POLICY = "BLOCKED_POLICY"
    BLOCKED_INJECTION = "BLOCKED_INJECTION"
    BLOCKED_ASSERTION_FAILED = "BLOCKED_ASSERTION_FAILED"
    SETTLED = "SETTLED"


class AssertionRule(BaseModel):
    format: DeliverableFormat = DeliverableFormat.JSON
    required_keys: List[str] = Field(default_factory=list)
    min_length: int = 0


class CompiledMandatePolicy(BaseModel):
    owner_paypal_email: EmailStr
    total_budget_limit: float = Field(..., ge=1.0, le=1000.0)
    max_charge_per_txn: float = Field(..., ge=0.01, le=100.0)
    allowed_categories: List[str]
    assertion_schema: AssertionRule


class MandateCreateRequest(BaseModel):
    prompt: str = Field(
        ...,
        json_schema_extra={
            "example": "Allocate $30 for NLP data labeling tasks. Max $3 per task. Require deliverable JSON keys 'record_id' and 'sentiment'."
        },
    )
    owner_paypal_email: EmailStr = Field(
        default="buyer_owner@sandbox.paypal.com",
        json_schema_extra={"example": "buyer_owner@sandbox.paypal.com"},
    )
    auto_activate: bool = Field(
        default=False,
        description="If true, automatically captures sandbox top-up and transitions to ACTIVE for instant testing.",
    )


class MandateResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    ownerEmail: str
    totalBudgetLimit: float
    currentSpent: float
    maxChargePerTxn: float
    allowedCategories: List[str]
    assertionSchema: AssertionRule
    paypalOrderId: Optional[str] = None
    approvalUrl: Optional[str] = None
    status: str
    createdAt: datetime
    updatedAt: datetime


class AgentSpendRequest(BaseModel):
    mandate_id: str
    buyer_agent_id: str
    seller_agent_id: str
    seller_paypal_email: EmailStr
    amount: float
    category: str
    prompt_payload: str
    deliverable: Optional[Dict[str, Any]] = None


class ValidationResult(BaseModel):
    passed: bool
    status: str
    reason: Optional[str] = None
    latency_ms: float = 0.0
    matched_signature: Optional[str] = None


class AuditLogResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    transactionId: Optional[str] = None
    eventType: str
    actor: str
    decision: str
    detailJson: Dict[str, Any]
    createdAt: datetime


class TransactionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    mandateId: str
    buyerAgentId: str
    sellerAgentId: str
    sellerPaypalEmail: str
    amount: float
    category: str
    promptPayload: str
    deliverablePayload: Optional[Dict[str, Any]] = None
    status: str
    rejectionReason: Optional[str] = None
    netted: bool
    payoutBatchId: Optional[str] = None
    latencyMs: Optional[float] = None
    createdAt: datetime
    auditLogs: List[AuditLogResponse] = Field(default_factory=list)


class NettingItem(BaseModel):
    recipient_type: str = "EMAIL"
    amount: Dict[str, str]
    note: str
    sender_item_id: str
    receiver: str
    task_count: int = 1


class NettingSummaryResponse(BaseModel):
    mandate_id: Optional[str] = None
    total_gross_volume: float
    total_net_payout: float
    raw_transaction_count: int
    consolidated_payout_count: int
    fee_savings_pct: float
    payout_items: List[NettingItem]


class SettlementExecutionResponse(BaseModel):
    batch_id: str
    paypal_batch_status: str
    settled_transaction_ids: List[str]
    netting_summary: NettingSummaryResponse
    paypal_response: Dict[str, Any]

