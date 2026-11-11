import json
from typing import Any, Dict
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session
from app.api.deps import get_db, broadcaster
from app.api.routes_mandate import serialize_mandate
from app.core.database import AuditLogORM, MandateORM, TransactionORM
from app.models.schemas import MandateStatus, TxnStatus
from app.services.paypal_client import paypal_client

router = APIRouter(prefix="/api/webhooks", tags=["Webhooks"])


@router.post("/paypal")
async def handle_paypal_webhook(
    request: Request,
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """
    PayPal Sandbox Webhook Listener (`POST /api/webhooks/paypal`).
    1. Cryptographically verifies the incoming webhook via PayPal's
       `POST /v1/notifications/verify-webhook-signature`.
    2. Processes events:
       - `PAYMENT.CAPTURE.COMPLETED` -> Activates Mandate (`ACTIVE`).
       - `PAYMENT.PAYOUTSBATCH.SUCCESS` -> Marks batched transactions as `SETTLED`.
       - `PAYMENT.PAYOUTS-ITEM.FAILED` -> Flags transaction failure & alerts AG Grid.
    """
    raw_bytes = await request.body()
    raw_body = raw_bytes.decode("utf-8") if raw_bytes else "{}"
    headers_dict = dict(request.headers)

    is_valid = await paypal_client.verify_webhook_signature(
        headers=headers_dict,
        raw_body=raw_body,
    )
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Webhook cryptographic signature verification failed.",
        )

    event_payload = json.loads(raw_body)
    event_type = event_payload.get("event_type", "")
    resource = event_payload.get("resource", {})

    # 1. PAYMENT.CAPTURE.COMPLETED -> Activate Mandate
    if event_type == "PAYMENT.CAPTURE.COMPLETED":
        order_id = (
            resource.get("supplementary_data", {}).get("related_ids", {}).get("order_id")
            or resource.get("id")
        )
        mandate = None
        if order_id:
            mandate = (
                db.query(MandateORM)
                .filter(MandateORM.paypalOrderId == order_id)
                .first()
            )
        if not mandate:
            mandate = (
                db.query(MandateORM)
                .filter(MandateORM.status == MandateStatus.AWAITING_PAYMENT.value)
                .order_by(MandateORM.createdAt.desc())
                .first()
            )

        if mandate:
            mandate.status = MandateStatus.ACTIVE.value
            db.commit()
            db.refresh(mandate)
            serialized = serialize_mandate(mandate)
            await broadcaster.broadcast("mandate_updated", serialized.model_dump(mode="json"))
            return {
                "status": "WEBHOOK_PROCESSED",
                "event_type": event_type,
                "mandate_id": mandate.id,
                "new_status": mandate.status,
            }

    # 2. PAYMENT.PAYOUTSBATCH.SUCCESS -> Transition queued ledger transactions to SETTLED
    elif event_type == "PAYMENT.PAYOUTSBATCH.SUCCESS":
        batch_header = resource.get("batch_header", {})
        payout_batch_id = batch_header.get("payout_batch_id", "WEBHOOK_BATCH")

        pending_txns = (
            db.query(TransactionORM)
            .filter(TransactionORM.status == TxnStatus.APPROVED.value)
            .all()
        )
        settled_ids = []
        for t in pending_txns:
            t.status = TxnStatus.SETTLED.value
            t.netted = True
            t.payoutBatchId = payout_batch_id
            settled_ids.append(t.id)

        db.commit()
        await broadcaster.broadcast(
            "webhook_payout_settled",
            {"payout_batch_id": payout_batch_id, "settled_ids": settled_ids},
        )
        return {
            "status": "WEBHOOK_PROCESSED",
            "event_type": event_type,
            "payout_batch_id": payout_batch_id,
            "settled_count": len(settled_ids),
        }

    # 3. PAYMENT.PAYOUTS-ITEM.FAILED -> Flag transaction error and push alert to AG Grid
    elif event_type == "PAYMENT.PAYOUTS-ITEM.FAILED":
        transaction_id = resource.get("payout_item", {}).get("sender_item_id")
        error_msg = resource.get("errors", {}).get("message", "Payout item failed at PayPal gateway")
        log = AuditLogORM(
            transactionId=None,
            eventType="PAYOUT_ITEM_FAILED",
            actor="PAYPAL_WEBHOOK",
            decision="FAILED",
            detailJson=json.dumps({"sender_item_id": transaction_id, "error": error_msg}),
        )
        db.add(log)
        db.commit()
        await broadcaster.broadcast(
            "webhook_payout_failed",
            {"sender_item_id": transaction_id, "error": error_msg},
        )
        return {
            "status": "WEBHOOK_PROCESSED",
            "event_type": event_type,
            "error": error_msg,
        }

    return {"status": "WEBHOOK_IGNORED", "event_type": event_type}

