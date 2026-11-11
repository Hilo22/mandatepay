import re
from collections import defaultdict
from typing import Any, Dict, List, Optional, Tuple
from app.models.schemas import NettingItem, NettingSummaryResponse


class NettingLedgerManager:
    """
    Off-Chain Multilateral / Bilateral Netting Engine.
    Maintains approved micro-transactions and computes net settlement obligations:
        NetBalance(Email_A) = Sum(Receivables(Email_A)) - Sum(Payables(Email_A))
    Only net creditors (positive balance) receive a single consolidated PayPal Payout item.
    """

    def __init__(self) -> None:
        self._records: List[Dict[str, Any]] = []

    def add_transaction(
        self,
        transaction_id: str,
        buyer_email: str,
        seller_email: str,
        amount: float,
        seller_agent_id: str = "SELLER_AGENT",
        buyer_agent_id: str = "BUYER_AGENT",
    ) -> None:
        self._records.append(
            {
                "id": transaction_id,
                "buyer_email": buyer_email.strip().lower(),
                "seller_email": seller_email.strip().lower(),
                "amount": float(amount),
                "seller_agent_id": seller_agent_id,
                "buyer_agent_id": buyer_agent_id,
            }
        )

    def clear(self) -> None:
        self._records.clear()

    @staticmethod
    def compute_from_records(
        records: List[Dict[str, Any]],
        mandate_id: Optional[str] = None,
    ) -> Tuple[List[NettingItem], NettingSummaryResponse]:
        """
        Given a list of approved transaction dicts containing:
        - `buyer_email` (or mandate owner email)
        - `seller_email`
        - `amount`
        - `seller_agent_id`
        Computes the bilateral/multilateral net balances across all participant emails.
        """
        net_balances: Dict[str, float] = defaultdict(float)
        credit_task_counts: Dict[str, int] = defaultdict(int)
        agent_labels: Dict[str, str] = {}
        gross_volume = 0.0

        for rec in records:
            amount = float(rec.get("amount", 0.0))
            if amount <= 0:
                continue
            buyer = str(rec.get("buyer_email", "platform_vault@mandatepay.io")).strip().lower()
            seller = str(rec.get("seller_email", "")).strip().lower()
            seller_agent_id = str(rec.get("seller_agent_id", "AGENT")).upper()

            gross_volume += amount
            net_balances[buyer] -= amount
            net_balances[seller] += amount
            credit_task_counts[seller] += 1
            if seller not in agent_labels:
                clean_id = re.sub(r"[^A-Z0-9_]", "_", seller_agent_id)
                agent_labels[seller] = clean_id

        payout_items: List[NettingItem] = []
        total_net_payout = 0.0

        for email, balance in sorted(net_balances.items(), key=lambda x: (-x[1], x[0])):
            rounded_balance = round(balance, 2)
            if rounded_balance > 0.0:
                total_net_payout += rounded_balance
                task_count = credit_task_counts.get(email, 1)
                agent_tag = agent_labels.get(email, email.split("@")[0].upper())
                payout_items.append(
                    NettingItem(
                        recipient_type="EMAIL",
                        amount={
                            "value": f"{rounded_balance:.2f}",
                            "currency": "USD",
                        },
                        note=f"Net payout for {task_count} verified micro-tasks",
                        sender_item_id=f"ITEM_{agent_tag}",
                        receiver=email,
                        task_count=task_count,
                    )
                )

        raw_count = len(records)
        consolidated_count = len(payout_items)
        fee_savings_pct = (
            round(((raw_count - consolidated_count) / raw_count) * 100.0, 1)
            if raw_count > 0 and raw_count >= consolidated_count
            else 0.0
        )

        summary = NettingSummaryResponse(
            mandate_id=mandate_id,
            total_gross_volume=round(gross_volume, 2),
            total_net_payout=round(total_net_payout, 2),
            raw_transaction_count=raw_count,
            consolidated_payout_count=consolidated_count,
            fee_savings_pct=fee_savings_pct,
            payout_items=payout_items,
        )
        return payout_items, summary

    def calculate_netting(
        self, mandate_id: Optional[str] = None
    ) -> Tuple[List[Dict[str, Any]], NettingSummaryResponse]:
        items, summary = self.compute_from_records(self._records, mandate_id=mandate_id)
        paypal_ready_items = [
            {
                "recipient_type": item.recipient_type,
                "amount": item.amount,
                "note": item.note,
                "sender_item_id": item.sender_item_id,
                "receiver": item.receiver,
            }
            for item in items
        ]
        return paypal_ready_items, summary

