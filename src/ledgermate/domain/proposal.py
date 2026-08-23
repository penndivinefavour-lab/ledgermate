"""LedgerMate V2 — transaction proposal model."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Optional


@dataclass
class TransactionProposal:
    transaction_type: str
    amount: str
    currency: str
    date: str
    description: str
    category: str
    counterparty: Optional[str] = None
    payment_method: Optional[str] = None
    notes: Optional[str] = None

    def confirmed_dict(self) -> dict:
        return {
            "transaction_id": f"txn-{abs(hash((self.date, self.description, self.amount))) & 0xffffffff:08x}",
            "date": self.date,
            "description": self.description,
            "category": self.category,
            "type": self.transaction_type,
            "amount": self.amount,
            "currency": self.currency,
            "payment_method": self.payment_method or "cash",
            "counterparty": self.counterparty or "",
            "notes": self.notes or "",
            "source": "voice",
        }
