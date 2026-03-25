from __future__ import annotations

import os
import sys
from pathlib import Path

APP_DIR_NAME = "PrimalGestion"


def get_project_root() -> Path:
    return Path(__file__).resolve().parent.parent


def get_bundle_root() -> Path:
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        return Path(sys._MEIPASS)
    return get_project_root()


def get_resource_path(*parts: str) -> Path:
    return get_bundle_root().joinpath(*parts)


def get_user_data_dir() -> Path:
    local_appdata = os.environ.get("LOCALAPPDATA")
    if local_appdata:
        data_dir = Path(local_appdata) / APP_DIR_NAME
    else:
        data_dir = Path.home() / f".{APP_DIR_NAME}"

    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir


def get_medical_files_dir() -> Path:
    medical_dir = get_user_data_dir() / "medical_files"
    medical_dir.mkdir(parents=True, exist_ok=True)
    return medical_dir


def get_desktop_dir() -> Path:
    user_profile = os.environ.get("USERPROFILE")
    if user_profile:
        desktop = Path(user_profile) / "Desktop"
    else:
        desktop = Path.home() / "Desktop"

    desktop.mkdir(parents=True, exist_ok=True)
    return desktop
