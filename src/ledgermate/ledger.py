"""Append-only ledger persistence with SQLite."""
from __future__ import annotations

import json
import sqlite3
from datetime import date, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Iterable, Optional

from ledgermate.schema import Transaction


class Ledger:
    def __init__(self, db_path: str | Path = "ledger.db") -> None:
        self.db_path = Path(db_path)
        self._ensure_schema()
        self._init_extended_schema()

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

    def _init_extended_schema(self) -> None:
        conn = self._connect()
        try:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS invoices (
                  invoice_id TEXT PRIMARY KEY,
                  customer_id TEXT,
                  customer_name TEXT,
                  items TEXT NOT NULL,
                  subtotal TEXT NOT NULL,
                  tax TEXT NOT NULL DEFAULT '0',
                  discount TEXT NOT NULL DEFAULT '0',
                  total TEXT NOT NULL,
                  currency TEXT NOT NULL DEFAULT 'XAF',
                  status TEXT NOT NULL DEFAULT 'draft',
                  invoice_date TEXT NOT NULL,
                  due_date TEXT,
                  notes TEXT,
                  created_at TEXT NOT NULL DEFAULT (datetime('now'))
                );
                CREATE TABLE IF NOT EXISTS customers (
                  customer_id TEXT PRIMARY KEY,
                  name TEXT NOT NULL,
                  company TEXT,
                  email TEXT,
                  phone TEXT,
                  address TEXT,
                  notes TEXT,
                  created_at TEXT NOT NULL DEFAULT (datetime('now'))
                );
                CREATE TABLE IF NOT EXISTS products (
                  product_id TEXT PRIMARY KEY,
                  name TEXT NOT NULL,
                  sku TEXT,
                  description TEXT,
                  category TEXT,
                  purchase_price TEXT NOT NULL DEFAULT '0',
                  selling_price TEXT NOT NULL DEFAULT '0',
                  unit TEXT,
                  tax TEXT NOT NULL DEFAULT '0',
                  stock_quantity INTEGER NOT NULL DEFAULT 0,
                  created_at TEXT NOT NULL DEFAULT (datetime('now'))
                );
                CREATE TABLE IF NOT EXISTS trash (
                  item_id TEXT PRIMARY KEY,
                  collection TEXT NOT NULL,
                  payload TEXT NOT NULL,
                  deleted_at TEXT NOT NULL DEFAULT (datetime('now'))
                );
                """
            )
            conn.commit()
        finally:
            conn.close()

    def soft_delete_transaction(self, transaction_id: str) -> None:
        self._init_extended_schema()
        conn = self._connect()
        try:
            row = conn.execute("SELECT * FROM transactions WHERE transaction_id = ?", (transaction_id,)).fetchone()
            if row:
                payload = json.dumps(dict(row))
                conn.execute(
                    "INSERT OR REPLACE INTO trash (item_id, collection, payload) VALUES (?, ?, ?)",
                    (transaction_id, "transactions", payload),
                )
                conn.execute("DELETE FROM transactions WHERE transaction_id = ?", (transaction_id,))
                conn.commit()
        finally:
            conn.close()

    def list_invoices(self) -> list[dict]:
        conn = self._connect()
        try:
            rows = conn.execute("SELECT * FROM invoices ORDER BY invoice_date ASC").fetchall()
            result = []
            for row in rows:
                item = dict(row)
                raw_items = item.get("items")
                if isinstance(raw_items, str):
                    try:
                        item["items"] = json.loads(raw_items)
                    except Exception:
                        item["items"] = []
                elif raw_items is None:
                    item["items"] = []
                result.append(item)
            return result
        finally:
            conn.close()

    def create_invoice(self, payload: dict) -> dict:
        self._init_extended_schema()
        invoice_id = payload.get("invoice_id") or f"inv-{datetime.now().strftime('%Y%m%d%H%M%S%f')}"
        conn = self._connect()
        try:
            conn.execute(
                """
                INSERT INTO invoices (invoice_id, customer_id, customer_name, items, subtotal, tax, discount, total, currency, status, invoice_date, due_date, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    invoice_id,
                    payload.get("customer_id"),
                    payload.get("customer_name"),
                    json.dumps(payload.get("items", [])),
                    str(payload.get("subtotal", "0")),
                    str(payload.get("tax", "0")),
                    str(payload.get("discount", "0")),
                    str(payload.get("total", "0")),
                    payload.get("currency", "XAF"),
                    payload.get("status", "draft"),
                    payload.get("invoice_date", date.today().isoformat()),
                    payload.get("due_date"),
                    payload.get("notes"),
                ),
            )
            conn.commit()
        finally:
            conn.close()
        return {"invoice_id": invoice_id, **payload}

    def mark_invoice_paid(self, invoice_id: str) -> dict:
        conn = self._connect()
        try:
            conn.execute("UPDATE invoices SET status = 'paid' WHERE invoice_id = ?", (invoice_id,))
            conn.commit()
            row = conn.execute("SELECT * FROM invoices WHERE invoice_id = ?", (invoice_id,)).fetchone()
            return dict(row) if row else {}
        finally:
            conn.close()

    def soft_delete_invoice(self, invoice_id: str) -> None:
        self._init_extended_schema()
        conn = self._connect()
        try:
            row = conn.execute("SELECT * FROM invoices WHERE invoice_id = ?", (invoice_id,)).fetchone()
            if row:
                payload = json.dumps(dict(row))
                conn.execute(
                    "INSERT OR REPLACE INTO trash (item_id, collection, payload) VALUES (?, ?, ?)",
                    (invoice_id, "invoices", payload),
                )
                conn.execute("DELETE FROM invoices WHERE invoice_id = ?", (invoice_id,))
                conn.commit()
        finally:
            conn.close()

    def list_customers(self) -> list[dict]:
        self._init_extended_schema()
        conn = self._connect()
        try:
            rows = conn.execute("SELECT * FROM customers ORDER BY name ASC").fetchall()
            return [dict(row) for row in rows]
        finally:
            conn.close()

    def create_customer(self, payload: dict) -> dict:
        self._init_extended_schema()
        customer_id = payload.get("customer_id") or f"cust-{datetime.now().strftime('%Y%m%d%H%M%S%f')}"
        conn = self._connect()
        try:
            conn.execute(
                "INSERT INTO customers (customer_id, name, company, email, phone, address, notes) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (
                    customer_id,
                    payload.get("name"),
                    payload.get("company"),
                    payload.get("email"),
                    payload.get("phone"),
                    payload.get("address"),
                    payload.get("notes"),
                ),
            )
            conn.commit()
        finally:
            conn.close()
        return {"customer_id": customer_id, **payload}

    def soft_delete_customer(self, customer_id: str) -> None:
        self._init_extended_schema()
        conn = self._connect()
        try:
            row = conn.execute("SELECT * FROM customers WHERE customer_id = ?", (customer_id,)).fetchone()
            if row:
                payload = json.dumps(dict(row))
                conn.execute(
                    "INSERT OR REPLACE INTO trash (item_id, collection, payload) VALUES (?, ?, ?)",
                    (customer_id, "customers", payload),
                )
                conn.execute("DELETE FROM customers WHERE customer_id = ?", (customer_id,))
                conn.commit()
        finally:
            conn.close()

    def soft_delete_product(self, product_id: str) -> None:
        self._init_extended_schema()
        conn = self._connect()
        try:
            row = conn.execute("SELECT * FROM products WHERE product_id = ?", (product_id,)).fetchone()
            if row:
                payload = json.dumps(dict(row))
                conn.execute(
                    "INSERT OR REPLACE INTO trash (item_id, collection, payload) VALUES (?, ?, ?)",
                    (product_id, "products", payload),
                )
                conn.execute("DELETE FROM products WHERE product_id = ?", (product_id,))
                conn.commit()
        finally:
            conn.close()

    def list_products(self) -> list[dict]:
        self._init_extended_schema()
        conn = self._connect()
        try:
            rows = conn.execute("SELECT * FROM products ORDER BY name ASC").fetchall()
            return [dict(row) for row in rows]
        finally:
            conn.close()

    def create_product(self, payload: dict) -> dict:
        self._init_extended_schema()
        product_id = payload.get("product_id") or f"prod-{datetime.now().strftime('%Y%m%d%H%M%S%f')}"
        conn = self._connect()
        try:
            conn.execute(
                "INSERT INTO products (product_id, name, sku, description, category, purchase_price, selling_price, unit, tax, stock_quantity) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    product_id,
                    payload.get("name"),
                    payload.get("sku"),
                    payload.get("description"),
                    payload.get("category"),
                    str(payload.get("purchase_price", "0")),
                    str(payload.get("selling_price", "0")),
                    payload.get("unit"),
                    str(payload.get("tax", "0")),
                    int(payload.get("stock_quantity", 0)),
                ),
            )
            conn.commit()
        finally:
            conn.close()
        return {"product_id": product_id, **payload}

    def soft_delete_product(self, product_id: str) -> None:
        self._init_extended_schema()
        conn = self._connect()
        try:
            row = conn.execute("SELECT * FROM products WHERE product_id = ?", (product_id,)).fetchone()
            if row:
                payload = json.dumps(dict(row))
                conn.execute(
                    "INSERT OR REPLACE INTO trash (item_id, collection, payload) VALUES (?, ?, ?)",
                    (product_id, "products", payload),
                )
                conn.execute("DELETE FROM products WHERE product_id = ?", (product_id,))
                conn.commit()
        finally:
            conn.close()

    def list_trash(self) -> list[dict]:
        self._init_extended_schema()
        conn = self._connect()
        try:
            rows = conn.execute("SELECT * FROM trash ORDER BY deleted_at DESC").fetchall()
            return [dict(row) for row in rows]
        finally:
            conn.close()

    def restore_trash(self, item_id: str) -> None:
        conn = self._connect()
        try:
            row = conn.execute("SELECT * FROM trash WHERE item_id = ?", (item_id,)).fetchone()
            if not row:
                return
            payload = json.loads(row["payload"])
            collection = row["collection"]
            if collection == "transactions":
                from ledgermate.validation import validate_transaction
                validated = validate_transaction(payload)
                conn.execute(
                    """
                    INSERT INTO transactions (transaction_id, date, description, category, type, amount, currency, payment_method, counterparty, notes, created_at, source)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        validated.transaction_id,
                        validated.date.isoformat(),
                        validated.description,
                        validated.category,
                        validated.type.value,
                        str(validated.amount),
                        validated.currency,
                        validated.payment_method.value if isinstance(validated.payment_method, PaymentMethod) else validated.payment_method,
                        validated.counterparty,
                        validated.notes,
                        datetime.now().isoformat(),
                        validated.source,
                    ),
                )
            elif collection == "invoices":
                payload.pop("created_at", None)
                conn.execute(
                    """
                    INSERT INTO invoices (invoice_id, customer_id, customer_name, items, subtotal, tax, discount, total, currency, status, invoice_date, due_date, notes)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        payload.get("invoice_id"),
                        payload.get("customer_id"),
                        payload.get("customer_name"),
                        json.dumps(payload.get("items", [])),
                        str(payload.get("subtotal", "0")),
                        str(payload.get("tax", "0")),
                        str(payload.get("discount", "0")),
                        str(payload.get("total", "0")),
                        payload.get("currency", "XAF"),
                        payload.get("status", "draft"),
                        payload.get("invoice_date"),
                        payload.get("due_date"),
                        payload.get("notes"),
                    ),
                )
            elif collection == "customers":
                conn.execute(
                    "INSERT INTO customers (customer_id, name, company, email, phone, address, notes) VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (
                        payload.get("customer_id"),
                        payload.get("name"),
                        payload.get("company"),
                        payload.get("email"),
                        payload.get("phone"),
                        payload.get("address"),
                        payload.get("notes"),
                    ),
                )
            elif collection == "products":
                conn.execute(
                    "INSERT INTO products (product_id, name, sku, description, category, purchase_price, selling_price, unit, tax, stock_quantity) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (
                        payload.get("product_id"),
                        payload.get("name"),
                        payload.get("sku"),
                        payload.get("description"),
                        payload.get("category"),
                        str(payload.get("purchase_price", "0")),
                        str(payload.get("selling_price", "0")),
                        payload.get("unit"),
                        str(payload.get("tax", "0")),
                        int(payload.get("stock_quantity", 0)),
                    ),
                )
            conn.execute("DELETE FROM trash WHERE item_id = ?", (item_id,))
            conn.commit()
        finally:
            conn.close()

    def permanent_delete_trash(self, item_id: str) -> None:
        conn = self._connect()
        try:
            conn.execute("DELETE FROM trash WHERE item_id = ?", (item_id,))
            conn.commit()
        finally:
            conn.close()
