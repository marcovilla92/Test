"""Raybox GUI helper application.

This version modernises the interface with ttkbootstrap widgets and performs a
couple of quality-of-life tweaks for Windows environments (high DPI awareness
and persistent configuration stored under %APPDATA%).
"""
from __future__ import annotations

import csv
import hashlib
import json
import os
import socket
import sys
import threading
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Mapping, MutableMapping

import tkinter as tk
from tkinter import filedialog, messagebox, ttk

try:  # pragma: no cover - runtime fallback
    import ttkbootstrap as tb  # type: ignore
    from ttkbootstrap.scrolled import ScrolledText  # type: ignore
except ModuleNotFoundError:  # pragma: no cover - fallback for environments without ttkbootstrap
    tb = None
    ScrolledText = None

import requests

APP_TITLE = "Raybox GUI — Compatibile ttkbootstrap 1.x"
DEFAULT_THEME = "superhero"
DEFAULT_PORT = 8080
ENV_PATH = Path(__file__).with_name(".env")
TABLE_COLUMNS = ("id", "nome", "macchina", "inizio", "fine", "durata")


class GUIInitError(RuntimeError):
    """Raised when the GUI cannot be initialised."""


@dataclass(slots=True)
class RayboxCredentials:
    """Container for Raybox credentials."""

    token: str
    secret: str

    def valid(self) -> bool:
        return bool(self.token and self.secret)


@dataclass(slots=True)
class RayboxRequest:
    """Container for Raybox request configuration."""

    base_url: str
    credentials: RayboxCredentials

    def headers(self) -> Dict[str, str]:
        timestamp = int(time.time() * 1000)
        sign_src = f"timestamp={timestamp}&token={self.credentials.token}&secret={self.credentials.secret}"
        signature = hashlib.md5(sign_src.encode("utf-8")).hexdigest()
        return {
            "token": self.credentials.token,
            "timestamp": str(timestamp),
            "sign": signature,
        }


def tcp_check(host: str, port: int = DEFAULT_PORT, timeout: float = 3) -> bool:
    """Check if a TCP port is reachable."""

    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except OSError:
        return False


def ensure_ttkbootstrap() -> type:
    """Return the ttkbootstrap window class if available."""

    if tb is None:
        raise GUIInitError(
            "ttkbootstrap non è installato. Installa 'ttkbootstrap' oppure usa l'interfaccia Tk standard."
        )
    return tb.Window


def enable_windows_enhancements() -> None:
    """Apply high DPI and AppUserModelID hints on Windows for a crisper UI."""

    if not sys.platform.startswith("win"):
        return

    try:  # pragma: no cover - requires Windows
        ctypes = __import__("ctypes")
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except Exception:
        pass

    try:  # pragma: no cover - requires Windows 7+
        ctypes = __import__("ctypes")
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("RayboxGUI")
    except Exception:
        pass


def config_path() -> Path:
    """Return the path where persistent settings are stored."""

    if sys.platform.startswith("win"):
        base_dir = Path(os.environ.get("APPDATA", Path.home()))
    else:
        base_dir = Path.home() / ".config"
    return base_dir / "RayboxGUI" / "settings.json"


class RayboxApp:
    """Tk GUI for interacting with Raybox devices."""

    def __init__(self) -> None:
        enable_windows_enhancements()

        window_cls = ensure_ttkbootstrap()
        self.window = window_cls(themename=DEFAULT_THEME)
        self.window.title(APP_TITLE)
        self.window.geometry("1180x720")
        self.window.minsize(1024, 640)

        self.ip = tk.StringVar(value="10.1.133.197")
        self.token = tk.StringVar()
        self.secret = tk.StringVar()
        self.dry_run = tk.BooleanVar(value=True)
        self.theme = tk.StringVar(value=DEFAULT_THEME)

        self.status_var = tk.StringVar(value="Pronto")

        if ScrolledText is not None:
            self.log_widget = ScrolledText(self.window, height=14, autohide=True, bootstyle="dark")
        else:  # pragma: no cover - fallback to standard Text widget
            self.log_widget = tk.Text(self.window, height=14, wrap="word")
        self.table = ttk.Treeview(self.window, columns=TABLE_COLUMNS, show="headings")
        self._build_ui()
        self._load_env()
        self._load_settings()
        self.window.protocol("WM_DELETE_WINDOW", self._on_close)

    # ------------------------------------------------------------------
    # UI helpers
    # ------------------------------------------------------------------
    def _build_ui(self) -> None:
        container = tb.Frame(self.window, padding=15)
        container.pack(fill="both", expand=True)

        top = tb.Labelframe(container, text="Connessione", padding=(15, 10))
        top.pack(fill="x")

        grid_opts = {"padx": 6, "pady": 4, "sticky": "ew"}
        top.columnconfigure((1, 3, 5), weight=1)

        tb.Label(top, text="Raybox IP").grid(row=0, column=0, sticky="w", padx=(0, 6))
        tb.Entry(top, textvariable=self.ip).grid(row=0, column=1, **grid_opts)
        tb.Label(top, text="TOKEN").grid(row=0, column=2, sticky="w", padx=(10, 6))
        tb.Entry(top, textvariable=self.token, show="•").grid(row=0, column=3, **grid_opts)
        tb.Label(top, text="SECRET").grid(row=0, column=4, sticky="w", padx=(10, 6))
        tb.Entry(top, textvariable=self.secret, show="•").grid(row=0, column=5, **grid_opts)

        controls = tb.Frame(top)
        controls.grid(row=0, column=6, padx=(10, 0), sticky="e")
        tb.Checkbutton(controls, text="Dry-run", variable=self.dry_run, bootstyle="round-toggle").pack(side="left", padx=(0, 6))
        tb.Button(controls, text="Test connessione", bootstyle="info-outline", command=self.test_conn).pack(side="left")

        theme_frame = tb.Frame(top)
        theme_frame.grid(row=1, column=0, columnspan=7, sticky="ew")
        tb.Label(theme_frame, text="Tema").pack(side="left")
        theme_selector = tb.Combobox(
            theme_frame,
            textvariable=self.theme,
            values=sorted(tb.Style().theme_names()),
            state="readonly",
            width=18,
        )
        theme_selector.pack(side="left", padx=8)
        theme_selector.bind("<<ComboboxSelected>>", self._on_theme_change)

        main_paned = tb.Panedwindow(container, orient="vertical", bootstyle="light")
        main_paned.pack(fill="both", expand=True, pady=(15, 0))

        log_frame = tb.Labelframe(main_paned, text="Log", padding=10)
        if hasattr(main_paned, "add"):
            main_paned.add(log_frame, weight=2)
        else:  # pragma: no cover - ttk fallback
            log_frame.pack(fill="both", expand=True)
        self.log_widget.pack(in_=log_frame, fill="both", expand=True)

        table_frame = tb.Labelframe(main_paned, text="Storico attività", padding=10)
        if hasattr(main_paned, "add"):
            main_paned.add(table_frame, weight=3)
        else:  # pragma: no cover - ttk fallback
            table_frame.pack(fill="both", expand=True, pady=(10, 0))

        style = tb.Style()
        style.configure("Treeview", rowheight=28)
        style.map("Treeview", background=[("selected", style.colors.primary)])

        for column in TABLE_COLUMNS:
            self.table.heading(column, text=column.capitalize())
            self.table.column(column, width=160, anchor="center")
        self.table.tag_configure("oddrow", background=style.colors.dark)
        self.table.tag_configure("evenrow", background=style.colors.light)
        self.table.pack(in_=table_frame, fill="both", expand=True)

        btns = tb.Frame(container)
        btns.pack(fill="x", pady=(12, 0))
        tb.Button(btns, text="Esporta CSV", bootstyle="success", command=self.export_csv).pack(side="left", padx=5)
        tb.Button(btns, text="Esporta JSON", bootstyle="secondary", command=self.export_json).pack(side="left", padx=5)

        status_bar = tb.Frame(self.window, bootstyle="dark")
        status_bar.pack(fill="x", side="bottom")
        tb.Label(status_bar, textvariable=self.status_var, padding=6, bootstyle="inverse-dark").pack(anchor="w")

    def _load_env(self) -> None:
        if not ENV_PATH.exists():
            return
        env_data: MutableMapping[str, str] = {}
        with ENV_PATH.open("r", encoding="utf-8") as handle:
            for line in handle:
                if not line.strip() or line.strip().startswith("#"):
                    continue
                if "=" not in line:
                    continue
                key, value = line.rstrip().split("=", 1)
                env_data[key.strip()] = value.strip()
        self.ip.set(env_data.get("RAYBOX_IP", self.ip.get()))
        self.token.set(env_data.get("RAYBOX_TOKEN", self.token.get()))
        self.secret.set(env_data.get("RAYBOX_SECRET", self.secret.get()))

    def _load_settings(self) -> None:
        settings_file = config_path()
        try:
            with settings_file.open("r", encoding="utf-8") as handle:
                data = json.load(handle)
        except FileNotFoundError:
            return
        except Exception as exc:  # pragma: no cover - configuration errors
            self.log(f"⚠️ Impossibile leggere le impostazioni: {exc}")
            return

        self.ip.set(data.get("ip", self.ip.get()))
        self.token.set(data.get("token", self.token.get()))
        self.secret.set(data.get("secret", self.secret.get()))
        theme = data.get("theme")
        if theme and theme in tb.Style().theme_names():
            self.theme.set(theme)
            tb.Style().theme_use(theme)

    def _save_settings(self) -> None:
        settings_file = config_path()
        settings_file.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "ip": self.ip.get().strip(),
            "token": self.token.get().strip(),
            "secret": self.secret.get().strip(),
            "theme": self.theme.get(),
        }
        try:
            with settings_file.open("w", encoding="utf-8") as handle:
                json.dump(data, handle, ensure_ascii=False, indent=2)
        except Exception as exc:  # pragma: no cover - disk errors
            self.log(f"⚠️ Impossibile salvare le impostazioni: {exc}")

    def _on_theme_change(self, *_: Any) -> None:
        new_theme = self.theme.get()
        try:
            tb.Style().theme_use(new_theme)
            self.status_var.set(f"Tema applicato: {new_theme}")
        except Exception as exc:  # pragma: no cover - invalid theme name
            self.log(f"⚠️ Tema non disponibile: {exc}")

    # ------------------------------------------------------------------
    # Actions
    # ------------------------------------------------------------------
    def run(self) -> None:
        self.window.mainloop()

    def log(self, message: str) -> None:
        self.log_widget.insert("end", message + "\n")
        self.log_widget.see("end")
        self.status_var.set(message)

    def test_conn(self) -> None:
        threading.Thread(target=self._test_conn_worker, daemon=True).start()

    def _test_conn_worker(self) -> None:
        ip_value = self.ip.get().strip()
        if not ip_value:
            self.log("⚠️ Inserisci IP.")
            return

        self.log(f"🔌 Test connessione a {ip_value}...")
        if not tcp_check(ip_value, DEFAULT_PORT):
            self.log("❌ Porta 8080 non raggiungibile.")
            self.status_var.set("Porta 8080 non raggiungibile")
            return

        self.log("✅ Porta 8080 OK. Provo /api/time...")
        try:
            response = requests.get(f"http://{ip_value}:{DEFAULT_PORT}/api/time", timeout=6)
            response.raise_for_status()
            self.log("⏱ " + json.dumps(response.json(), indent=2, ensure_ascii=False))
        except Exception as exc:
            self.log(f"⚠️ /api/time errore: {exc}")

        try:
            credentials = RayboxCredentials(self.token.get().strip(), self.secret.get().strip())
            if not credentials.valid():
                raise RuntimeError("Token o secret mancanti.")
            request = RayboxRequest(f"http://{ip_value}:{DEFAULT_PORT}", credentials)
            if self.dry_run.get():
                payload: Mapping[str, Any] = {
                    "status": "dry-run",
                    "msg": "simulazione attiva",
                    "url": f"{request.base_url}/api/datacenter/list",
                    "method": "GET",
                }
            else:
                payload = self._do_request("GET", f"{request.base_url}/api/datacenter/list", request.headers())
            self.log(json.dumps(payload, indent=2, ensure_ascii=False))
            self.status_var.set("Test completato")
        except Exception as exc:
            self.log(f"⚠️ Auth fallita: {exc}")

    def _do_request(
        self,
        method: str,
        url: str,
        headers: Mapping[str, str],
        *,
        params: Mapping[str, Any] | None = None,
        json_body: Mapping[str, Any] | None = None,
        files: Mapping[str, Any] | None = None,
        timeout: float = 15,
    ) -> Mapping[str, Any]:
        response = requests.request(
            method,
            url,
            headers=headers,
            params=params,
            json=json_body,
            files=files,
            timeout=timeout,
        )
        response.raise_for_status()
        try:
            data: Mapping[str, Any] = response.json()
        except ValueError as exc:  # pragma: no cover - error propagation
            raise RuntimeError(f"Risposta non-JSON: {response.text[:600]}") from exc
        if isinstance(data, Mapping) and data.get("status") not in (0, "dry-run", None):
            raise RuntimeError(f"Errore Raybox: {data.get('msg')}")
        return data

    def export_csv(self) -> None:
        rows = self.table.get_children()
        if not rows:
            messagebox.showinfo(APP_TITLE, "Nessun dato da esportare.")
            return
        path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV", "*.csv")])
        if not path:
            return
        with open(path, "w", newline="", encoding="utf-8") as handle:
            writer = csv.writer(handle)
            writer.writerow([column.upper() for column in TABLE_COLUMNS])
            for row_id in rows:
                writer.writerow(self.table.item(row_id)["values"])
        self.log(f"💾 Esportato CSV: {path}")

    def export_json(self) -> None:
        rows = self.table.get_children()
        if not rows:
            messagebox.showinfo(APP_TITLE, "Nessun dato da esportare.")
            return
        path = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON", "*.json")])
        if not path:
            return
        data = [dict(zip(TABLE_COLUMNS, self.table.item(row_id)["values"])) for row_id in rows]
        with open(path, "w", encoding="utf-8") as handle:
            json.dump(data, handle, ensure_ascii=False, indent=2)
        self.log(f"💾 Esportato JSON: {path}")

    def _on_close(self) -> None:
        self._save_settings()
        self.window.destroy()


def main() -> None:
    app = RayboxApp()
    app.run()


if __name__ == "__main__":  # pragma: no cover - GUI entry point
    main()
