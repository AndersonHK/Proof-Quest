import json
import os
import sys
from pathlib import Path
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "Scripts"))
from build_msi import build_msi, identity, inspect_msi, rows


@pytest.mark.skipif(
    os.name != "nt" or sys.version_info >= (3, 13), reason="Windows msilib builder"
)
def test_msi_has_stable_upgrade_identity_and_does_not_own_user_data(tmp_path):
    import msilib

    stage = tmp_path / "stage"
    icon = stage / "_internal/Assets/Fable/application.ico"
    icon.parent.mkdir(parents=True)
    icon.write_bytes(
        (
            Path(__file__).resolve().parents[1] / "Assets/Fable/application.ico"
        ).read_bytes()
    )
    (stage / "ProofQuest.exe").write_bytes(b"synthetic runtime")
    (stage / "proofquest.ini").write_text("demo defaults")
    names = [
        "ProofQuest.exe",
        "proofquest.ini",
        "_internal/Assets/Fable/application.ico",
    ]
    (stage / "release-manifest.json").write_text(json.dumps({"files": names}))
    package = build_msi(stage, tmp_path / "test.msi", "1.2.3")
    expected = {n: (stage / n).stat().st_size for n in names if n != "proofquest.ini"}
    expected["release-manifest.json"] = (stage / "release-manifest.json").stat().st_size
    receipt = inspect_msi(package, expected, "1.2.3")
    assert receipt["product_code"] == identity("product:1.2.3")
    db = msilib.OpenDatabase(str(package), msilib.MSIDBOPEN_READONLY)
    try:
        assert rows(
            db,
            "SELECT `Sequence` FROM `InstallExecuteSequence` WHERE `Action`='RemoveExistingProducts'",
            [int],
        ) == [(1510,)]
        assert rows(
            db,
            "SELECT `Property` FROM `AppSearch` WHERE `Signature_`='InstallLocation'",
            [str],
        ) == [("SAVEDINSTALLDIR",)]
        components = rows(
            db, "SELECT `Attributes`, `KeyPath` FROM `Component`", [int, str]
        )
        assert all(flags == 260 and key.startswith("R") for flags, key in components)
        assert len(rows(db, "SELECT `UpgradeCode` FROM `Upgrade`", [str])) == 2
    finally:
        db = None
