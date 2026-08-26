"""CSV, JSON, PDF and Word export utilities."""
from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any, Iterable

from fpdf import FPDF


def export_csv(transactions: Iterable[dict], path: str | Path) -> Path:
    rows = list(transactions)
    if not rows:
        raise ValueError("No transactions to export")
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    return out


def export_json(transactions: Iterable[dict], path: str | Path) -> Path:
    rows = list(transactions)
    if not rows:
        raise ValueError("No transactions to export")
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(rows, indent=2, ensure_ascii=False), encoding="utf-8")
    return out


def _build_pdf_bytes(rows: list[dict], profile: dict[str, Any], currency: str) -> bytes:
    lines: list[str] = []
    title = profile.get("business_name") or "LedgerMate"
    lines.append(f"{title} - Transactions Export")
    lines.append(f"Currency: {currency}")
    lines.append("")
    for row in rows:
        lines.append(f"{row.get('date', '')} | {row.get('type', '').upper()} | {row.get('amount', '0')} {currency} | {row.get('description', '')} | {row.get('category', '')}")
    return "\n".join(lines).encode("utf-8")


def export_invoice_pdf(invoice: dict[str, Any], path: str | Path, *, profile: dict[str, Any] | None = None, currency: str = "XAF") -> Path:
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    title = (profile or {}).get("business_name") or "LedgerMate"
    customer = invoice.get("customer_name", "Customer")
    items = invoice.get("items", [])

    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 10, title, ln=True)
    pdf.set_font("Helvetica", "", 12)
    pdf.cell(0, 8, f"Invoice: {invoice.get('invoice_id', '')}", ln=True)
    pdf.cell(0, 8, f"Customer: {customer}", ln=True)
    pdf.cell(0, 8, f"Date: {invoice.get('created_at', invoice.get('date', ''))}", ln=True)
    pdf.cell(0, 8, f"Status: {invoice.get('status', 'draft')}", ln=True)
    pdf.ln(6)

    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 8, "Items:", ln=True)
    pdf.set_font("Helvetica", "", 12)
    for item in items:
        name = item.get("name", "Item")
        quantity = item.get("quantity", 1)
        unit_price = item.get("unit_price", 0)
        total = item.get("total", unit_price)
        pdf.cell(0, 8, f"- {name} x{quantity} @ {unit_price} {currency} = {total} {currency}", ln=True)

    pdf.ln(4)
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 8, f"Subtotal: {invoice.get('subtotal', 0)} {currency}", ln=True)
    pdf.cell(0, 8, f"Tax: {invoice.get('tax', 0)} {currency}", ln=True)
    pdf.cell(0, 8, f"Discount: {invoice.get('discount', 0)} {currency}", ln=True)
    pdf.cell(0, 8, f"Total: {invoice.get('total', 0)} {currency}", ln=True)

    pdf.output(str(out))
    return out


def export_invoice_word(invoice: dict[str, Any], path: str | Path, *, profile: dict[str, Any] | None = None, currency: str = "XAF") -> Path:
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    title = (profile or {}).get("business_name") or "LedgerMate"
    customer = invoice.get("customer_name", "Customer")
    rows = invoice.get("items", [])
    html = f"""<html><head><meta charset='UTF-8'><title>{title}</title></head><body>
<h1>{title}</h1>
<p>Invoice: {invoice.get('invoice_id', '')}</p>
<p>Customer: {customer}</p>
<p>Date: {invoice.get('created_at', invoice.get('date', ''))}</p>
<p>Status: {invoice.get('status', 'draft')}</p>
<table border='1' cellpadding='6' cellspacing='0'>
<tr><th>Item</th><th>Qty</th><th>Unit Price</th><th>Total</th></tr>
"""
    for item in rows:
        html += f"<tr><td>{item.get('name', 'Item')}</td><td>{item.get('quantity', 1)}</td><td>{item.get('unit_price', 0)} {currency}</td><td>{item.get('total', item.get('unit_price', 0))} {currency}</td></tr>\n"
    html += f"</table><p><strong>Subtotal:</strong> {invoice.get('subtotal', 0)} {currency}</p>"
    html += f"<p><strong>Tax:</strong> {invoice.get('tax', 0)} {currency}</p>"
    html += f"<p><strong>Discount:</strong> {invoice.get('discount', 0)} {currency}</p>"
    html += f"<p><strong>Total:</strong> {invoice.get('total', 0)} {currency}</p></body></html>"
    out.write_text(html, encoding="utf-8")
    return out


def export_pdf(transactions: Iterable[dict], path: str | Path, *, profile: dict[str, Any] | None = None, currency: str = "XAF") -> Path:
    rows = list(transactions)
    if not rows:
        raise ValueError("No transactions to export")
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    payload = _build_pdf_bytes(rows, profile or {}, currency)
    out.write_bytes(payload)
    return out


def export_word(transactions: Iterable[dict], path: str | Path, *, profile: dict[str, Any] | None = None, currency: str = "XAF") -> Path:
    rows = list(transactions)
    if not rows:
        raise ValueError("No transactions to export")
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    title = profile.get("business_name") or "LedgerMate" if profile else "LedgerMate"
    html = f"""<html><head><meta charset='UTF-8'><title>{title}</title></head><body>
<h1>{title}</h1>
<p>Currency: {currency}</p>
<table border='1' cellpadding='6' cellspacing='0'>
<tr><th>Date</th><th>Type</th><th>Amount</th><th>Description</th><th>Category</th></tr>
"""
    for row in rows:
        html += f"<tr><td>{row.get('date', '')}</td><td>{row.get('type', '')}</td><td>{row.get('amount', '0')} {currency}</td><td>{row.get('description', '')}</td><td>{row.get('category', '')}</td></tr>\n"
    html += "</table></body></html>"
    out.write_text(html, encoding="utf-8")
    return out
