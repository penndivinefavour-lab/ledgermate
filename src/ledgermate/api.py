"""LedgerMate V2 — FastAPI backend for web dashboard."""
from __future__ import annotations

import json
import os
import re
import socket
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

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from ledgermate.ledger import Ledger
from ledgermate.llm import extract_transaction_json, run_llama
from ledgermate.validation import validate_transaction
from ledgermate.schema import TransactionType, PaymentMethod
from ledgermate.services import settings

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

DB_PATH = Path(__file__).resolve().parents[2] / "data" / "ledger.db"


def get_ledger() -> Ledger:
    return Ledger(DB_PATH)


class TransactionInput(BaseModel):
    description: str
    amount: str | None = None
    currency: str | None = None
    type: str = "expense"
    category: str = "general"
    payment_method: str = "cash"
    counterparty: str | None = None
    notes: str | None = None
    date: str | None = None


class NaturalLanguageInput(BaseModel):
    text: str
    amount: str | None = None


class AssistantQuery(BaseModel):
    question: str


@app.get("/api/health")
def health() -> dict[str, Any]:
    return {"status": "ok", "offline": "true"}


@app.get("/api/settings")
def get_settings() -> dict[str, Any]:
    return {
        "profile": settings.profile.to_dict(),
        "financial": settings.financial.to_dict(),
        "date_time": settings.date_time.to_dict(),
        "language": settings.language,
    }


@app.post("/api/settings")
def save_settings(payload: dict[str, Any]) -> dict[str, Any]:
    if "profile" in payload:
        settings.profile = settings.profile.__class__(**{k: payload["profile"].get(k, getattr(settings.profile, k)) for k in settings.profile.__dataclass_fields__})
    if "financial" in payload:
        settings.financial = settings.financial.__class__(**{k: payload["financial"].get(k, getattr(settings.financial, k)) for k in settings.financial.__dataclass_fields__})
    if "date_time" in payload:
        settings.date_time = settings.date_time.__class__(**{k: payload["date_time"].get(k, getattr(settings.date_time, k)) for k in settings.date_time.__dataclass_fields__})
    if "language" in payload:
        settings.language = str(payload["language"])
    settings.save()
    return {"status": "ok"}


@app.get("/api/dashboard")
def dashboard(period: str = "month") -> dict[str, Any]:
    ledger = get_ledger()
    today = settings.current_date()
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
            income_by_category[cat] = income_by_category.get(cat, Decimal("0")) + amt
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


def _normalize_transaction_type(raw_type: str) -> str:
    canonical = {
        'sale': 'income', 'sell': 'income', 'income': 'income',
        'expense': 'expense', 'purchase': 'expense', 'bought': 'expense',
        'transfer': 'transfer', 'debt_in': 'debt_in', 'debt_out': 'debt_out',
    }
    return canonical.get(raw_type.strip().lower(), raw_type)


def _extract_amount_from_text(text: str) -> Decimal:
    for_pattern = r"for\s+(\d[\d,]*\.?\d*)"
    for_matches = [m.replace(",", "") for m in re.findall(for_pattern, text, re.IGNORECASE)]
    all_numbers = [Decimal(m.replace(",", "")) for m in re.findall(r"(\d[\d,]*\.?\d*)", text)]
    if not all_numbers:
        return Decimal("0")
    if for_matches:
        total = Decimal("0")
        for num_str in for_matches:
            total += Decimal(num_str)
        return total
    return all_numbers[-1]


@app.post("/api/transactions")
def create_transaction(txn: TransactionInput) -> dict:
    ledger = get_ledger()
    data = txn.model_dump()
    if not data.get("date"):
        data["date"] = settings.current_date().isoformat()
    if not data.get("transaction_id"):
        data["transaction_id"] = f"txn-{datetime.now().strftime('%Y%m%d%H%M%S%f')}"
    if not data.get("currency"):
        data["currency"] = settings.current_currency()
    data["type"] = _normalize_transaction_type(str(data.get("type", "expense")))

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

    # Always use the current device/application date unless the user explicitly mentioned a historical date
    today = settings.current_date()
    if not extracted.get("date") or extracted.get("date", "").startswith(("2020", "2021", "2022", "2023", "2024")):
        extracted["date"] = today.isoformat()

    computed_total = _extract_amount_from_text(input_data.text)
    if computed_total > 0:
        extracted["amount"] = str(int(computed_total))

    if not extracted.get("currency"):
        extracted["currency"] = settings.current_currency()
    if not extracted.get("date"):
        extracted["date"] = today.isoformat()
    extracted["type"] = _normalize_transaction_type(str(extracted.get("type", "expense")))
    if not extracted.get("category"):
        extracted["category"] = "general"

    raw_nl = re.sub(r"\s+", " ", input_data.text).strip()
    raw_with_amount = raw_nl + (f" {input_data.amount}" if input_data.amount else "")
    nl_id = re.sub(r"[^a-zA-Z0-9]+", "-", raw_with_amount).strip("-").lower() or f"nl-{datetime.now().strftime('%Y%m%d%H%M%S%f')}"
    suffix = datetime.now().strftime('%Y%m%d%H%M%S%f')
    extracted["transaction_id"] = f"{nl_id[:48]}_{suffix}"[:64]

    # Clean up description from LLM artifacts
    description = str(extracted.get("description", "")).strip()
    description = re.sub(r"\s+", " ", description)
    description = description.replace("Buyed ", "Bought ").replace("buyed ", "bought ")
    extracted["description"] = description[:120]

    # Clarification support when user did not provide any amount in raw text
    if not input_data.amount and not re.search(r"\d", input_data.text):
        return JSONResponse({"needs_clarification": True, "clarification_prompt": "What was the amount?", "proposal": { "description": extracted.get("description", ""), "type": extracted.get("type", "expense"), "currency": extracted.get("currency", settings.current_currency()), "date": extracted.get("date", today.isoformat()) } })

    if input_data.amount:
        extracted["amount"] = str(int(Decimal(str(input_data.amount).replace(",", ""))))

    try:
        validated = validate_transaction(extracted)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Validation failed: {exc}") from exc

    if not getattr(validated, "transaction_id", None):
        validated.transaction_id = f"txn-{datetime.now().strftime('%Y%m%d%H%M%S%f')}"

    try:
        ledger.add_transaction(validated)
    except Exception as exc:
        raise HTTPException(status_code=409, detail=f"Transaction conflict: {exc}") from exc

    return {"status": "ok", "proposal": validated.to_dict(), "committed": True}


@app.get("/api/analytics/categories")
def category_analytics(period: str = "month") -> dict[str, Any]:
    ledger = get_ledger()
    today = settings.current_date()
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
    
    if any(word in q for word in ["balance", "how much", "spent", "made", "profit", "income", "expense"]):
        rows = ledger.list_transactions()
        income = sum(Decimal(str(r.get("amount", "0"))) for r in rows if r.get("type") == "income")
        expense = sum(Decimal(str(r.get("amount", "0"))) for r in rows if r.get("type") == "expense")
        profit = income - expense
        answer = f"Your business has {len(rows)} transactions. Income: {income:,.0f} {settings.current_currency()}, Expenses: {expense:,.0f} {settings.current_currency()}, Net: {profit:,.0f} {settings.current_currency()}."
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
            return {"answer": f"Your biggest expense category is {top} at {expense_by_cat[top]:,.0f} {settings.current_currency()}.", "type": "analytics", "data": {"top_category": top, "amount": str(expense_by_cat[top])}}
        return {"answer": "No expense data available yet.", "type": "analytics", "data": {}}
    
    if any(word in q for word in ["summary", "how is", "doing", "overview", "recommend"]):
        rows = ledger.list_transactions()
        income = sum(Decimal(str(r.get("amount", "0"))) for r in rows if r.get("type") == "income")
        expense = sum(Decimal(str(r.get("amount", "0"))) for r in rows if r.get("type") == "expense")
        profit = income - expense
        answer = f"Your business recorded {income:,.0f} {settings.current_currency()} in income and {expense:,.0f} {settings.current_currency()} in expenses, leaving a net of {profit:,.0f} {settings.current_currency()}. "
        if len(rows) < 5:
            answer += "Not enough historical data to establish trends. Keep recording transactions for better insights."
        else:
            answer += "Keep tracking your expenses to identify savings opportunities."
        return {"answer": answer, "type": "summary", "data": {"income": str(income), "expense": str(expense), "profit": str(profit)}}

    if "business name" in q or "my name" in q:
        name = settings.profile.business_name or settings.profile.owner_name
        if name:
            return {"answer": f"Your configured business name is: {name}", "type": "business_context", "data": {"business_name": name}}
        return {"answer": "I don't have your business name yet. Please add it in Settings → Business Profile.", "type": "business_context", "data": {}}

    try:
        context = f"Business: {settings.profile.business_name or 'Not configured'}. Currency: {settings.current_currency()}."
        prompt = f"{context}\nQuestion: {input_data.question}\nAnswer briefly and clearly for a small business owner."
        answer = run_llama(prompt, max_tokens=256)
        return {"answer": answer.strip(), "type": "ai", "data": {}}
    except Exception as exc:
        return {"answer": "I couldn't process that question. Try asking about your balance, expenses, or business summary.", "type": "error", "data": {}}


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)


from ledgermate.ledger import Ledger as _Ledger

def _get_ledger() -> _Ledger:
    return _Ledger(DB_PATH)


@app.delete("/api/transactions/{transaction_id}")
def delete_transaction(transaction_id: str) -> dict:
    ledger = get_ledger()
    ledger.soft_delete_transaction(transaction_id)
    return {"status": "ok"}


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
    ledger.soft_delete_invoice(invoice_id)
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
    ledger.soft_delete_customer(customer_id)
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
    ledger.soft_delete_product(product_id)
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


@app.get("/api/export/pdf")
def export_pdf(start_date: str | None = None, end_date: str | None = None) -> FileResponse:
    ledger = _get_ledger()
    rows = ledger.list_transactions(start_date=start_date, end_date=end_date)
    if not rows:
        raise HTTPException(status_code=404, detail="No transactions to export")
    from ledgermate.export import export_pdf
    out_path = Path(__file__).resolve().parents[2] / "data" / "exports" / "transactions.pdf"
    profile = settings.profile.to_dict()
    currency = settings.current_currency()
    export_pdf(rows, out_path, profile=profile, currency=currency)
    return FileResponse(out_path, media_type="application/pdf", filename="transactions.pdf")


@app.get("/api/export/word")
def export_word(start_date: str | None = None, end_date: str | None = None) -> FileResponse:
    ledger = _get_ledger()
    rows = ledger.list_transactions(start_date=start_date, end_date=end_date)
    if not rows:
        raise HTTPException(status_code=404, detail="No transactions to export")
    from ledgermate.export import export_word
    out_path = Path(__file__).resolve().parents[2] / "data" / "exports" / "transactions.docx"
    profile = settings.profile.to_dict()
    currency = settings.current_currency()
    export_word(rows, out_path, profile=profile, currency=currency)
    return FileResponse(out_path, media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document", filename="transactions.docx")


@app.get("/api/invoices/{invoice_id}/pdf")
def export_invoice_pdf(invoice_id: str) -> FileResponse:
    ledger = _get_ledger()
    invoice = next((inv for inv in ledger.list_invoices() if inv.get("invoice_id") == invoice_id), None)
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    from ledgermate.export import export_invoice_pdf
    out_path = Path(__file__).resolve().parents[2] / "data" / "exports" / f"{invoice_id}.pdf"
    profile = settings.profile.to_dict()
    currency = settings.current_currency()
    export_invoice_pdf(invoice, out_path, profile=profile, currency=currency)
    return FileResponse(out_path, media_type="application/pdf", filename=f"{invoice_id}.pdf")

@app.get("/api/invoices/{invoice_id}/word")
def export_invoice_word(invoice_id: str) -> FileResponse:
    ledger = _get_ledger()
    invoice = next((inv for inv in ledger.list_invoices() if inv.get("invoice_id") == invoice_id), None)
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    from ledgermate.export import export_invoice_word
    out_path = Path(__file__).resolve().parents[2] / "data" / "exports" / f"{invoice_id}.docx"
    profile = settings.profile.to_dict()
    currency = settings.current_currency()
    export_invoice_word(invoice, out_path, profile=profile, currency=currency)
    return FileResponse(out_path, media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document", filename=f"{invoice_id}.docx")

@app.get("/api/conversations")
def list_conversations() -> list[dict]:
    conv_dir = Path(__file__).resolve().parents[2] / "data" / "conversations"
    conv_dir.mkdir(parents=True, exist_ok=True)
    conversations = []
    for path in sorted(conv_dir.glob("*.json")):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            conversations.append({"id": path.stem, "title": data.get("title", "Conversation"), "updated_at": data.get("updated_at", "")})
        except Exception:
            continue
    return conversations


@app.post("/api/conversations")
def create_conversation(payload: dict) -> dict:
    conv_dir = Path(__file__).resolve().parents[2] / "data" / "conversations"
    conv_dir.mkdir(parents=True, exist_ok=True)
    conv_id = f"conv-{datetime.now().strftime('%Y%m%d%H%M%S%f')}"
    path = conv_dir / f"{conv_id}.json"
    data = {
        "id": conv_id,
        "title": payload.get("title", "New Conversation"),
        "messages": [],
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
    }
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    return data


@app.post("/api/conversations/{conv_id}/messages")
def add_conversation_message(conv_id: str, payload: dict) -> dict:
    conv_dir = Path(__file__).resolve().parents[2] / "data" / "conversations"
    path = conv_dir / f"{conv_id}.json"
    if not path.exists():
        raise HTTPException(status_code=404, detail="Conversation not found")
    data = json.loads(path.read_text(encoding="utf-8"))
    data.setdefault("messages", []).append({
        "role": payload.get("role", "user"),
        "content": payload.get("content", ""),
        "created_at": datetime.now().isoformat(),
    })
    data["updated_at"] = datetime.now().isoformat()
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    return data


@app.get("/api/conversations/{conv_id}")
def get_conversation(conv_id: str) -> dict:
    conv_dir = Path(__file__).resolve().parents[2] / "data" / "conversations"
    path = conv_dir / f"{conv_id}.json"
    if not path.exists():
        raise HTTPException(status_code=404, detail="Conversation not found")
    return json.loads(path.read_text(encoding="utf-8"))


@app.delete("/api/conversations/{conv_id}")
def delete_conversation(conv_id: str) -> dict:
    conv_dir = Path(__file__).resolve().parents[2] / "data" / "conversations"
    path = conv_dir / f"{conv_id}.json"
    if path.exists():
        path.unlink()
    return {"status": "ok"}


def _port_in_use(host: str, port: int) -> bool:
    try:
        output = os.popen(f"netstat -ano | findstr :{port}").read()
    except Exception:
        return False
    for line in output.splitlines():
        parts = line.split()
        if len(parts) >= 2 and parts[1].endswith(f":{port}") and parts[-2].upper() == "LISTENING":
            return True
    return False


def _can_bind(host: str, port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            sock.bind((host, port))
            return True
        except OSError:
            return False


def _owner_process(port: int) -> dict | None:
    try:
        output = os.popen(f"netstat -ano | findstr :{port}").read()
    except Exception:
        return None
    info: dict[str, Any] = {"bindings": [], "pids": []}
    for line in output.splitlines():
        parts = line.split()
        if len(parts) >= 2:
            proto = parts[0]
            addr = parts[1]
            state = parts[3] if len(parts) >= 4 else ""
            if addr.endswith(f":{port}") and state.upper() == "LISTENING":
                pid = parts[-1]
                info["bindings"].append({"proto": proto, "addr": addr, "state": state, "pid": pid})
                info["pids"].append(pid)
    unique_pids = sorted(set(info["pids"]))
    info["pids"] = unique_pids
    for pid in unique_pids:
        try:
            cmd = os.popen(f'tasklist /FI "PID eq {pid}" /NH').read().strip()
            info.setdefault("processes", {})[pid] = cmd
        except Exception:
            pass
    return info


def _is_ledgermate_health(host: str, port: int) -> bool:
    try:
        import urllib.request
        with urllib.request.urlopen(f"http://{host}:{port}/api/health", timeout=2) as resp:
            body = resp.read().decode("utf-8")
            return '"status":"ok"' in body and '"offline"' in body
    except Exception:
        return False


def _safe_default_port(host: str, preferred_port: int) -> tuple[str, int]:
    if not _port_in_use(host, preferred_port) and _can_bind(host, preferred_port):
        return host, preferred_port
    owner = _owner_process(preferred_port)
    ledgermate_running = bool(owner and _is_ledgermate_health(host, preferred_port))
    print(f"[LedgerMate] Port {host}:{preferred_port} is in use.")
    if owner:
        print(f"[LedgerMate] Owner diagnostics: {json.dumps(owner)}")
    if ledgermate_running:
        print(f"[LedgerMate] Existing LedgerMate instance detected at http://{host}:{preferred_port}")
        print(f"[LedgerMate] Open that URL instead of starting another instance.")
        sys.exit(0)
    fallback = preferred_port + 1
    while not _can_bind(host, fallback):
        fallback += 1
    print(f"[LedgerMate] Falling back to http://{host}:{fallback}")
    return host, fallback


if __name__ == "__main__":
    host = os.environ.get("LEDGERMATE_HOST", "127.0.0.1")
    port = int(os.environ.get("LEDGERMATE_PORT", "8000"))
    host, port = _safe_default_port(host, port)
    print(f"[LedgerMate] Starting server at http://{host}:{port}")
    uvicorn.run("ledgermate.api:app", host=host, port=port, reload=False)
