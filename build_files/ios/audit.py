#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 Blender Authors
#
# SPDX-License-Identifier: GPL-2.0-or-later

"""Static contract, ABI, and bundle audits for the Blender iOS port."""

from __future__ import annotations

import argparse
import csv
from dataclasses import asdict, dataclass
import json
from pathlib import Path
import plistlib
import re
import subprocess
import sys
from typing import Iterable, Sequence


SHA_PATTERN = re.compile(r"^[0-9a-f]{40}$")
RUN_ID_PATTERN = re.compile(r"^\d{8}T\d{6}Z-[0-9a-f]{7,40}-[a-z0-9-]+$")
PRIVATE_PATH_PATTERNS = (
    ("PATH-PRIVATE", re.compile(r"/Users/[^/\s]+/"), "private user path"),
    ("PATH-TEMP", re.compile(r"/var/folders/[^\s\"']+"), "ephemeral macOS path"),
)
SIGNING_NAMES = {"_CodeSignature", "embedded.mobileprovision"}
SIGNING_KEYS = {
    "ApplicationIdentifier",
    "CodeSignIdentity",
    "DEVELOPMENT_TEAM",
    "DevelopmentTeam",
    "ProvisioningProfile",
    "PROVISIONING_PROFILE_SPECIFIER",
}
PORT_MAP_FIELDS = (
    "path",
    "change",
    "packet",
    "action",
    "owner_tier",
    "status",
    "test",
    "notes",
)


@dataclass(frozen=True)
class Finding:
    code: str
    message: str
    path: str


def run_tool(command: Sequence[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, check=False, capture_output=True, text=True)


def add_finding(findings: list[Finding], code: str, message: str, path: Path) -> None:
    findings.append(Finding(code, message, str(path)))


def audit_manifest(path: Path) -> list[Finding]:
    findings: list[Finding] = []
    try:
        document = json.loads(path.read_text())
    except (OSError, UnicodeError, json.JSONDecodeError) as ex:
        add_finding(findings, "MANIFEST-JSON", f"cannot load JSON: {ex}", path)
        return findings

    required_types: dict[str, type] = {
        "schema_version": int,
        "run_id": str,
        "packet": str,
        "baseline_sha": str,
        "donor_sha": str,
        "target": str,
        "feature_profile": str,
        "signing_mode": str,
        "paths": dict,
    }
    for key, expected_type in required_types.items():
        if key not in document or not isinstance(document[key], expected_type):
            add_finding(
                findings,
                "MANIFEST-SCHEMA",
                f"{key!r} must be present as {expected_type.__name__}",
                path,
            )

    for key in ("baseline_sha", "donor_sha"):
        value = document.get(key)
        if isinstance(value, str) and not SHA_PATTERN.fullmatch(value):
            add_finding(findings, "MANIFEST-SCHEMA", f"{key!r} must be a full SHA-1", path)

    run_id = document.get("run_id")
    if isinstance(run_id, str) and not RUN_ID_PATTERN.fullmatch(run_id):
        add_finding(findings, "MANIFEST-SCHEMA", "run_id has an invalid format", path)

    if document.get("target") not in {"ios-simulator-arm64", "ios-device-arm64"}:
        add_finding(findings, "MANIFEST-SCHEMA", "target is not an iOS lane", path)
    if document.get("signing_mode") not in {"SIMULATOR_LOCAL", "UNSIGNED"}:
        add_finding(findings, "MANIFEST-SCHEMA", "signing_mode is invalid", path)

    paths = document.get("paths")
    if isinstance(paths, dict):
        for key in ("source", "bulk", "artifact"):
            if not isinstance(paths.get(key), str) or not paths[key].startswith("/"):
                add_finding(
                    findings,
                    "MANIFEST-SCHEMA",
                    f"paths.{key} must be an absolute path",
                    path,
                )
        for key in ("bulk", "artifact"):
            value = paths.get(key)
            if isinstance(value, str) and not value.startswith(
                "/Volumes/BlenderBuild/blender-ios"
            ):
                add_finding(
                    findings,
                    "MANIFEST-STORAGE",
                    f"paths.{key} is outside the canonical bulk root",
                    path,
                )
    return findings


def candidate_text_files(paths: Iterable[Path]) -> Iterable[Path]:
    for path in paths:
        if path.is_dir():
            for child in path.rglob("*"):
                if child.is_file() and not child.is_symlink() and child.stat().st_size <= 5_000_000:
                    yield child
        elif path.is_file() and path.stat().st_size <= 5_000_000:
            yield path


def audit_paths(paths: Sequence[Path]) -> list[Finding]:
    findings: list[Finding] = []
    for path in candidate_text_files(paths):
        try:
            contents = path.read_text(errors="strict")
        except (OSError, UnicodeError):
            continue
        for code, pattern, description in PRIVATE_PATH_PATTERNS:
            match = pattern.search(contents)
            if match:
                add_finding(
                    findings,
                    code,
                    f"contains {description}: {match.group(0)}",
                    path,
                )
    return findings


def audit_bundle(bundle: Path, lane: str, required_resources: Sequence[str]) -> list[Finding]:
    findings: list[Finding] = []
    if not bundle.is_dir():
        add_finding(findings, "BUNDLE-MISSING", "bundle directory does not exist", bundle)
        return findings

    plist_path = bundle / "Info.plist"
    plist: dict[str, object] = {}
    if not plist_path.is_file():
        add_finding(findings, "BUNDLE-PLIST-MISSING", "Info.plist is missing", plist_path)
    else:
        try:
            with plist_path.open("rb") as handle:
                plist = plistlib.load(handle)
        except (OSError, plistlib.InvalidFileException) as ex:
            add_finding(findings, "BUNDLE-PLIST-INVALID", f"cannot parse plist: {ex}", plist_path)

    for key in ("CFBundleIdentifier", "CFBundleExecutable", "CFBundlePackageType"):
        if not plist.get(key):
            add_finding(findings, "BUNDLE-PLIST-KEY", f"missing required key {key}", plist_path)

    executable = plist.get("CFBundleExecutable")
    if isinstance(executable, str) and not (bundle / executable).is_file():
        add_finding(
            findings,
            "BUNDLE-EXECUTABLE-MISSING",
            f"declared executable {executable!r} is missing",
            bundle / executable,
        )

    for resource in required_resources:
        resource_path = bundle / resource
        if not resource_path.exists():
            add_finding(
                findings,
                "BUNDLE-RESOURCE-MISSING",
                f"required resource {resource!r} is missing",
                resource_path,
            )

    if lane == "device-unsigned":
        for child in bundle.rglob("*"):
            if child.name in SIGNING_NAMES:
                add_finding(
                    findings,
                    "SIGN-CONTAMINATION",
                    f"unsigned lane contains {child.name}",
                    child,
                )
        for key in sorted(SIGNING_KEYS.intersection(plist)):
            add_finding(
                findings,
                "SIGN-CONTAMINATION",
                f"unsigned lane plist contains signing key {key}",
                plist_path,
            )
    return findings


def macho_candidates(path: Path) -> Iterable[Path]:
    if path.is_file():
        yield path
        return
    if path.is_dir():
        for child in path.rglob("*"):
            if child.is_file() and not child.is_symlink():
                file_result = run_tool(["/usr/bin/file", "-b", str(child)])
                if "Mach-O" in file_result.stdout or "current ar archive" in file_result.stdout:
                    yield child


def audit_abi(path: Path, target: str, architecture: str) -> list[Finding]:
    findings: list[Finding] = []
    expected_platform = {"ios-simulator": "IOSSIMULATOR", "ios-device": "IOS"}[target]
    candidates = list(macho_candidates(path))
    if not candidates:
        add_finding(findings, "ABI-NOT-MACHO", "no Mach-O input was found", path)
        return findings

    for binary in candidates:
        arch_result = run_tool(["xcrun", "lipo", "-archs", str(binary)])
        architectures = set(arch_result.stdout.split()) if arch_result.returncode == 0 else set()
        if architecture not in architectures:
            add_finding(
                findings,
                "ABI-ARCH",
                f"expected {architecture}; found {sorted(architectures) or 'unknown'}",
                binary,
            )

        platform_result = run_tool(["xcrun", "vtool", "-show-build", str(binary)])
        platforms = set(re.findall(r"^\s*platform\s+(\S+)", platform_result.stdout, re.MULTILINE))
        if expected_platform not in platforms:
            add_finding(
                findings,
                "ABI-PLATFORM",
                f"expected {expected_platform}; found {sorted(platforms) or 'unknown'}",
                binary,
            )
        unexpected = platforms.difference({expected_platform})
        if unexpected:
            add_finding(
                findings,
                "ABI-PLATFORM-MIXED",
                f"contains unexpected platforms {sorted(unexpected)}",
                binary,
            )
    return findings


def donor_paths(repository: Path, base: str, donor: str) -> tuple[set[str], str | None]:
    result = run_tool(
        ["git", "-C", str(repository), "diff", "--name-only", f"{base}..{donor}"]
    )
    if result.returncode != 0:
        return set(), result.stderr.strip() or "git diff failed"
    return {line for line in result.stdout.splitlines() if line}, None


def audit_port_map(path: Path, repository: Path, base: str, donor: str) -> list[Finding]:
    findings: list[Finding] = []
    try:
        with path.open(newline="") as handle:
            reader = csv.DictReader(handle, delimiter="\t")
            if tuple(reader.fieldnames or ()) != PORT_MAP_FIELDS:
                add_finding(
                    findings,
                    "PORT-MAP-SCHEMA",
                    f"header must be {PORT_MAP_FIELDS}",
                    path,
                )
            rows = list(reader)
    except OSError as ex:
        add_finding(findings, "PORT-MAP-READ", f"cannot read map: {ex}", path)
        return findings

    expected, error = donor_paths(repository, base, donor)
    if error:
        add_finding(findings, "PORT-MAP-DIFF", error, repository)
        return findings

    mapped: set[str] = set()
    for row_number, row in enumerate(rows, start=2):
        row_path = row.get("path", "")
        if row_path in mapped:
            add_finding(
                findings,
                "PORT-MAP-DUPLICATE",
                f"row {row_number} duplicates {row_path!r}",
                path,
            )
        mapped.add(row_path)
        for field in PORT_MAP_FIELDS:
            if not row.get(field, "").strip():
                add_finding(
                    findings,
                    "PORT-MAP-UNCLASSIFIED",
                    f"row {row_number} has an empty {field!r}",
                    path,
                )
        if row.get("action") not in {"reuse", "adapt", "rewrite", "drop", "defer"}:
            add_finding(
                findings,
                "PORT-MAP-UNCLASSIFIED",
                f"row {row_number} has invalid action {row.get('action')!r}",
                path,
            )
        if row.get("owner_tier") not in {"S", "M", "F"}:
            add_finding(
                findings,
                "PORT-MAP-UNCLASSIFIED",
                f"row {row_number} has invalid owner tier {row.get('owner_tier')!r}",
                path,
            )

    missing = sorted(expected.difference(mapped))
    extra = sorted(mapped.difference(expected))
    if missing:
        add_finding(
            findings,
            "PORT-MAP-MISSING",
            f"{len(missing)} donor paths are missing; first: {missing[:5]}",
            path,
        )
    if extra:
        add_finding(
            findings,
            "PORT-MAP-EXTRA",
            f"{len(extra)} paths are outside the donor delta; first: {extra[:5]}",
            path,
        )
    return findings


def parse_arguments(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    manifest_parser = subparsers.add_parser("manifest")
    manifest_parser.add_argument("path", type=Path)

    path_parser = subparsers.add_parser("paths")
    path_parser.add_argument("paths", nargs="+", type=Path)

    bundle_parser = subparsers.add_parser("bundle")
    bundle_parser.add_argument("path", type=Path)
    bundle_parser.add_argument(
        "--lane", choices=("simulator", "device-unsigned"), default="simulator"
    )
    bundle_parser.add_argument("--required-resource", action="append", default=[])

    abi_parser = subparsers.add_parser("abi")
    abi_parser.add_argument("path", type=Path)
    abi_parser.add_argument("--target", choices=("ios-simulator", "ios-device"), required=True)
    abi_parser.add_argument("--arch", default="arm64")

    port_map_parser = subparsers.add_parser("port-map")
    port_map_parser.add_argument("path", type=Path)
    port_map_parser.add_argument("--repository", type=Path, required=True)
    port_map_parser.add_argument("--base", required=True)
    port_map_parser.add_argument("--donor", required=True)
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    arguments = parse_arguments(sys.argv[1:] if argv is None else argv)
    if arguments.command == "manifest":
        findings = audit_manifest(arguments.path)
    elif arguments.command == "paths":
        findings = audit_paths(arguments.paths)
    elif arguments.command == "bundle":
        findings = audit_bundle(arguments.path, arguments.lane, arguments.required_resource)
    elif arguments.command == "abi":
        findings = audit_abi(arguments.path, arguments.target, arguments.arch)
    else:
        findings = audit_port_map(
            arguments.path, arguments.repository, arguments.base, arguments.donor
        )

    report = {
        "schema_version": 1,
        "audit": arguments.command,
        "ok": not findings,
        "findings": [asdict(finding) for finding in findings],
    }
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if not findings else 1


if __name__ == "__main__":
    sys.exit(main())
