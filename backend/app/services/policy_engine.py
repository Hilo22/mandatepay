import json
import time
from typing import List, Union
from app.core.database import MandateORM
from app.core.security import inspect_prompt_injection
from app.models.schemas import AgentSpendRequest, ValidationResult, TxnStatus


def _parse_categories(raw_categories: Union[str, List[str]]) -> List[str]:
    if isinstance(raw_categories, list):
        return [str(c).strip().lower() for c in raw_categories]
    try:
        parsed = json.loads(raw_categories)
        if isinstance(parsed, list):
            return [str(c).strip().lower() for c in parsed]
    except Exception:
        pass
    return [c.strip().lower() for c in str(raw_categories).split(",") if c.strip()]


def validate_transaction(mandate: MandateORM, req: AgentSpendRequest) -> ValidationResult:
    """
    Deterministic Policy Engine executing in < 5ms without external LLM calls.
    Step 1: Prompt Injection Shield (scans prompt_payload and deliverable).
    Step 2: Mandate Lifecycle Status verification.
    Step 3: Per-Transaction Hard Cap verification.
    Step 4: Total Aggregate Budget Limit verification.
    Step 5: Category Whitelist verification.
    """
    start_ns = time.perf_counter_ns()

    # 1. Scan prompt_payload & deliverable for prompt injection
    combined_text = req.prompt_payload or ""
    if req.deliverable:
        try:
            combined_text += " " + json.dumps(req.deliverable)
        except Exception:
            combined_text += " " + str(req.deliverable)

    is_injected, injection_reason = inspect_prompt_injection(combined_text)
    if is_injected:
        elapsed_ms = round((time.perf_counter_ns() - start_ns) / 1_000_000, 3)
        return ValidationResult(
            passed=False,
            status=TxnStatus.BLOCKED_INJECTION.value,
            reason=f"Deterministic Policy Engine dropped request in {elapsed_ms}ms without financial impact. {injection_reason}",
            latency_ms=elapsed_ms,
            matched_signature=injection_reason,
        )

    # 2. Check Mandate status
    if mandate.status not in ("ACTIVE", "MANDATE_ACTIVE"):
        elapsed_ms = round((time.perf_counter_ns() - start_ns) / 1_000_000, 3)
        return ValidationResult(
            passed=False,
            status=TxnStatus.BLOCKED_POLICY.value,
            reason=f"Mandate is currently '{mandate.status}' (must be ACTIVE).",
            latency_ms=elapsed_ms,
        )

    # 3. Check per-transaction cap
    if req.amount <= 0:
        elapsed_ms = round((time.perf_counter_ns() - start_ns) / 1_000_000, 3)
        return ValidationResult(
            passed=False,
            status=TxnStatus.BLOCKED_POLICY.value,
            reason=f"Transaction amount (${req.amount:.2f}) must be greater than $0.00.",
            latency_ms=elapsed_ms,
        )

    if req.amount > mandate.maxChargePerTxn:
        elapsed_ms = round((time.perf_counter_ns() - start_ns) / 1_000_000, 3)
        return ValidationResult(
            passed=False,
            status=TxnStatus.BLOCKED_POLICY.value,
            reason=(
                f"Amount ${req.amount:.2f} exceeds per-transaction cap "
                f"of ${mandate.maxChargePerTxn:.2f}."
            ),
            latency_ms=elapsed_ms,
        )

    # 4. Check cumulative budget cap
    projected_spend = round(mandate.currentSpent + req.amount, 4)
    if projected_spend > mandate.totalBudgetLimit:
        elapsed_ms = round((time.perf_counter_ns() - start_ns) / 1_000_000, 3)
        remaining = max(0.0, mandate.totalBudgetLimit - mandate.currentSpent)
        return ValidationResult(
            passed=False,
            status=TxnStatus.BLOCKED_POLICY.value,
            reason=(
                f"Budget exhausted: Requested ${req.amount:.2f}, "
                f"but only ${remaining:.2f} remaining of ${mandate.totalBudgetLimit:.2f} limit."
            ),
            latency_ms=elapsed_ms,
        )

    # 5. Check category whitelist
    allowed_categories = _parse_categories(mandate.allowedCategories)
    req_cat = req.category.strip().lower()
    if allowed_categories and "*" not in allowed_categories and req_cat not in allowed_categories:
        elapsed_ms = round((time.perf_counter_ns() - start_ns) / 1_000_000, 3)
        return ValidationResult(
            passed=False,
            status=TxnStatus.BLOCKED_POLICY.value,
            reason=(
                f"Category '{req.category}' is not in approved whitelist: "
                f"{allowed_categories}."
            ),
            latency_ms=elapsed_ms,
        )

    elapsed_ms = round((time.perf_counter_ns() - start_ns) / 1_000_000, 3)
    return ValidationResult(
        passed=True,
        status=TxnStatus.APPROVED.value,
        reason="All deterministic policy guardrails passed.",
        latency_ms=elapsed_ms,
    )

