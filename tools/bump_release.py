from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


def update_app_info(app_info_path: Path, version: str, repo: str) -> None:
    text = app_info_path.read_text(encoding="utf-8")
    text = re.sub(r'APP_VERSION\s*=\s*"[^"]+"', f'APP_VERSION = "{version}"', text)
    text = re.sub(r'GITHUB_REPO\s*=\s*"[^"]*"', f'GITHUB_REPO = "{repo}"', text)
    app_info_path.write_text(text, encoding="utf-8")


def update_version_txt(version_txt_path: Path, version: str) -> None:
    major, minor, patch = [int(v) for v in version.split(".")]
    file_ver_tuple = f"({major}, {minor}, {patch}, 0)"
    file_ver_string = f"{major}.{minor}.{patch}.0"

    text = version_txt_path.read_text(encoding="utf-8")
    text = re.sub(r"filevers=\([^\)]+\)", f"filevers={file_ver_tuple}", text)
    text = re.sub(r"prodvers=\([^\)]+\)", f"prodvers={file_ver_tuple}", text)
    text = re.sub(
        r"StringStruct\('FileVersion',\s*'[^']+'\)",
        f"StringStruct('FileVersion', '{file_ver_string}')",
        text,
    )
    text = re.sub(
        r"StringStruct\('ProductVersion',\s*'[^']+'\)",
        f"StringStruct('ProductVersion', '{file_ver_string}')",
        text,
    )
    version_txt_path.write_text(text, encoding="utf-8")


def update_installer_iss(iss_path: Path, version: str) -> None:
    text = iss_path.read_text(encoding="utf-8")
    text = re.sub(
        r'#define\s+MyAppVersion\s+"[^"]+"',
        f'#define MyAppVersion "{version}"',
        text,
    )
    iss_path.write_text(text, encoding="utf-8")


def update_latest_json(latest_json_path: Path, version: str, repo: str, notes: str) -> None:
    data = {
        "version": version,
        "download_url": f"https://github.com/{repo}/releases/download/{version}/PrimalGestionSetup_{version}.exe",
        "notes": notes,
    }
    latest_json_path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Actualiza versionado para release.")
    parser.add_argument("--version", required=True, help="Version semantica, ej: 1.0.2")
    parser.add_argument("--repo", required=True, help="Repo GitHub en formato usuario/repositorio")
    parser.add_argument("--notes", default="Release", help="Notas para latest.json")
    args = parser.parse_args()

    root = Path(__file__).resolve().parents[1]
    update_app_info(root / "core" / "app_info.py", args.version, args.repo)
    update_version_txt(root / "version.txt", args.version)
    update_installer_iss(root / "installer" / "PrimalGestion.iss", args.version)
    update_latest_json(root / "update" / "latest.json", args.version, args.repo, args.notes)

    print(f"Version actualizada a {args.version}")


if __name__ == "__main__":
    main()
