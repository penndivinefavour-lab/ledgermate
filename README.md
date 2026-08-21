# LedgerMate

**Offline SME Bookkeeping Assistant for Africa**

Africa Deep Tech Challenge 2026 — The Laptop LLM Challenge

## Problem

Small business owners in Cameroon and across Africa keep ledgers on paper, in spreadsheets, or in their heads. When records are lost, damaged, or never reconciled, owners cannot answer basic questions: “How much cash do I have today?”, “Who owes me money?”, “What did I spend last month?”

LedgerMate converts natural-language transaction descriptions into structured, validated ledger entries — entirely on-device, with no internet, no cloud fees, and no subscription.

## What it does

- Converts natural-language input into structured bookkeeping entries.
- Validates every transaction with a deterministic Python Decimal engine.
- Stores records in SQLite with an append-only audit log.
- Exports to CSV and JSON.
- Runs 100% offline using a local GGUF model via llama.cpp.

## Example

```
You: Yesterday I bought 15 bags of feed for 180,000 XAF from a supplier in Bamenda. I paid 80,000 XAF cash and owe the remaining 100,000 XAF.

LedgerMate extracts:
- date: 2026-08-19
- type: expense
- category: inventory/feed
- amount: 180000 XAF
- payment_method: cash + payable
- counterparty: Bamenda supplier
- notes: partial payment; 100000 XAF outstanding
```

## Why this matters for Africa

- No stable internet required after model download.
- No recurring SaaS costs.
- No data leaves the device.
- Designed for cash, partial payments, and mobile-money-style records — the actual daily reality of African SMEs.

## Architecture

```
Natural language → LLM extraction → Validation layer → Python Decimal engine → SQLite → Export
```

The LLM interprets intent. The deterministic engine owns arithmetic and ledger integrity.

## Technology

- **Inference:** Llama 3.2 1B Instruct GGUF Q4_K_M via llama.cpp
- **Validation:** Python Decimal deterministic engine
- **Storage:** SQLite with append-only audit log
- **Runtime:** 100% offline, no cloud APIs
- **Target hardware:** 8 GB RAM commodity laptop

## Competition

- **Challenge:** Africa Deep Tech Challenge 2026 — Laptop LLM Track
- **Domain:** Corporate / Enterprise
- **Team:** Solo — Penn Divine Favour
- **Repository:** https://github.com/penndivinefavour-lab/ledgermate

## Quick start

```bash
# 1. Download model weights
bash download_model.sh

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run the CLI
python src/cli.py
```

## Model license

Llama 3.2 Community License — attribution required: “Built with Llama”.

## LedgerMate code license

MIT License

## Status

Day 2 implementation in progress. Core engine, CLI, and tests are being built. Benchmarks will be run on Dell Vostro 3500 with the official ADTC profiler.
