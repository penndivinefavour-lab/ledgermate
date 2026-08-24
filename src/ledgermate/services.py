"""LedgerMate shared business context services."""
from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from datetime import date, datetime
from pathlib import Path
from typing import Any

CONFIG_PATH = Path(__file__).resolve().parents[2] / "data" / "settings.json"


def _load_settings() -> dict[str, Any]:
    if CONFIG_PATH.exists():
        try:
            return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
        except Exception:
            return {}
    return {}


def _save_settings(data: dict[str, Any]) -> None:
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    CONFIG_PATH.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


@dataclass
class BusinessProfile:
    business_name: str = ""
    owner_name: str = ""
    business_type: str = ""
    industry: str = ""
    description: str = ""
    phone: str = ""
    email: str = ""
    website: str = ""
    address: str = ""
    city: str = ""
    region: str = ""
    country: str = ""
    tax_id: str = ""
    registration_number: str = ""
    logo_path: str = ""
    primary_color: str = "#10b981"
    secondary_color: str = "#0b1220"
    accent_color: str = "#10b981"

    def to_dict(self) -> dict[str, Any]:
        return {
            "business_name": self.business_name,
            "owner_name": self.owner_name,
            "business_type": self.business_type,
            "industry": self.industry,
            "description": self.description,
            "phone": self.phone,
            "email": self.email,
            "website": self.website,
            "address": self.address,
            "city": self.city,
            "region": self.region,
            "country": self.country,
            "tax_id": self.tax_id,
            "registration_number": self.registration_number,
            "logo_path": self.logo_path,
            "primary_color": self.primary_color,
            "secondary_color": self.secondary_color,
            "accent_color": self.accent_color,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "BusinessProfile":
        fields = {f.name for f in cls.__dataclass_fields__.values()}
        defaults = {f.name: f.default for f in cls.__dataclass_fields__.values()}
        return cls(**{k: data.get(k, defaults.get(k, "")) for k in fields})


@dataclass
class FinancialSettings:
    currency: str = "XAF"
    decimal_places: int = 0
    tax_rate: float = 0.0
    invoice_prefix: str = "INV"
    payment_terms_days: int = 14

    def to_dict(self) -> dict[str, Any]:
        return {
            "currency": self.currency,
            "decimal_places": self.decimal_places,
            "tax_rate": self.tax_rate,
            "invoice_prefix": self.invoice_prefix,
            "payment_terms_days": self.payment_terms_days,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "FinancialSettings":
        fields = {f.name for f in cls.__dataclass_fields__.values()}
        defaults = {f.name: f.default for f in cls.__dataclass_fields__.values()}
        return cls(**{k: data.get(k, defaults.get(k, "")) for k in fields})


@dataclass
class DateTimeSettings:
    use_device_time: bool = True
    manual_date: str = ""
    timezone: str = "UTC"
    date_format: str = "%Y-%m-%d"
    time_format: str = "%H:%M"

    def to_dict(self) -> dict[str, Any]:
        return {
            "use_device_time": self.use_device_time,
            "manual_date": self.manual_date,
            "timezone": self.timezone,
            "date_format": self.date_format,
            "time_format": self.time_format,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "DateTimeSettings":
        return cls(**{k: data.get(k, getattr(cls, k).default if hasattr(cls, k) else "") for k in {f.name for f in cls.__dataclass_fields__.values()}})


SUPPORTED_LANGUAGES = [
    ("en", "English"),
    ("fr", "French"),
    ("es", "Spanish"),
    ("pt", "Portuguese"),
    ("ar", "Arabic"),
    ("de", "German"),
    ("zh", "Chinese"),
]


TRANSLATIONS: dict[str, dict[str, str]] = {
    "en": {
        "dashboard": "Dashboard",
        "transactions": "Transactions",
        "invoices": "Invoices",
        "customers": "Customers",
        "products": "Products",
        "reports": "Reports",
        "assistant": "AI Assistant",
        "exports": "Exports",
        "trash": "Trash",
        "settings": "Settings",
        "business_name": "Business Name",
        "owner": "Owner",
        "phone": "Phone",
        "email": "Email",
        "currency": "Currency",
        "language": "Language",
        "save": "Save",
        "cancel": "Cancel",
        "confirm": "Confirm",
        "delete": "Delete",
        "restore": "Restore",
        "no_data": "No data yet.",
        "transaction_saved": "Transaction saved successfully.",
        "invoice_saved": "Invoice saved successfully.",
        "customer_saved": "Customer saved successfully.",
        "product_saved": "Product saved successfully.",
    },
    "fr": {
        "dashboard": "Tableau de bord",
        "transactions": "Transactions",
        "invoices": "Factures",
        "customers": "Clients",
        "products": "Produits",
        "reports": "Rapports",
        "assistant": "Assistant IA",
        "exports": "Exports",
        "trash": "Corbeille",
        "settings": "Paramètres",
        "business_name": "Nom de l'entreprise",
        "owner": "Propriétaire",
        "phone": "Téléphone",
        "email": "Email",
        "currency": "Devise",
        "language": "Langue",
        "save": "Enregistrer",
        "cancel": "Annuler",
        "confirm": "Confirmer",
        "delete": "Supprimer",
        "restore": "Restaurer",
        "no_data": "Aucune donnée.",
        "transaction_saved": "Transaction enregistrée.",
        "invoice_saved": "Facture enregistrée.",
        "customer_saved": "Client enregistré.",
        "product_saved": "Produit enregistré.",
    },
}


class AppSettings:
    def __init__(self) -> None:
        self._data = _load_settings()
        try:
            self.profile = BusinessProfile.from_dict(self._data.get("profile", {}))
        except Exception:
            self.profile = BusinessProfile()
        try:
            self.financial = FinancialSettings.from_dict(self._data.get("financial", {}))
        except Exception:
            self.financial = FinancialSettings()
        try:
            self.date_time = DateTimeSettings.from_dict(self._data.get("date_time", {}))
        except Exception:
            self.date_time = DateTimeSettings()
        self.language = str(self._data.get("language", "en"))

    def save(self) -> None:
        self._data["profile"] = self.profile.to_dict()
        self._data["financial"] = self.financial.to_dict()
        self._data["date_time"] = self.date_time.to_dict()
        self._data["language"] = self.language
        _save_settings(self._data)

    def current_date(self) -> date:
        if self.date_time.use_device_time and not self.date_time.manual_date:
            return date.today()
        if self.date_time.manual_date:
            try:
                return date.fromisoformat(self.date_time.manual_date)
            except ValueError:
                return date.today()
        return date.today()

    def current_currency(self) -> str:
        return self.financial.currency or "XAF"

    def t(self, key: str) -> str:
        lang = TRANSLATIONS.get(self.language, TRANSLATIONS["en"])
        return lang.get(key, TRANSLATIONS["en"].get(key, key))


settings = AppSettings()
