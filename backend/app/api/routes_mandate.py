import json
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.api.deps import get_db, broadcaster
from app.core.database import MandateORM
from app.models.schemas import (
    AssertionRule,
    MandateCreateRequest,
    MandateResponse,
    MandateStatus,
)
from app.services.llm_compiler import compile_mandate_from_prompt
from app.services.paypal_client import paypal_client

router = APIRouter(prefix="/api/mandates", tags=["Mandates"])


def serialize_mandate(mandate: MandateORM, approval_url: Optional[str] = None) -> MandateResponse:
    try:
        categories = json.loads(mandate.allowedCategories)
    except Exception:
        categories = []

    try:
        schema_dict = json.loads(mandate.assertionSchema)
        assertion_rule = AssertionRule(**schema_dict)
    except Exception:
        assertion_rule = AssertionRule()

    return MandateResponse(
        id=mandate.id,
        ownerEmail=mandate.ownerEmail,
        totalBudgetLimit=mandate.totalBudgetLimit,
        currentSpent=round(mandate.currentSpent, 2),
        maxChargePerTxn=mandate.maxChargePerTxn,
        allowedCategories=categories,
        assertionSchema=assertion_rule,
        paypalOrderId=mandate.paypalOrderId,
        approvalUrl=approval_url
        or (
            f"https://www.sandbox.paypal.com/checkoutnow?token={mandate.paypalOrderId}"
            if mandate.paypalOrderId
            else None
        ),
        status=mandate.status,
        createdAt=mandate.createdAt,
        updatedAt=mandate.updatedAt,
    )


@router.post("", response_model=MandateResponse, status_code=status.HTTP_201_CREATED)
async def create_mandate(
    req: MandateCreateRequest,
    db: Session = Depends(get_db),
) -> MandateResponse:
    """
    1. Synthesizes structured `CompiledMandatePolicy` from natural language prompt.
    2. Creates a PayPal Orders API v2 Top-Up order (`POST /v2/checkout/orders`).
    3. Saves Mandate in DB (`AWAITING_PAYMENT` or `ACTIVE` if `auto_activate=True`).
    """
    try:
        compiled = await compile_mandate_from_prompt(
            prompt=req.prompt,
            owner_paypal_email=str(req.owner_paypal_email),
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    # Create PayPal Sandbox Order
    order_resp = await paypal_client.create_order(
        amount=compiled.total_budget_limit,
        reference_id="MANDATE_TOPUP_001",
    )
    paypal_order_id = order_resp.get("id")
    approval_url = None
    for link in order_resp.get("links", []):
        if link.get("rel") == "approve":
            approval_url = link.get("href")
            break

    initial_status = MandateStatus.AWAITING_PAYMENT.value
    if req.auto_activate and paypal_order_id:
        capture_resp = await paypal_client.capture_order(paypal_order_id)
        if capture_resp.get("status") == "COMPLETED":
            initial_status = MandateStatus.ACTIVE.value

    mandate = MandateORM(
        ownerEmail=str(compiled.owner_paypal_email),
        totalBudgetLimit=compiled.total_budget_limit,
        currentSpent=0.0,
        maxChargePerTxn=compiled.max_charge_per_txn,
        allowedCategories=json.dumps(compiled.allowed_categories),
        assertionSchema=json.dumps(compiled.assertion_schema.model_dump()),
        paypalOrderId=paypal_order_id,
        status=initial_status,
    )
    db.add(mandate)
    db.commit()
    db.refresh(mandate)

    resp = serialize_mandate(mandate, approval_url=approval_url)
    await broadcaster.broadcast("mandate_updated", resp.model_dump(mode="json"))
    return resp


@router.get("", response_model=List[MandateResponse])
def list_mandates(db: Session = Depends(get_db)) -> List[MandateResponse]:
    mandates = db.query(MandateORM).order_by(MandateORM.createdAt.desc()).all()
    return [serialize_mandate(m) for m in mandates]


@router.get("/active", response_model=Optional[MandateResponse])
def get_latest_mandate(db: Session = Depends(get_db)) -> Optional[MandateResponse]:
    mandate = db.query(MandateORM).order_by(MandateORM.createdAt.desc()).first()
    if not mandate:
        return None
    return serialize_mandate(mandate)


@router.get("/{mandate_id}", response_model=MandateResponse)
def get_mandate(mandate_id: str, db: Session = Depends(get_db)) -> MandateResponse:
    mandate = db.query(MandateORM).filter(MandateORM.id == mandate_id).first()
    if not mandate:
        raise HTTPException(status_code=404, detail=f"Mandate '{mandate_id}' not found")
    return serialize_mandate(mandate)


@router.post("/{mandate_id}/activate", response_model=MandateResponse)
async def activate_mandate(mandate_id: str, db: Session = Depends(get_db)) -> MandateResponse:
    """
    Captures the PayPal Sandbox Top-Up Order (`POST /v2/checkout/orders/{id}/capture`)
    and transitions the Mandate from `AWAITING_PAYMENT` to `ACTIVE`.
    """
    mandate = db.query(MandateORM).filter(MandateORM.id == mandate_id).first()
    if not mandate:
        raise HTTPException(status_code=404, detail=f"Mandate '{mandate_id}' not found")

    if mandate.paypalOrderId:
        capture_resp = await paypal_client.capture_order(mandate.paypalOrderId)
        if capture_resp.get("status") != "COMPLETED":
            raise HTTPException(
                status_code=400,
                detail=f"PayPal Order capture failed: {capture_resp}",
            )

    mandate.status = MandateStatus.ACTIVE.value
    db.commit()
    db.refresh(mandate)

    resp = serialize_mandate(mandate)
    await broadcaster.broadcast("mandate_updated", resp.model_dump(mode="json"))
    return resp


@router.post("/order/{paypal_order_id}/capture", response_model=MandateResponse)
async def capture_mandate_by_paypal_order(
    paypal_order_id: str,
    db: Session = Depends(get_db),
) -> MandateResponse:
    """
    Captures a PayPal Sandbox Order by its `paypal_order_id` (`token` query param from return_url)
    and transitions the associated Mandate to `ACTIVE`.
    """
    mandate = (
        db.query(MandateORM)
        .filter(MandateORM.paypalOrderId == paypal_order_id)
        .first()
    )
    if not mandate:
        raise HTTPException(
            status_code=404,
            detail=f"Mandate with PayPal Order '{paypal_order_id}' not found",
        )

    capture_resp = await paypal_client.capture_order(paypal_order_id)
    if capture_resp.get("status") != "COMPLETED":
        raise HTTPException(
            status_code=400,
            detail=f"PayPal Order capture failed: {capture_resp}",
        )

    mandate.status = MandateStatus.ACTIVE.value
    db.commit()
    db.refresh(mandate)

    resp = serialize_mandate(mandate)
    await broadcaster.broadcast("mandate_updated", resp.model_dump(mode="json"))
    return resp


