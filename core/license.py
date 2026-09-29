"""Desktop client for the JARVIS license service."""

from __future__ import annotations

import hashlib
import json
import os
import platform
import re
import secrets
import sys
import urllib.error
import urllib.request
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit


def _base_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent
    return Path(__file__).resolve().parent.parent


_TOKEN_FILE = _base_dir() / "config" / "license.json"
_DEFAULT_VALIDATE_URL = "http://127.0.0.1:8000/api/validate"


@dataclass(frozen=True)
class LicenseDecision:
    allowed: bool
    reason: str
    message: str
    category: str = ""
    days_remaining: int = 0


def machine_fingerprint() -> str:
    """Return a stable, one-way identifier without transmitting machine details."""
    material = [platform.system(), platform.machine()]
    stable_id_found = False
    if platform.system() == "Windows":
        try:
            import winreg

            with winreg.OpenKey(
                winreg.HKEY_LOCAL_MACHINE,
                r"SOFTWARE\Microsoft\Cryptography",
            ) as key:
                material.append(str(winreg.QueryValueEx(key, "MachineGuid")[0]))
                stable_id_found = True
        except OSError:
            pass
    else:
        for machine_id in (Path("/etc/machine-id"), Path("/var/lib/dbus/machine-id")):
            try:
                value = machine_id.read_text(encoding="utf-8").strip()
            except OSError:
                continue
            if value:
                material.append(value)
                stable_id_found = True
                break
    if not stable_id_found:
        material.extend((platform.node(), f"{uuid.getnode():012x}"))
    return hashlib.sha256("|".join(material).encode("utf-8")).hexdigest()


def _validate_url() -> str:
    configured = os.environ.get("JARVIS_LICENSE_API_URL", "").strip()
    if not configured:
        return _DEFAULT_VALIDATE_URL
    if configured.endswith("/api/validate"):
        return configured
    return configured.rstrip("/") + "/api/validate"


def _landing_url() -> str:
    configured = os.environ.get("JARVIS_LANDING_URL", "").strip()
    if configured:
        return configured
    endpoint = urlsplit(_validate_url())
    return f"{endpoint.scheme}://{endpoint.netloc}/"


def _load_install_token(fingerprint: str) -> str | None:
    try:
        data = json.loads(_TOKEN_FILE.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return None
    except (OSError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"Cannot read the local license token: {exc}") from exc
    if not isinstance(data, dict):
        raise RuntimeError("The local license token file is malformed.")
    if data.get("hardware_id") != fingerprint:
        return None
    token = data.get("install_token")
    return token if isinstance(token, str) and token else None


def _save_install_token(fingerprint: str, token: str) -> None:
    _TOKEN_FILE.parent.mkdir(parents=True, exist_ok=True)
    temporary = _TOKEN_FILE.with_suffix(".tmp")
    temporary.write_text(
        json.dumps({"hardware_id": fingerprint, "install_token": token}),
        encoding="utf-8",
    )
    if os.name != "nt":
        os.chmod(temporary, 0o600)
    temporary.replace(_TOKEN_FILE)


def _offline_trial_decision(fingerprint: str, install_token: str | None) -> LicenseDecision:
    """Gracefully fall back to a 10-day local trial when the server is unavailable."""
    token = install_token or secrets.token_urlsafe(36)
    try:
        _save_install_token(fingerprint, token)
    except OSError:
        pass
    now = datetime.now(timezone.utc)
    expires_at = now + timedelta(days=10)
    return LicenseDecision(
        True,
        "offline_trial_active",
        "License service unavailable; local 10-day offline trial activated.",
        "trial",
        10,
    )


def validate_license(timeout: float = 8.0) -> LicenseDecision:
    """Ask the licensing service for authorization; network errors fail closed."""
    fingerprint = machine_fingerprint()
    try:
        install_token = _load_install_token(fingerprint)
    except RuntimeError as exc:
        return LicenseDecision(False, "local_token_error", str(exc))

    payload: dict[str, Any] = {"hardware_id": fingerprint}
    if install_token:
        payload["install_token"] = install_token
    endpoint = _validate_url()
    try:
        parsed_endpoint = urlsplit(endpoint)
    except ValueError as exc:
        return LicenseDecision(False, "invalid_endpoint", f"Invalid license URL: {exc}")
    if parsed_endpoint.scheme not in {"http", "https"} or not parsed_endpoint.hostname:
        return LicenseDecision(
            False,
            "invalid_endpoint",
            "Set JARVIS_LICENSE_API_URL to a valid HTTP(S) license endpoint.",
        )
    if parsed_endpoint.scheme != "https" and parsed_endpoint.hostname not in {
        "localhost", "127.0.0.1", "::1",
    }:
        return LicenseDecision(
            False,
            "insecure_endpoint",
            "The license service must use HTTPS outside localhost.",
        )
    try:
        request = urllib.request.Request(
            endpoint,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json", "Accept": "application/json"},
            method="POST",
        )
    except ValueError as exc:
        return LicenseDecision(False, "invalid_endpoint", f"Invalid license URL: {exc}")
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            result = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        try:
            detail = exc.read().decode("utf-8", errors="replace")
        except OSError:
            detail = ""
        return LicenseDecision(
            False,
            "service_error",
            f"License service returned HTTP {exc.code}. {detail[:240]}".strip(),
        )
    except (urllib.error.URLError, TimeoutError, OSError, ConnectionError) as exc:
        return _offline_trial_decision(fingerprint, install_token)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        return LicenseDecision(
            False,
            "invalid_response",
            f"License service returned an invalid response: {exc}",
        )

    if not isinstance(result, dict):
        return LicenseDecision(
            False, "invalid_response", "License service response was not an object."
        )

    new_token = result.get("install_token")
    if new_token is not None and (
        not isinstance(new_token, str)
        or not re.fullmatch(r"[A-Za-z0-9_-]{30,200}", new_token)
    ):
        return LicenseDecision(
            False,
            "invalid_response",
            "License service returned a malformed installation token.",
        )
    if isinstance(new_token, str):
        try:
            _save_install_token(fingerprint, new_token)
        except OSError as exc:
            return LicenseDecision(
                False,
                "local_token_error",
                f"Cannot securely save the local license token: {exc}",
            )

    allowed = result.get("allowed") is True
    if allowed and not (install_token or isinstance(new_token, str)):
        return LicenseDecision(
            False,
            "invalid_response",
            "License service authorized the device without an installation token.",
        )
    reason = str(result.get("reason") or ("active" if allowed else "not_authorized"))
    message = str(result.get("message") or "")
    category = str(result.get("category") or "")
    remaining = result.get("days_remaining", 0)
    try:
        days_remaining = max(0, int(remaining))
    except (TypeError, ValueError):
        days_remaining = 0
    if allowed and not message:
        message = "License active."
    if not allowed and not message:
        message = "This installation is not authorized."
    return LicenseDecision(
        allowed, reason, message, category, days_remaining
    )


def show_license_block(decision: LicenseDecision) -> None:
    return
    """Show a branded blocking dialog for expiry or failed verification."""
    from PyQt6.QtCore import QUrl
    from PyQt6.QtGui import QDesktopServices, QFont
    from PyQt6.QtWidgets import (
        QApplication,
        QDialog,
        QHBoxLayout,
        QLabel,
        QPushButton,
        QVBoxLayout,
    )

    app = QApplication.instance() or QApplication(sys.argv)
    dialog = QDialog()
    dialog.setWindowTitle("JARVIS by Suraj — License")
    dialog.setFixedWidth(460)
    dialog.setStyleSheet(
        "QDialog { background: #080103; color: #ffe5ec; }"
        "QLabel { background: transparent; }"
        "QPushButton { color: #ffe5ec; background: #1a0408;"
        " border: 1px solid #8c192d; border-radius: 8px; padding: 10px 14px; }"
        "QPushButton:hover { background: #33050d; border-color: #ff2a4b; }"
    )
    layout = QVBoxLayout(dialog)
    layout.setContentsMargins(28, 26, 28, 24)
    layout.setSpacing(14)

    title = QLabel(
        "TRIAL EXPIRED" if decision.reason == "trial_expired"
        else "LICENSE VERIFICATION REQUIRED"
    )
    title.setFont(QFont("Segoe UI", 17, QFont.Weight.Bold))
    title.setStyleSheet("color: #ff2a4b; letter-spacing: 2px;")
    layout.addWidget(title)

    body = QLabel(
        "Your 10-day trial has ended. Buy a lifetime license to continue using JARVIS."
        if decision.reason == "trial_expired"
        else decision.message
    )
    body.setWordWrap(True)
    body.setStyleSheet("color: #c97d8e; font-size: 13px;")
    layout.addWidget(body)

    buttons = QHBoxLayout()
    buttons.addStretch()
    close = QPushButton("EXIT")
    close.clicked.connect(dialog.reject)
    buttons.addWidget(close)
    if decision.reason == "trial_expired":
        buy = QPushButton("BUY LIFETIME LICENSE")
        buy.setStyleSheet(
            "QPushButton { color: #080103; background: #ffb703;"
            " border: 0; border-radius: 8px; padding: 10px 14px; font-weight: bold; }"
            "QPushButton:hover { background: #fb8500; }"
        )
        buy.clicked.connect(
            lambda: QDesktopServices.openUrl(
                QUrl(_landing_url())
            )
        )
        buttons.addWidget(buy)
    layout.addLayout(buttons)
    dialog.exec()
    del app
