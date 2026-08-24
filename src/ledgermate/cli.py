"""LedgerMate CLI."""
from __future__ import annotations

import uuid
from datetime import date
from decimal import Decimal
from pathlib import Path
from typing import Optional

from rich import print
from rich.panel import Panel
from rich.prompt import Prompt

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from ledgermate.ledger import Ledger

from ledgermate.llm import extract_transaction_json
from ledgermate.validation import validate_transaction


DEFAULT_LEDGER = Path(__file__).resolve().parents[2] / "ledger.db"


def _fallback_transaction_from_text(text: str) -> dict:
    today = date.today().isoformat()
    return {
        "transaction_id": f"txn-{uuid.uuid4().hex[:8]}",
        "date": today,
        "description": text[:120],
        "category": "general",
        "type": "expense",
        "amount": "0",
        "currency": "XAF",
        "payment_method": "cash",
        "counterparty": None,
        "notes": "LLM extraction failed; manual entry required",
        "source": "fallback",
    }


def run_cli(ledger_path: Path = DEFAULT_LEDGER) -> None:
    ledger = Ledger(ledger_path)
    print(Panel.fit("[bold green]LedgerMate[/bold green] — Offline SME Bookkeeping Assistant"))
    print("Type a transaction, or commands: balance, list, export, exit")
    while True:
        user_input = Prompt.ask("[bold cyan]You[/bold cyan]")
        if not user_input.strip():
            continue
        if user_input.strip().lower() in {"exit", "quit"}:
            print("Goodbye.")
            return
        if user_input.strip().lower() == "help":
            print("Type a transaction, or commands: balance, list, export, exit")
            print("help       - show this help")
            print("balance    - show income/expense/net")
            print("list       - show all transactions")
            print("export     - export to CSV and JSON")
            print("exit       - exit LedgerMate")
            continue

        if user_input.strip().lower() == "balance":
            bal = ledger.balance()
            print(f"Income: {bal['income']} {bal['currency']}")
            print(f"Expense: {bal['expense']} {bal['currency']}")
            print(f"Net: {bal['net']} {bal['currency']}")
            continue
        if user_input.strip().lower() == "list":
            rows = ledger.list_transactions()
            for row in rows:
                print(row)
            continue
        if user_input.strip().lower().startswith("export"):
            rows = ledger.list_transactions()
            from ledgermate.export import export_csv, export_json
            csv_path = export_csv(rows, Path("exports/transactions.csv"))
            json_path = export_json(rows, Path("exports/transactions.json"))
            print(f"Exported CSV: {csv_path}")
            print(f"Exported JSON: {json_path}")
            continue

        extracted = extract_transaction_json(user_input)
        try:
            txn = validate_transaction(extracted)
        except Exception as exc:
            print(f"[yellow]Validation error: {exc}[/yellow]")
            txn = validate_transaction(_fallback_transaction_from_text(user_input))
        ledger.add_transaction(txn)
        print(f"[green]Recorded:[/green] {txn.date} {txn.type} {txn.amount} {txn.currency} — {txn.description}")


if __name__ == "__main__":
    run_cli()
