import asyncio
import json
import time
import uuid
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from app.api.deps import get_db, broadcaster
from app.api.routes_mandate import serialize_mandate
from app.core.database import AuditLogORM, MandateORM, TransactionORM
from app.models.schemas import (
    AgentSpendRequest,
    AuditLogResponse,
    MandateStatus,
    NettingSummaryResponse,
    SettlementExecutionResponse,
    TransactionResponse,
    TxnStatus,
)
from app.services.assertion_runner import run_assertions
from app.services.netting_ledger import NettingLedgerManager
from app.services.paypal_client import paypal_client
from app.services.policy_engine import validate_transaction

router = APIRouter(prefix="/api/transactions", tags=["Transactions"])


def serialize_transaction(
    txn: TransactionORM,
    latency_ms: Optional[float] = None,
) -> TransactionResponse:
    deliverable_obj: Optional[Dict[str, Any]] = None
    if txn.deliverablePayload:
        try:
            deliverable_obj = json.loads(txn.deliverablePayload)
        except Exception:
            deliverable_obj = {"raw": txn.deliverablePayload}

    audit_list: List[AuditLogResponse] = []
    for log in txn.auditLogs:
        try:
            detail_obj = json.loads(log.detailJson)
        except Exception:
            detail_obj = {"raw": log.detailJson}
        if latency_ms is None and "latency_ms" in detail_obj:
            latency_ms = float(detail_obj["latency_ms"])
        audit_list.append(
            AuditLogResponse(
                id=log.id,
                transactionId=log.transactionId,
                eventType=log.eventType,
                actor=log.actor,
                decision=log.decision,
                detailJson=detail_obj,
                createdAt=log.createdAt,
            )
        )

    return TransactionResponse(
        id=txn.id,
        mandateId=txn.mandateId,
        buyerAgentId=txn.buyerAgentId,
        sellerAgentId=txn.sellerAgentId,
        sellerPaypalEmail=txn.sellerPaypalEmail,
        amount=round(txn.amount, 2),
        category=txn.category,
        promptPayload=txn.promptPayload,
        deliverablePayload=deliverable_obj,
        status=txn.status,
        rejectionReason=txn.rejectionReason,
        netted=txn.netted,
        payoutBatchId=txn.payoutBatchId,
        latencyMs=latency_ms,
        createdAt=txn.createdAt,
        auditLogs=audit_list,
    )


@router.post("/spend", response_model=TransactionResponse)
async def execute_agent_spend(
    req: AgentSpendRequest,
    db: Session = Depends(get_db),
) -> TransactionResponse:
    """
    Full MandatePay Autonomous Transaction Pipeline:
    1. Deterministic Policy Engine & Prompt Injection Shield (<5ms).
    2. Contract Deliverable Assertion Runner.
    3. Off-Chain Ledger Update & Real-time SSE Broadcast.
    """
    mandate = db.query(MandateORM).filter(MandateORM.id == req.mandate_id).first()
    if not mandate:
        raise HTTPException(
            status_code=404,
            detail=f"Mandate '{req.mandate_id}' not found.",
        )

    pipeline_start_ns = time.perf_counter_ns()

    # Step 1: Deterministic Policy Engine + Prompt Injection Filter
    policy_res = validate_transaction(mandate, req)
    final_status = policy_res.status
    rejection_reason: Optional[str] = None if policy_res.passed else policy_res.reason
    event_type = "GUARDRAIL_CHECK"

    # Step 2: Contract Deliverable Assertions (if policy passed)
    if policy_res.passed:
        assertion_passed, assertion_msg = run_assertions(
            deliverable=req.deliverable,
            rules=mandate.assertionSchema,
        )
        if not assertion_passed:
            final_status = TxnStatus.BLOCKED_ASSERTION_FAILED.value
            rejection_reason = assertion_msg
            event_type = "ASSERTION_VERIFICATION_FAILED"
        else:
            final_status = TxnStatus.APPROVED.value
            rejection_reason = None
            event_type = "CONTRACT_VERIFIED_APPROVED"
    else:
        if final_status == TxnStatus.BLOCKED_INJECTION.value:
            event_type = "PROMPT_INJECTION_INTERCEPTED"
        else:
            event_type = "POLICY_GUARDRAIL_BLOCKED"

    total_latency_ms = round((time.perf_counter_ns() - pipeline_start_ns) / 1_000_000, 3)

    # Step 3: Persist Transaction & Update Mandate Spend if APPROVED
    txn = TransactionORM(
        mandateId=mandate.id,
        buyerAgentId=req.buyer_agent_id,
        sellerAgentId=req.seller_agent_id,
        sellerPaypalEmail=str(req.seller_paypal_email),
        amount=round(req.amount, 2),
        category=req.category,
        promptPayload=req.prompt_payload,
        deliverablePayload=json.dumps(req.deliverable) if req.deliverable is not None else None,
        status=final_status,
        rejectionReason=rejection_reason,
        netted=False,
    )
    db.add(txn)
    db.flush()

    diagnostic_trace = {
        "mandate_id": mandate.id,
        "buyer_agent_id": req.buyer_agent_id,
        "seller_agent_id": req.seller_agent_id,
        "seller_paypal_email": str(req.seller_paypal_email),
        "requested_amount": req.amount,
        "category": req.category,
        "status": final_status,
        "reason": rejection_reason or "Transaction approved and queued in Off-Chain Netting Ledger.",
        "matched_signature": policy_res.matched_signature,
        "latency_ms": total_latency_ms,
        "prompt_payload": req.prompt_payload,
        "deliverable_payload": req.deliverable,
        "expected_assertion_schema": json.loads(mandate.assertionSchema),
    }

    audit_log = AuditLogORM(
        transactionId=txn.id,
        eventType=event_type,
        actor=req.buyer_agent_id,
        decision=final_status,
        detailJson=json.dumps(diagnostic_trace),
    )
    db.add(audit_log)

    if final_status == TxnStatus.APPROVED.value:
        mandate.currentSpent = round(mandate.currentSpent + req.amount, 2)
        if mandate.currentSpent >= mandate.totalBudgetLimit:
            mandate.status = MandateStatus.EXHAUSTED.value

    db.commit()
    db.refresh(txn)
    db.refresh(mandate)

    serialized_txn = serialize_transaction(txn, latency_ms=total_latency_ms)
    serialized_mandate = serialize_mandate(mandate)

    await broadcaster.broadcast("transaction_created", serialized_txn.model_dump(mode="json"))
    await broadcaster.broadcast("mandate_updated", serialized_mandate.model_dump(mode="json"))

    return serialized_txn


@router.get("", response_model=List[TransactionResponse])
def list_transactions(
    mandate_id: Optional[str] = Query(default=None),
    db: Session = Depends(get_db),
) -> List[TransactionResponse]:
    query = db.query(TransactionORM)
    if mandate_id:
        query = query.filter(TransactionORM.mandateId == mandate_id)
    txns = query.order_by(TransactionORM.createdAt.desc()).limit(200).all()
    return [serialize_transaction(t) for t in txns]


@router.get("/netting", response_model=NettingSummaryResponse)
def get_netting_preview(
    mandate_id: Optional[str] = Query(default=None),
    db: Session = Depends(get_db),
) -> NettingSummaryResponse:
    """
    Computes the real-time Off-Chain Netting preview for all `APPROVED` (unsettled) transactions.
    """
    query = db.query(TransactionORM).filter(
        TransactionORM.status == TxnStatus.APPROVED.value,
        TransactionORM.netted == False,  # noqa: E712
    )
    if mandate_id:
        query = query.filter(TransactionORM.mandateId == mandate_id)
    txns = query.all()

    records = [
        {
            "id": t.id,
            "buyer_email": t.mandate.ownerEmail if t.mandate else "vault@mandatepay.io",
            "seller_email": t.sellerPaypalEmail,
            "amount": t.amount,
            "seller_agent_id": t.sellerAgentId,
            "buyer_agent_id": t.buyerAgentId,
        }
        for t in txns
    ]
    _, summary = NettingLedgerManager.compute_from_records(records, mandate_id=mandate_id)
    return summary


@router.post("/settle", response_model=SettlementExecutionResponse)
async def execute_net_settlement(
    mandate_id: Optional[str] = Query(default=None),
    db: Session = Depends(get_db),
) -> SettlementExecutionResponse:
    """
    Consolidates all `APPROVED` transactions in the Off-Chain Netting Ledger and
    dispatches a single batch payout via PayPal Payouts API v1 (`POST /v1/payments/payouts`)
    with an idempotency `PayPal-Request-Id` UUID header.
    """
    query = db.query(TransactionORM).filter(
        TransactionORM.status == TxnStatus.APPROVED.value,
        TransactionORM.netted == False,  # noqa: E712
    )
    if mandate_id:
        query = query.filter(TransactionORM.mandateId == mandate_id)
    txns = query.all()

    if not txns:
        raise HTTPException(
            status_code=400,
            detail="No pending APPROVED transactions in ledger to settle.",
        )

    ledger = NettingLedgerManager()
    for t in txns:
        ledger.add_transaction(
            transaction_id=t.id,
            buyer_email=t.mandate.ownerEmail if t.mandate else "vault@mandatepay.io",
            seller_email=t.sellerPaypalEmail,
            amount=t.amount,
            seller_agent_id=t.sellerAgentId,
            buyer_agent_id=t.buyerAgentId,
        )

    paypal_items, summary = ledger.calculate_netting(mandate_id=mandate_id)
    batch_id = f"MANDATEPAY_BATCH_{time.strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:4].upper()}"
    idempotency_key = str(uuid.uuid4())

    paypal_resp = await paypal_client.execute_batch_payout(
        batch_id=batch_id,
        items=paypal_items,
        request_id=idempotency_key,
    )

    payout_batch_id = (
        paypal_resp.get("batch_header", {}).get("payout_batch_id") or batch_id
    )
    batch_status = (
        paypal_resp.get("batch_header", {}).get("batch_status") or "SUCCESS"
    )

    settled_ids: List[str] = []
    for t in txns:
        t.status = TxnStatus.SETTLED.value
        t.netted = True
        t.payoutBatchId = payout_batch_id
        settled_ids.append(t.id)

        settle_log = AuditLogORM(
            transactionId=t.id,
            eventType="PAYPAL_BATCH_SETTLED",
            actor="MANDATEPAY_NETTING_ENGINE",
            decision=TxnStatus.SETTLED.value,
            detailJson=json.dumps(
                {
                    "payout_batch_id": payout_batch_id,
                    "sender_batch_id": batch_id,
                    "idempotency_request_id": idempotency_key,
                    "batch_status": batch_status,
                }
            ),
        )
        db.add(settle_log)

    db.commit()

    settlement_resp = SettlementExecutionResponse(
        batch_id=payout_batch_id,
        paypal_batch_status=batch_status,
        settled_transaction_ids=settled_ids,
        netting_summary=summary,
        paypal_response=paypal_resp,
    )

    await broadcaster.broadcast(
        "batch_settled",
        settlement_resp.model_dump(mode="json"),
    )
    return settlement_resp


@router.get("/stream")
async def stream_transactions(request: Request) -> StreamingResponse:
    """
    Server-Sent Events (SSE) endpoint (`GET /api/transactions/stream`) pushing
    real-time updates (`transaction_created`, `mandate_updated`, `batch_settled`)
    to AG Grid and Dashboard components.
    """
    queue = broadcaster.subscribe()

    async def event_generator():
        try:
            yield f"data: {json.dumps({'event': 'connected', 'data': {'status': 'STREAM_ONLINE'}})}\n\n"
            while True:
                if await request.is_disconnected():
                    break
                try:
                    msg = await asyncio.wait_for(queue.get(), timeout=15.0)
                    yield f"data: {msg}\n\n"
                except asyncio.TimeoutError:
                    yield ": keep-alive\n\n"
        finally:
            broadcaster.unsubscribe(queue)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )

