"""LedgerMate V2 — FastAPI backend for web dashboard."""
from __future__ import annotations

import os
import subprocess
import sys
from datetime import date, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any

import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from ledgermate.ledger import Ledger
from ledgermate.llm import extract_transaction_json
from ledgermate.validation import validate_transaction
from ledgermate.schema import TransactionType, PaymentMethod

app = FastAPI(title="LedgerMate API", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

STATIC_DIR = Path(__file__).resolve().parents[2] / "static"
if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

@app.get("/")
def serve_index() -> FileResponse:
    index = STATIC_DIR / "index.html"
    if index.exists():
        return FileResponse(index)
    return JSONResponse({"status": "ok", "message": "LedgerMate API running"})

DB_PATH = Path(__file__).resolve().parents[2] / "data" / "ledger.db"


def get_ledger() -> Ledger:
    return Ledger(DB_PATH)


class TransactionInput(BaseModel):
    description: str
    amount: str | None = None
    currency: str = "XAF"
    type: str = "expense"
    category: str = "general"
    payment_method: str = "cash"
    counterparty: str | None = None
    notes: str | None = None
    date: str | None = None


class NaturalLanguageInput(BaseModel):
    text: str


class AssistantQuery(BaseModel):
    question: str


@app.get("/api/health")
def health() -> dict[str, Any]:
    return {"status": "ok", "offline": "true"}


@app.get("/api/dashboard")
def dashboard(period: str = "month") -> dict[str, Any]:
    ledger = get_ledger()
    today = date.today()
    if period == "today":
        start = today
    elif period == "week":
        start = today - timedelta(days=7)
    elif period == "month":
        start = today.replace(day=1)
    elif period == "year":
        start = today.replace(month=1, day=1)
    else:
        start = today.replace(day=1)

    rows = ledger.list_transactions(start_date=start.isoformat(), end_date=today.isoformat())
    
    income = Decimal("0")
    expense = Decimal("0")
    expense_by_category: dict[str, Decimal] = {}
    income_by_category: dict[str, Decimal] = {}
    txn_count = len(rows)
    income_count = 0
    expense_count = 0

    for row in rows:
        amt = Decimal(str(row.get("amount", "0")))
        ttype = row.get("type", "expense")
        cat = row.get("category", "general")
        if ttype == "income":
            income += amt
            income_count += 1
            expense_by_category[cat] = expense_by_category.get(cat, Decimal("0")) + amt
        else:
            expense += amt
            expense_count += 1
            expense_by_category[cat] = expense_by_category.get(cat, Decimal("0")) + amt

    net = income - expense
    top_expense_category = max(expense_by_category, key=expense_by_category.get) if expense_by_category else None
    top_expense_amount = expense_by_category.get(top_expense_category, Decimal("0")) if top_expense_category else Decimal("0")

    return {
        "period": period,
        "start_date": start.isoformat(),
        "end_date": today.isoformat(),
        "income": str(income),
        "expenses": str(expense),
        "profit": str(net),
        "cash": str(income - expense),
        "transaction_count": txn_count,
        "income_count": income_count,
        "expense_count": expense_count,
        "top_expense_category": top_expense_category,
        "top_expense_amount": str(top_expense_amount),
        "expense_by_category": {k: str(v) for k, v in expense_by_category.items()},
        "income_by_category": {k: str(v) for k, v in income_by_category.items()},
    }


@app.get("/api/transactions")
def list_transactions(
    start_date: str | None = None,
    end_date: str | None = None,
    category: str | None = None,
    type: str | None = None,
) -> list[dict]:
    ledger = get_ledger()
    return ledger.list_transactions(
        start_date=start_date,
        end_date=end_date,
        category=category,
        txn_type=type,
    )


@app.post("/api/transactions")
def create_transaction(txn: TransactionInput) -> dict:
    ledger = get_ledger()
    data = txn.model_dump()
    if data.get("date") is None:
        data["date"] = date.today().isoformat()
    if not data.get("transaction_id"):
        data["transaction_id"] = f"txn-{datetime.now().strftime('%Y%m%d%H%M%S%f')}"
    # Map natural language aliases to canonical transaction types.
    _TYPE_ALIASES = {
        'sale': 'income',
        'sell': 'income',
        'income': 'income',
        'expense': 'expense',
        'purchase': 'expense',
        'bought': 'expense',
        'transfer': 'transfer',
        'debt_in': 'debt_in',
        'debt_out': 'debt_out',
    }
    raw_type = str(data.get('type', 'expense')).strip().lower()
    data['type'] = _TYPE_ALIASES.get(raw_type, raw_type)

    try:
        validated = validate_transaction(data)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    try:
        ledger.add_transaction(validated)
    except Exception as exc:
        raise HTTPException(status_code=409, detail=f"Transaction conflict: {exc}") from exc
    return {"status": "ok", "transaction": validated.to_dict()}


@app.post("/api/transactions/nl")
def create_transaction_nl(input_data: NaturalLanguageInput) -> dict:
    ledger = get_ledger()
    try:
        extracted = extract_transaction_json(input_data.text)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"LLM extraction failed: {exc}") from exc
    try:
        validated = validate_transaction(extracted)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Validation failed: {exc}") from exc
    # Map natural language aliases to canonical transaction types before persistence.
    _TYPE_ALIASES = {
        'sale': 'income', 'sell': 'income', 'income': 'income',
        'expense': 'expense', 'purchase': 'expense', 'bought': 'expense',
        'transfer': 'transfer', 'debt_in': 'debt_in', 'debt_out': 'debt_out',
    }
    raw_type = str(validated.type.value if hasattr(validated.type, 'value') else validated.type).strip().lower()
    canonical = _TYPE_ALIASES.get(raw_type, raw_type)
    if canonical != raw_type:
        validated.type = TransactionType(canonical)
    if not validated.transaction_id:
        validated.transaction_id = f"txn-{datetime.now().strftime('%Y%m%d%H%M%S%f')}"
    try:
        ledger.add_transaction(validated)
    except Exception as exc:
        # Retry once with a fresh transaction id in case of accidental duplication
        try:
            validated.transaction_id = f"txn-{datetime.now().strftime('%Y%m%d%H%M%S%f')}"
            ledger.add_transaction(validated)
        except Exception as retry_exc:
            raise HTTPException(status_code=409, detail=f"Transaction conflict: {retry_exc}") from retry_exc
    return {"status": "ok", "proposal": validated.to_dict(), "committed": True}


@app.get("/api/analytics/categories")
def category_analytics(period: str = "month") -> dict[str, Any]:
    ledger = get_ledger()
    today = date.today()
    if period == "month":
        start = today.replace(day=1)
    elif period == "year":
        start = today.replace(month=1, day=1)
    else:
        start = today - timedelta(days=30)
    rows = ledger.list_transactions(start_date=start.isoformat(), end_date=today.isoformat())
    
    expense_by_cat: dict[str, Decimal] = {}
    income_by_cat: dict[str, Decimal] = {}
    for row in rows:
        amt = Decimal(str(row.get("amount", "0")))
        cat = row.get("category", "general")
        if row.get("type") == "income":
            income_by_cat[cat] = income_by_cat.get(cat, Decimal("0")) + amt
        else:
            expense_by_cat[cat] = expense_by_cat.get(cat, Decimal("0")) + amt
    
    return {
        "expense_by_category": {k: str(v) for k, v in sorted(expense_by_cat.items(), key=lambda x: x[1], reverse=True)},
        "income_by_category": {k: str(v) for k, v in sorted(income_by_cat.items(), key=lambda x: x[1], reverse=True)},
    }


@app.get("/api/export/csv")
def export_csv(start_date: str | None = None, end_date: str | None = None) -> FileResponse:
    ledger = get_ledger()
    rows = ledger.list_transactions(start_date=start_date, end_date=end_date)
    if not rows:
        raise HTTPException(status_code=404, detail="No transactions to export")
    from ledgermate.export import export_csv as do_export_csv
    out_path = Path(__file__).resolve().parents[2] / "data" / "exports" / "transactions.csv"
    do_export_csv(rows, out_path)
    return FileResponse(out_path, media_type="text/csv", filename="transactions.csv")


@app.get("/api/export/json")
def export_json(start_date: str | None = None, end_date: str | None = None) -> FileResponse:
    ledger = get_ledger()
    rows = ledger.list_transactions(start_date=start_date, end_date=end_date)
    if not rows:
        raise HTTPException(status_code=404, detail="No transactions to export")
    from ledgermate.export import export_json as do_export_json
    out_path = Path(__file__).resolve().parents[2] / "data" / "exports" / "transactions.json"
    do_export_json(rows, out_path)
    return FileResponse(out_path, media_type="application/json", filename="transactions.json")


@app.post("/api/assistant")
def assistant_query(input_data: AssistantQuery) -> dict[str, Any]:
    ledger = get_ledger()
    q = input_data.question.lower().strip()
    
    # Deterministic routing for financial questions
    if any(word in q for word in ["balance", "how much", "spent", "made", "profit", "income", "expense"]):
        rows = ledger.list_transactions()
        income = sum(Decimal(str(r.get("amount", "0"))) for r in rows if r.get("type") == "income")
        expense = sum(Decimal(str(r.get("amount", "0"))) for r in rows if r.get("type") == "expense")
        profit = income - expense
        answer = f"Your business has {len(rows)} transactions. Income: {income:,.0f} XAF, Expenses: {expense:,.0f} XAF, Net: {profit:,.0f} XAF."
        if profit > 0:
            answer += " You are profitable."
        elif profit < 0:
            answer += " You are operating at a loss."
        else:
            answer += " You are breaking even."
        return {"answer": answer, "type": "analytics", "data": {"income": str(income), "expense": str(expense), "profit": str(profit)}}
    
    if any(word in q for word in ["biggest", "largest", "most", "top", "spend"]):
        rows = ledger.list_transactions()
        expense_by_cat: dict[str, Decimal] = {}
        for r in rows:
            if r.get("type") == "expense":
                amt = Decimal(str(r.get("amount", "0")))
                cat = r.get("category", "general")
                expense_by_cat[cat] = expense_by_cat.get(cat, Decimal("0")) + amt
        if expense_by_cat:
            top = max(expense_by_cat, key=expense_by_cat.get)
            return {"answer": f"Your biggest expense category is {top} at {expense_by_cat[top]:,.0f} XAF.", "type": "analytics", "data": {"top_category": top, "amount": str(expense_by_cat[top])}}
        return {"answer": "No expense data available yet.", "type": "analytics", "data": {}}
    
    if any(word in q for word in ["summary", "how is", "doing", "overview", "recommend"]):
        rows = ledger.list_transactions()
        income = sum(Decimal(str(r.get("amount", "0"))) for r in rows if r.get("type") == "income")
        expense = sum(Decimal(str(r.get("amount", "0"))) for r in rows if r.get("type") == "expense")
        profit = income - expense
        answer = f"Your business recorded {income:,.0f} XAF in income and {expense:,.0f} XAF in expenses, leaving a net of {profit:,.0f} XAF. "
        if len(rows) < 5:
            answer += "Not enough historical data to establish trends. Keep recording transactions for better insights."
        else:
            answer += "Keep tracking your expenses to identify savings opportunities."
        return {"answer": answer, "type": "summary", "data": {"income": str(income), "expense": str(expense), "profit": str(profit)}}
    
    # Default: use LLM for natural language interpretation
    try:
        prompt = f"Answer this business question briefly and clearly for a small business owner: {input_data.question}"
        # Use LLM for open-ended questions
        from ledgermate.llm import run_llama
        answer = run_llama(prompt, max_tokens=256)
        return {"answer": answer.strip(), "type": "ai", "data": {}}
    except Exception as exc:
        return {"answer": f"I couldn't process that question. Try asking about your balance, expenses, or business summary.", "type": "error", "data": {}}


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)


# --- Local modules for invoices, customers, products, trash ---
from ledgermate.ledger import Ledger as _Ledger

def _get_ledger() -> _Ledger:
    return _Ledger(DB_PATH)


@app.get("/api/invoices")
def list_invoices() -> list[dict]:
    ledger = _get_ledger()
    return ledger.list_invoices()


@app.post("/api/invoices")
def create_invoice(payload: dict) -> dict:
    ledger = _get_ledger()
    invoice = ledger.create_invoice(payload)
    return {"status": "ok", "invoice": invoice}


@app.post("/api/invoices/{invoice_id}/mark-paid")
def mark_invoice_paid(invoice_id: str) -> dict:
    ledger = _get_ledger()
    invoice = ledger.mark_invoice_paid(invoice_id)
    return {"status": "ok", "invoice": invoice}


@app.delete("/api/invoices/{invoice_id}")
def delete_invoice(invoice_id: str) -> dict:
    ledger = _get_ledger()
    ledger.delete_invoice(invoice_id)
    return {"status": "ok"}


@app.get("/api/customers")
def list_customers() -> list[dict]:
    ledger = _get_ledger()
    return ledger.list_customers()


@app.post("/api/customers")
def create_customer(payload: dict) -> dict:
    ledger = _get_ledger()
    customer = ledger.create_customer(payload)
    return {"status": "ok", "customer": customer}


@app.delete("/api/customers/{customer_id}")
def delete_customer(customer_id: str) -> dict:
    ledger = _get_ledger()
    ledger.delete_customer(customer_id)
    return {"status": "ok"}


@app.get("/api/products")
def list_products() -> list[dict]:
    ledger = _get_ledger()
    return ledger.list_products()


@app.post("/api/products")
def create_product(payload: dict) -> dict:
    ledger = _get_ledger()
    product = ledger.create_product(payload)
    return {"status": "ok", "product": product}


@app.delete("/api/products/{product_id}")
def delete_product(product_id: str) -> dict:
    ledger = _get_ledger()
    ledger.delete_product(product_id)
    return {"status": "ok"}


@app.get("/api/trash")
def list_trash() -> list[dict]:
    ledger = _get_ledger()
    return ledger.list_trash()


@app.post("/api/trash/{item_id}/restore")
def restore_trash(item_id: str) -> dict:
    ledger = _get_ledger()
    ledger.restore_trash(item_id)
    return {"status": "ok"}


@app.delete("/api/trash/{item_id}")
def permanent_delete_trash(item_id: str) -> dict:
    ledger = _get_ledger()
    ledger.permanent_delete_trash(item_id)
    return {"status": "ok"}
