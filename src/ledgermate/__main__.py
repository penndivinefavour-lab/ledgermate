"""LedgerMate V2 — TUI voice workflow."""
from __future__ import annotations

from pathlib import Path

from rich import print
from rich.panel import Panel
from rich.prompt import Prompt

from ledgermate.audio.recorder import AudioRecorder
from ledgermate.audio.states import VoiceState
from ledgermate.audio.transcript import Transcript
from ledgermate.config import Config
from ledgermate.domain.proposal import TransactionProposal
from ledgermate.ledger import Ledger
from ledgermate.providers.base import ExtractedTransaction
from ledgermate.providers.registry import build_registry
from ledgermate.validation import validate_transaction


def _summarize_transcript(transcript: Transcript) -> str:
    text = transcript.final or transcript.edited or transcript.current or transcript.raw
    return text[:200]


def _summarize_proposal(proposal: TransactionProposal) -> str:
    return (
        f"Type: {proposal.transaction_type}\n"
        f"Amount: {proposal.amount} {proposal.currency}\n"
        f"Date: {proposal.date}\n"
        f"Description: {proposal.description}\n"
        f"Category: {proposal.category}\n"
        f"Counterparty: {proposal.counterparty or '-'}\n"
        f"Payment method: {proposal.payment_method or '-'}"
    )


def run_voice_workflow(ledger: Ledger, registry=None, config=None, recorder=None) -> VoiceState:
    config = config or Config()
    registry = registry or build_registry()
    recorder = recorder or AudioRecorder(config)

    state = VoiceState.IDLE
    audio_path = None
    transcript = None
    proposal = None

    try:
        print("[bold green]Voice workflow[/bold green] — press Ctrl+C to cancel")
        if not recorder.available:
            print("[red]Audio recording is not available on this system.[/red]")
            return VoiceState.FAILED

        # Record
        state = VoiceState.RECORDING
        print("[bold cyan]Recording...[/bold cyan]")
        audio_path = recorder.start()
        input("[Press Enter to stop recording]")
        audio_path = recorder.stop()
        print(f"[green]Saved:[/green] {audio_path}")

        # Transcribe
        state = VoiceState.TRANSCRIBING
        print("[bold cyan]Transcribing...[/bold cyan]")
        transcript = registry.stt.transcribe(audio_path)
        print(f"[green]Transcript:[/green] {_summarize_transcript(transcript)}")

        # Edit
        state = VoiceState.EDITING
        edited = Prompt.ask("[bold yellow]Edit transcript[/bold yellow]", default=_summarize_transcript(transcript))
        transcript.apply_edit(edited)

        # Extract
        state = VoiceState.PROCESSING
        print("[bold cyan]Extracting transaction...[/bold cyan]")
        extracted: ExtractedTransaction = registry.llm.extract_transaction(transcript.final or transcript.current)
        proposal = TransactionProposal(
            transaction_type=extracted.transaction_type,
            amount=extracted.amount,
            currency=extracted.currency,
            date=extracted.date,
            description=extracted.description,
            category=extracted.category,
            counterparty=extracted.counterparty,
            payment_method=extracted.payment_method,
            notes=extracted.notes,
        )
        print(Panel(_summarize_proposal(proposal), title="Proposed Transaction"))

        # Confirm
        state = VoiceState.CONFIRMATION
        confirm = Prompt.ask("[bold yellow]Save this transaction?[/bold yellow]", choices=["y", "n"], default="y")
        if confirm.lower() != "y":
            state = VoiceState.CANCELLED
            print("[yellow]Transaction not saved.[/yellow]")
            return state

        # Validate and commit
        validated = validate_transaction(proposal.confirmed_dict())
        ledger.add_transaction(validated)
        state = VoiceState.SAVED
        print(f"[green]Recorded:[/green] {validated.date} {validated.type} {validated.amount} {validated.currency} — {validated.description}")
        return state

    except KeyboardInterrupt:
        state = VoiceState.CANCELLED
        print("\n[yellow]Cancelled.[/yellow]")
        return state
    except Exception as exc:
        state = VoiceState.FAILED
        print(f"[red]Voice workflow failed:[/red] {exc}")
        return state
    finally:
        if audio_path and audio_path.exists() and state != VoiceState.SAVED:
            try:
                audio_path.unlink()
            except FileNotFoundError:
                pass


def run_cli(ledger_path: Path | None = None) -> None:
    config = Config()
    config.ensure_dirs()
    ledger = Ledger(ledger_path or config.data_dir / "ledger.db")
    registry = build_registry()
    recorder = AudioRecorder(config)

    print(Panel.fit("[bold green]LedgerMate V2[/bold green] — Offline SME Bookkeeping Assistant"))
    print("Commands: balance, list, export, voice, exit")
    while True:
        user_input = Prompt.ask("[bold cyan]You[/bold cyan]")
        if not user_input.strip():
            continue
        if user_input.strip().lower() in {"exit", "quit"}:
            print("Goodbye.")
            return
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
            csv_path = export_csv(rows, config.exports_dir / "transactions.csv")
            json_path = export_json(rows, config.exports_dir / "transactions.json")
            print(f"Exported CSV: {csv_path}")
            print(f"Exported JSON: {json_path}")
            continue
        if user_input.strip().lower() == "voice":
            run_voice_workflow(ledger, registry=registry, config=config, recorder=recorder)
            continue

        # Text fallback
        extracted = registry.llm.extract_transaction(user_input)
        try:
            txn = validate_transaction(extracted.__dict__)
        except Exception as exc:
            print(f"[yellow]Validation error: {exc}[/yellow]")
            continue
        ledger.add_transaction(txn)
        print(f"[green]Recorded:[/green] {txn.date} {txn.type} {txn.amount} {txn.currency} — {txn.description}")


if __name__ == "__main__":
    run_cli()
