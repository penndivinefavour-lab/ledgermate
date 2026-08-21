"""Append-only ledger persistence with SQLite."""
from __future__ import annotations

import json
import sqlite3
from decimal import Decimal
from pathlib import Path
from typing import Iterable, Optional

from ledgermate.schema import Transaction


class Ledger:
    def __init__(self, db_path: str | Path = "ledger.db") -> None:
        self.db_path = Path(db_path)
        self._ensure_schema()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _ensure_schema(self) -> None:
        conn = self._connect()
        try:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS transactions (
                  transaction_id TEXT PRIMARY KEY,
                  date TEXT NOT NULL,
                  description TEXT NOT NULL,
                  category TEXT NOT NULL,
                  type TEXT NOT NULL,
                  amount TEXT NOT NULL,
                  currency TEXT NOT NULL DEFAULT 'XAF',
                  payment_method TEXT,
                  counterparty TEXT,
                  notes TEXT,
                  created_at TEXT NOT NULL,
                  source TEXT NOT NULL DEFAULT 'manual'
                );
                CREATE TABLE IF NOT EXISTS audit_log (
                  id INTEGER PRIMARY KEY AUTOINCREMENT,
                  action TEXT NOT NULL,
                  transaction_id TEXT,
                  created_at TEXT NOT NULL DEFAULT (datetime('now')),
                  details TEXT
                );
                CREATE INDEX IF NOT EXISTS idx_transactions_date ON transactions(date);
                CREATE INDEX IF NOT EXISTS idx_transactions_category ON transactions(category);
                """
            )
            conn.commit()
        finally:
            conn.close()

    def add_transaction(self, transaction: Transaction) -> None:
        conn = self._connect()
        try:
            conn.execute(
                """
                INSERT INTO transactions (
                  transaction_id, date, description, category, type, amount,
                  currency, payment_method, counterparty, notes, created_at, source
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    transaction.transaction_id,
                    transaction.date.isoformat(),
                    transaction.description,
                    transaction.category,
                    transaction.type.value,
                    str(transaction.amount),
                    transaction.currency,
                    transaction.payment_method.value if transaction.payment_method else None,
                    transaction.counterparty,
                    transaction.notes,
                    transaction.created_at.isoformat(),
                    transaction.source,
                ),
            )
            conn.execute(
                "INSERT INTO audit_log (action, transaction_id, details) VALUES (?, ?, ?)",
                ("insert", transaction.transaction_id, json.dumps(transaction.to_dict())),
            )
            conn.commit()
        finally:
            conn.close()

    def list_transactions(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        category: Optional[str] = None,
        txn_type: Optional[str] = None,
    ) -> list[dict]:
        query = "SELECT * FROM transactions WHERE 1=1"
        params: list = []
        if start_date:
            query += " AND date >= ?"
            params.append(start_date)
        if end_date:
            query += " AND date <= ?"
            params.append(end_date)
        if category:
            query += " AND category = ?"
            params.append(category)
        if txn_type:
            query += " AND type = ?"
            params.append(txn_type)
        query += " ORDER BY date ASC"
        conn = self._connect()
        try:
            rows = conn.execute(query, params).fetchall()
            return [dict(row) for row in rows]
        finally:
            conn.close()

    def balance(self) -> dict:
        conn = self._connect()
        try:
            income = conn.execute(
                "SELECT COALESCE(SUM(CAST(amount AS DECIMAL)), 0) FROM transactions WHERE type = ?",
                ("income",),
            ).fetchone()[0]
            expense = conn.execute(
                "SELECT COALESCE(SUM(CAST(amount AS DECIMAL)), 0) FROM transactions WHERE type = ?",
                ("expense",),
            ).fetchone()[0]
        finally:
            conn.close()
        return {
            "income": str(income),
            "expense": str(expense),
            "net": str(Decimal(str(income)) - Decimal(str(expense))),
            "currency": "XAF",
        }
