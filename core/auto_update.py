from __future__ import annotations

import json
import re
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.parse import urlparse
from urllib.error import HTTPError, URLError
from urllib.request import urlopen


class UpdateCheckError(Exception):
    pass


class UpdateInstallError(Exception):
    pass


@dataclass
class UpdateInfo:
    version: str
    download_url: str
    notes: str


def resolve_metadata_url(metadata_url: str, github_repo: str, github_branch: str = "main") -> str:
    if metadata_url.strip():
        return metadata_url.strip()

    repo = github_repo.strip().strip("/")
    if not repo:
        return ""

    branch = github_branch.strip() or "main"
    return f"https://raw.githubusercontent.com/{repo}/{branch}/update/latest.json"


def _parse_version(version: str) -> tuple[int, ...]:
    chunks = version.split(".")
    parsed: list[int] = []
    for chunk in chunks:
        match = re.search(r"\d+", chunk)
        parsed.append(int(match.group(0)) if match else 0)
    return tuple(parsed)


def _is_newer_version(remote: str, current: str) -> bool:
    remote_parts = list(_parse_version(remote))
    current_parts = list(_parse_version(current))

    length = max(len(remote_parts), len(current_parts))
    remote_parts.extend([0] * (length - len(remote_parts)))
    current_parts.extend([0] * (length - len(current_parts)))

    return tuple(remote_parts) > tuple(current_parts)


def _fetch_json(url: str, timeout: float = 4.0) -> dict[str, Any]:
    try:
        with urlopen(url, timeout=timeout) as response:
            payload = response.read().decode("utf-8")
    except URLError as exc:
        raise UpdateCheckError(f"No se pudo consultar actualizaciones: {exc}") from exc

    try:
        data = json.loads(payload)
    except json.JSONDecodeError as exc:
        raise UpdateCheckError("La respuesta de actualizacion no es JSON valido.") from exc

    if not isinstance(data, dict):
        raise UpdateCheckError("El JSON de actualizacion debe ser un objeto.")

    return data


def check_for_update(current_version: str, metadata_url: str) -> UpdateInfo | None:
    if not metadata_url:
        return None

    data = _fetch_json(metadata_url)
    remote_version = str(data.get("version", "")).strip()
    download_url = str(data.get("download_url", "")).strip()

    if not remote_version or not download_url:
        raise UpdateCheckError(
            "El JSON de actualizacion debe incluir version y download_url."
        )

    if not _is_newer_version(remote_version, current_version):
        return None

    notes = str(data.get("notes", "")).strip()
    return UpdateInfo(version=remote_version, download_url=download_url, notes=notes)


def _candidate_download_urls(download_url: str) -> list[str]:
    parsed = urlparse(download_url)
    path = parsed.path or ""
    parts = path.split("/")

    # Expected path: /owner/repo/releases/download/<tag>/<file>
    if len(parts) < 7 or parts[4] != "download":
        return [download_url]

    tag = parts[5]
    if not tag:
        return [download_url]

    tag_variants = [tag]
    raw = tag[1:] if tag[:1].lower() == "v" else tag
    for candidate in (raw, f"v{raw}", f"V{raw}"):
        if candidate and candidate not in tag_variants:
            tag_variants.append(candidate)

    urls: list[str] = []
    for variant in tag_variants:
        variant_parts = list(parts)
        variant_parts[5] = variant
        variant_path = "/".join(variant_parts)
        rebuilt = parsed._replace(path=variant_path).geturl()
        if rebuilt not in urls:
            urls.append(rebuilt)

    return urls


def download_update_installer(download_url: str, app_name: str, version: str) -> Path:
    parsed = urlparse(download_url)
    guessed_name = Path(parsed.path).name if parsed.path else ""
    if guessed_name.lower().endswith(".exe"):
        file_name = guessed_name
    else:
        safe_app_name = re.sub(r"[^A-Za-z0-9_-]", "", app_name) or "App"
        file_name = f"{safe_app_name}Setup_{version}.exe"

    target_dir = Path(tempfile.gettempdir()) / "PrimalGestionUpdates"
    target_dir.mkdir(parents=True, exist_ok=True)
    target_path = target_dir / file_name

    last_exc: Exception | None = None
    data = b""
    for candidate_url in _candidate_download_urls(download_url):
        try:
            with urlopen(candidate_url, timeout=15) as response:
                data = response.read()
            break
        except (HTTPError, URLError) as exc:
            last_exc = exc

    if not data and last_exc is not None:
        raise UpdateInstallError(f"No se pudo descargar la actualizacion: {last_exc}") from last_exc

    if not data:
        raise UpdateInstallError("La descarga de actualizacion llego vacia.")

    target_path.write_bytes(data)
    return target_path
