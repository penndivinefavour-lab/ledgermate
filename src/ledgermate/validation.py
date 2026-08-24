"""Deterministic validation layer for LedgerMate transactions."""
from __future__ import annotations

import re
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from typing import Optional

from ledgermate.schema import PaymentMethod, Transaction, TransactionType


class ValidationError(Exception):
    pass


def validate_transaction(data: dict) -> Transaction:
    """Validate extracted transaction data and return a Transaction."""
    required_fields = ["date", "description", "category", "type", "amount"]
    missing = [field for field in required_fields if not data.get(field)]
    if missing:
        raise ValidationError(f"Missing required fields: {missing}")

    # Parse date
    raw_date = str(data.get("date", "")).strip()
    try:
        parsed_date = datetime.strptime(raw_date, "%Y-%m-%d").date()
    except ValueError:
        try:
            parsed_date = datetime.strptime(raw_date, "%d/%m/%Y").date()
        except ValueError:
            raise ValidationError(f"Unparseable date: {raw_date!r}")

    # Future date guard: allow small forward window for timezone drift
    today = date.today()
    if parsed_date > today:
        raise ValidationError(f"Future date not allowed: {parsed_date}")

    # Type
    raw_type = str(data.get("type", "")).strip().lower()
    _TYPE_ALIASES = {
        "sale": "income",
        "sell": "income",
        "income": "income",
        "expense": "expense",
        "purchase": "expense",
        "bought": "expense",
        "transfer": "transfer",
        "debt_in": "debt_in",
        "debt_out": "debt_out",
    }
    canonical_type = _TYPE_ALIASES.get(raw_type, raw_type)
    try:
        txn_type = TransactionType(canonical_type)
    except ValueError:
        raise ValidationError(f"Unknown transaction type: {raw_type}")

    # Amount
    raw_amount = str(data.get("amount", "")).strip()
    try:
        amount = Decimal(raw_amount)
    except InvalidOperation:
        raise ValidationError(f"Invalid amount: {raw_amount}")

    if amount <= Decimal("0"):
        raise ValidationError("Amount must be positive")

    # Currency
    currency = str(data.get("currency", "XAF")).strip().upper()
    if currency not in {"XAF", "USD", "EUR", "GBP", "NGN", "GHS", "KES"}:
        raise ValidationError(f"Unsupported currency: {currency}")

    # Payment method
    raw_pm = str(data.get("payment_method", "")).strip().lower()
    payment_method: Optional[PaymentMethod] = None
    if raw_pm:
        try:
            payment_method = PaymentMethod(raw_pm)
        except ValueError:
            payment_method = PaymentMethod.OTHER

    # Description/category length
    description = str(data.get("description", "")).strip()
    category = str(data.get("category", "")).strip()
    if len(description) < 2:
        raise ValidationError("Description too short")
    if len(category) < 2:
        raise ValidationError("Category too short")

    # Transaction ID
    txn_id = str(data.get("transaction_id", "")).strip()
    if not re.fullmatch(r"[A-Za-z0-9\-_]{3,64}", txn_id):
        raise ValidationError(f"Invalid transaction_id format: {txn_id}")

    return Transaction(
        transaction_id=txn_id,
        date=parsed_date,
        description=description,
        category=category,
        type=txn_type,
        amount=amount,
        currency=currency,
        payment_method=payment_method,
        counterparty=str(data.get("counterparty", "")).strip() or None,
        notes=str(data.get("notes", "")).strip() or None,
        source=str(data.get("source", "manual")).strip(),
    )
