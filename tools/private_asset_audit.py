#!/usr/bin/env python3
"""Privacy-preserving PRIVATE asset risk inventory (not legal adjudication).

Usage: python tools/private_asset_audit.py
Does not upload, copy, rewrite or log image/text payloads or EXIF values.
Stdout contains ONLY aggregate counters, generic boolean flags, and warning codes.
The existence of metadata is not proof of sensitive content or a release defect.
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

from PIL import Image, UnidentifiedImageError

ROOT = Path(__file__).resolve().parents[1]
PROJECT = "AIGC/项目-01-角色视觉资产/"
IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".webp", ".tif", ".tiff"}
BINARY_EXT = IMAGE_SUFFIXES | {".ora", ".psd", ".moc3", ".cmo3"}
FORBIDDEN_FILENAME = re.compile(
    r"(^|/)(?:\.env(?:\.[^/]*)?|id_rsa|id_ed25519|local\.env|credentials\.json|"
    r"secret(?:s)?\.json|private[-_]key(?:\.[^/]*)?)$", re.I)
CREDENTIAL_PATTERNS = [
    re.compile(rb"gh[pousr]_[A-Za-z0-9]{30,}"),
    re.compile(rb"sk-[A-Za-z0-9_\-]{30,}"),
    re.compile(rb"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    re.compile(rb"AKIA[0-9A-Z]{16}"),
]
TEXT_SUFFIXES = {".md", ".txt", ".yml", ".yaml", ".py", ".js", ".html", ".json", ".toml", ".ps1", ".xml", ".csv"}

def tracked_files() -> list[str]:
    data = subprocess.check_output(["git", "-C", str(ROOT), "ls-files", "-z"])
    return [p.decode("utf-8", "surrogateescape") for p in data.split(b"\0") if p]

def inspect_image(path: Path) -> tuple[bool, bool]:
    # Returns metadata-present flags, never values.
    with Image.open(path) as img:
        metadata = False
        try:
            exif = img.getexif()
            metadata = bool(exif)
        except (OSError, ValueError):
            metadata = True  # unreadable metadata requires manual inspection
        keys = {str(k).lower() for k in img.info.keys()}
        textual = any("exif" in k or "xmp" in k or "comment" in k or
                      "description" in k or "xml" in k or k.startswith("text")
                      for k in keys)
        return metadata, textual

def scan():
    paths = tracked_files()
    stats = {
        "audit_kind": "private_repository_internal_risk_inventory",
        "legal_clearance_issued": False,
        "public_distribution_authorized": False,
        "source_images_tracked": 0,
        "derived_images_tracked": 0,
        "editable_ora_psd_tracked": 0,
        "images_with_exif_or_xmp_risk": 0,
        "images_with_other_textual_metadata_risk": 0,
        "unreadable_or_invalid_images": 0,
        "suspected_tracked_credentials": 0,
        "remote_js_reference_present": False,
        "optional_external_llm_code_present": False,
        "has_open_source_license_file": False,
        "warnings": []
    }
    for rel in paths:
        p = ROOT / rel
        suffix = p.suffix.lower()
        if suffix in IMAGE_SUFFIXES:
            if rel.startswith(PROJECT + "人物设定-1/"):
                stats["source_images_tracked"] += 1
            elif rel.startswith(PROJECT + "Live2D-开发中/"):
                stats["derived_images_tracked"] += 1
            try:
                exif, textual = inspect_image(p)
                stats["images_with_exif_or_xmp_risk"] += int(exif)
                stats["images_with_other_textual_metadata_risk"] += int(textual)
            except (OSError, UnidentifiedImageError, ValueError):
                stats["unreadable_or_invalid_images"] += 1
        elif suffix in {".ora", ".psd"}:
            stats["editable_ora_psd_tracked"] += 1
        if rel.upper() in {"LICENSE", "LICENSE.MD", "LICENSE.TXT", "COPYING"}:
            stats["has_open_source_license_file"] = True
        if FORBIDDEN_FILENAME.search(rel):
            stats["suspected_tracked_credentials"] += 1
        elif suffix in TEXT_SUFFIXES and p.is_file() and p.stat().st_size < 2_000_000:
            # Only scan candidate credential literals and never print their contents.
            try:
                body = p.read_bytes()
                if any(pattern.search(body) for pattern in CREDENTIAL_PATTERNS):
                    stats["suspected_tracked_credentials"] += 1
                if rel.endswith("/viewer.html") and b"cdn.jsdelivr.net" in body:
                    stats["remote_js_reference_present"] = True
                if rel.endswith("/deepseek_client.py"):
                    stats["optional_external_llm_code_present"] = True
            except OSError:
                stats["warnings"].append("unreadable_text_file")
    if stats["source_images_tracked"] < 1:
        stats["warnings"].append("missing_source_image")
    if stats["images_with_exif_or_xmp_risk"] or stats["images_with_other_textual_metadata_risk"]:
        stats["warnings"].append("metadata_review_needed_before_release")
    if stats["remote_js_reference_present"]:
        stats["warnings"].append("remote_javascript_not_strictly_offline")
    if stats["optional_external_llm_code_present"]:
        stats["warnings"].append("cloud_llm_must_be_opt_in")
    if not stats["has_open_source_license_file"]:
        stats["warnings"].append("no_open_license_intended")
    if stats["suspected_tracked_credentials"]:
        stats["warnings"].append("potential_credentials_block_release")
    # Report only aggregate numbers. This program never writes binary copies or uploads results.
    print(json.dumps(stats, ensure_ascii=False, indent=2))
    return 2 if stats["suspected_tracked_credentials"] or stats["unreadable_or_invalid_images"] else 0

if __name__ == "__main__":
    sys.exit(scan())
