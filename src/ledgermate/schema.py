"""LedgerMate data models."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import Optional


class TransactionType(str, Enum):
    INCOME = "income"
    EXPENSE = "expense"
    TRANSFER = "transfer"
    DEBT_IN = "debt_in"
    DEBT_OUT = "debt_out"


class PaymentMethod(str, Enum):
    CASH = "cash"
    MOBILE_MONEY = "mobile_money"
    BANK = "bank"
    CREDIT = "credit"
    OTHER = "other"


@dataclass
class Transaction:
    transaction_id: str
    date: date
    description: str
    category: str
    type: TransactionType
    amount: Decimal
    currency: str = "XAF"
    payment_method: Optional[PaymentMethod] = None
    counterparty: Optional[str] = None
    notes: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    source: str = "manual"

    @classmethod
    def from_dict(cls, data: dict) -> "Transaction":
        """Create transaction from dictionary."""
        raw_type = data["type"]
        if isinstance(raw_type, TransactionType):
            txn_type = raw_type
        else:
            txn_type = TransactionType(raw_type)
        raw_pm = data.get("payment_method")
        if isinstance(raw_pm, PaymentMethod):
            pm = raw_pm
        elif raw_pm is not None:
            pm = PaymentMethod(raw_pm)
        else:
            pm = PaymentMethod.CASH
        raw_date = data["date"]
        if isinstance(raw_date, str):
            parsed_date = date.fromisoformat(raw_date)
        else:
            parsed_date = raw_date
        raw_amount = data["amount"]
        if isinstance(raw_amount, Decimal):
            amount = raw_amount
        elif isinstance(raw_amount, str):
            amount = Decimal(raw_amount)
        else:
            amount = Decimal(str(raw_amount))
        return cls(
            transaction_id=data["transaction_id"],
            date=parsed_date,
            description=data["description"],
            category=data["category"],
            type=txn_type,
            amount=amount,
            currency=data.get("currency", "XAF"),
            payment_method=pm,
            counterparty=data.get("counterparty", ""),
            notes=data.get("notes"),
        )

    def to_dict(self) -> dict:
        """Convert transaction to dictionary."""
        return {
            "transaction_id": self.transaction_id,
            "date": self.date.isoformat(),
            "description": self.description,
            "category": self.category,
            "type": self.type.value,
            "amount": str(self.amount),
            "currency": self.currency,
            "payment_method": self.payment_method.value if isinstance(self.payment_method, PaymentMethod) else self.payment_method,
            "counterparty": self.counterparty,
            "notes": self.notes or "",
            "created_at": self.created_at.isoformat(),
        }
