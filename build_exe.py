#!/usr/bin/env python3
"""Utility script per creare l'eseguibile Windows della Raybox GUI."""

from __future__ import annotations

import shutil
import sys
from pathlib import Path


def main() -> None:
    try:
        import PyInstaller.__main__ as pyinstaller
    except ModuleNotFoundError as exc:  # pragma: no cover - richiede PyInstaller
        raise SystemExit(
            "PyInstaller non è installato. Esegui 'pip install pyinstaller' e riprova."
        ) from exc

    project_root = Path(__file__).resolve().parent
    dist_dir = project_root / "dist"
    build_dir = project_root / "build"
    spec_file = project_root / "RayboxControlCenter.spec"

    for path in (dist_dir, build_dir, spec_file):
        if path.exists():
            if path.is_file():
                path.unlink()
            else:
                shutil.rmtree(path)

    pyinstaller.run(
        [
            "raybox_gui.py",
            "--noconfirm",
            "--onefile",
            "--windowed",
            "--name=RayboxControlCenter",
            "--clean",
        ]
    )

    exe_path = dist_dir / "RayboxControlCenter.exe"
    if exe_path.exists():
        print(f"Eseguibile creato in: {exe_path}")
    else:  # pragma: no cover - messaggio diagnostico
        print("Compilazione completata, ma non è stato trovato l'eseguibile atteso.")


if __name__ == "__main__":
    if sys.platform.startswith("win"):
        main()
    else:
        print(
            "Attenzione: la creazione dell'eseguibile deve essere eseguita su Windows. "
            "Puoi comunque lanciare questo script su Windows per ottenere il file .exe."
        )
