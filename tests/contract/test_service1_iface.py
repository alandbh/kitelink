"""Contract tests: D-Bus Service1 interface method presence."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CONTRACT = ROOT / "specs/001-kitelink-mvp/contracts/dbus-org.kitelink.Service1.xml"
IPC = ROOT / "src/kitelink/ipc/service1.py"

REQUIRED_METHODS = [
    "GetAuthStatus",
    "StartSignIn",
    "SignOut",
    "GetConnectionStatus",
    "OpenMountpoint",
    "RestartConnection",
    "GetPathState",
    "GetAggregatedTransfers",
    "GetPreferences",
    "SetPreferences",
    "GetDiagnostics",
]

REQUIRED_SIGNALS = [
    "StatusChanged",
    "TransfersChanged",
    "PathStateMayHaveChanged",
]


def test_contract_xml_lists_required_methods() -> None:
    xml = CONTRACT.read_text(encoding="utf-8")
    for name in REQUIRED_METHODS:
        assert f'name="{name}"' in xml


def test_contract_xml_lists_required_signals() -> None:
    xml = CONTRACT.read_text(encoding="utf-8")
    for name in REQUIRED_SIGNALS:
        assert f'name="{name}"' in xml


def test_ipc_introspection_matches_contract_methods() -> None:
    src = IPC.read_text(encoding="utf-8")
    for name in REQUIRED_METHODS + REQUIRED_SIGNALS:
        assert name in src
