"""Build a per-user x64 MSI using Windows Python 3.9-3.12's standard msilib."""

import argparse
import gc
import hashlib
import json
import os
import re
import struct
import tempfile
import uuid
from pathlib import Path

from distribution import ARCHIVE_NAME, extract_archive, safe_relative

ROOT = Path(__file__).resolve().parents[1]
MSI_NAME = "ProofQuest-win-x64.msi"
# Fixed across releases: changing this identity would break MSI upgrades.
NAMESPACE = uuid.UUID("308c3b84-9ee2-4a4e-a508-4f3cf693d649")
UPGRADE_CODE = "{" + str(NAMESPACE).upper() + "}"


def identity(name):
    return "{" + str(uuid.uuid5(NAMESPACE, name)).upper() + "}"


def identifier(prefix, name):
    return prefix + hashlib.sha256(name.encode()).hexdigest()[:30]


def msi_api():
    if os.name != "nt" or struct.calcsize("P") != 8:
        raise RuntimeError("MSI builds require 64-bit Windows Python 3.9-3.12.")
    try:
        import msilib
    except ImportError as error:
        raise RuntimeError(
            "Use Windows Python 3.9-3.12 for MSI builds (msilib)."
        ) from error
    return msilib


def rows(db, sql, types):
    view = db.OpenView(sql)
    view.Execute(None)
    result = []
    while True:
        record = view.Fetch()
        if record is None:
            break
        result.append(
            tuple(
                record.GetInteger(i) if kind is int else record.GetString(i)
                for i, kind in enumerate(types, 1)
            )
        )
    view.Close()
    return result


def inspect_msi(path, expected_files=None, version=None):
    msi = msi_api()
    db = msi.OpenDatabase(str(path), msi.MSIDBOPEN_READONLY)
    try:
        props = dict(rows(db, "SELECT `Property`, `Value` FROM `Property`", [str, str]))
        if props.get("UpgradeCode") != UPGRADE_CODE or props.get("ALLUSERS"):
            raise ValueError("MSI identity/context mismatch.")
        if props.get("ProductCode") != identity("product:" + props["ProductVersion"]):
            raise ValueError("MSI product identity mismatch.")
        if version and props["ProductVersion"] != version:
            raise ValueError("MSI version mismatch.")
        directories = {
            key: (parent, name.split("|")[-1])
            for key, parent, name in rows(
                db,
                "SELECT `Directory`, `Directory_Parent`, `DefaultDir` FROM `Directory`",
                [str] * 3,
            )
        }

        def relative(key):
            if key == "INSTALLDIR":
                return ""
            parent, name = directories[key]
            return relative(parent) + name + "/"

        components = dict(
            rows(db, "SELECT `Component`, `Directory_` FROM `Component`", [str, str])
        )
        files = {
            relative(components[component]) + name.split("|")[-1]: size
            for component, name, size in rows(
                db,
                "SELECT `Component_`, `FileName`, `FileSize` FROM `File`",
                [str, str, int],
            )
        }
        if any(name == "proofquest.ini" or name.startswith("Logs/") for name in files):
            raise ValueError("MSI must not manage personal settings/history.")
        if expected_files is not None and files != expected_files:
            raise ValueError(
                "MSI file inventory/sizes differ from the portable bundle."
            )
        return {
            "version": props["ProductVersion"],
            "product_code": props["ProductCode"],
            "files": files,
        }
    finally:
        db = None


def add_ui(msi, db):
    msi.add_data(
        db,
        "TextStyle",
        [("Normal", "Segoe UI", 9, None, 0), ("Heading", "Segoe UI", 14, None, 1)],
    )
    msi.add_data(db, "Property", [("DefaultUIFont", "Normal")])
    welcome = msi.Dialog(
        db,
        "Welcome",
        50,
        50,
        370,
        220,
        3,
        "Proof Quest Setup",
        "Install",
        "Install",
        "Cancel",
    )
    welcome.text("Title", 20, 18, 330, 25, 3, "{\\Heading}Proof Quest")
    welcome.text(
        "Description",
        20,
        57,
        330,
        90,
        3,
        "Install Proof Quest for your Windows account, with its original demo and a Start-menu shortcut.\n\n"
        "Your settings and study history are kept when you update or uninstall.",
    )
    welcome.pushbutton("Install", 215, 180, 65, 20, 3, "Install", "Cancel").event(
        "EndDialog", "Return"
    )
    welcome.pushbutton("Cancel", 285, 180, 65, 20, 3, "Cancel", "Install").event(
        "EndDialog", "Exit"
    )
    for name, message, result in [
        ("ExitDialog", "Proof Quest setup is complete.", "Return"),
        (
            "FatalError",
            "Setup could not finish. No further changes were made. Check the installer log for details.",
            "Exit",
        ),
        ("UserExit", "Setup was cancelled.", "Exit"),
    ]:
        dlg = msi.Dialog(
            db,
            name,
            50,
            50,
            370,
            180,
            3,
            "Proof Quest Setup",
            "Close",
            "Close",
            "Close",
        )
        dlg.text("Message", 20, 30, 330, 90, 3, message)
        dlg.pushbutton("Close", 280, 140, 70, 20, 3, "Close", None).event(
            "EndDialog", result
        )
    msi.add_data(db, "InstallUISequence", [("Welcome", "NOT Installed", 1230)])


def build_msi(staging, destination, version):
    msi = msi_api()
    from msilib import schema, sequence

    if not re.fullmatch(r"\d+\.\d+\.\d+", version):
        raise ValueError("MSI version must have three numeric parts.")
    major, minor, build = map(int, version.split("."))
    if major > 255 or minor > 255 or build > 65535:
        raise ValueError("Version exceeds Windows Installer limits.")
    staging, destination = Path(staging).resolve(), Path(destination).resolve()
    manifest = json.loads(
        (staging / "release-manifest.json").read_text(encoding="utf-8")
    )
    names = sorted(
        (set(manifest["files"]) | {"release-manifest.json"}) - {"proofquest.ini"}
    )
    for name in names:
        safe_relative(name)
        path = staging / name
        if (
            not path.is_file()
            or path.is_symlink()
            or not path.resolve().is_relative_to(staging)
        ):
            raise ValueError("Invalid MSI payload path: " + name)
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_suffix(".msi.tmp")
    db = msi.init_database(
        str(temporary),
        schema,
        "Proof Quest",
        identity("product:" + version),
        version,
        "Anderson Klein",
    )
    summary = db.GetSummaryInformation(20)
    summary.SetProperty(
        msi.PID_WORDCOUNT, 10
    )  # Compressed; no elevated privileges required.
    summary.SetProperty(msi.PID_PAGECOUNT, 500)
    summary.Persist()
    summary = None
    msi.add_tables(db, sequence)
    # Remember a command-line install location for repair/uninstall and upgrades.
    msi.add_data(db, "AppSearch", [("SAVEDINSTALLDIR", "InstallLocation")])
    msi.add_data(
        db,
        "RegLocator",
        [("InstallLocation", 1, "Software\\ProofQuest", "InstallDirectory", 18)],
    )
    msi.add_data(
        db,
        "CustomAction",
        [("RestoreInstallLocation", 51, "INSTALLDIR", "[SAVEDINSTALLDIR]")],
    )
    for table in ("InstallExecuteSequence", "InstallUISequence"):
        msi.add_data(
            db,
            table,
            [("RestoreInstallLocation", "SAVEDINSTALLDIR AND NOT INSTALLDIR", 750)],
        )
    # Remove older versions within the installation transaction, with rollback.
    view = db.OpenView(
        "UPDATE `InstallExecuteSequence` SET `Sequence`=1510 WHERE `Action`='RemoveExistingProducts'"
    )
    view.Execute(None)
    view.Close()
    msi.add_data(
        db,
        "Property",
        [
            ("UpgradeCode", UPGRADE_CODE),
            ("INSTALLLEVEL", "1"),
            ("SecureCustomProperties", "OLDERPRODUCTS;NEWERPRODUCTS"),
            ("ARPPRODUCTICON", "Fable.ico"),
            ("ARPHELPLINK", "https://github.com/AndersonHK/Proof-Quest"),
            ("ARPNOMODIFY", "1"),
        ],
    )
    msi.add_data(
        db,
        "Upgrade",
        [
            (UPGRADE_CODE, None, version, None, 1, None, "OLDERPRODUCTS"),
            (UPGRADE_CODE, version, None, None, 2, None, "NEWERPRODUCTS"),
        ],
    )
    # LaunchConditions normally runs before FindRelatedProducts; move it after.
    for table in ("InstallExecuteSequence", "InstallUISequence"):
        view = db.OpenView(
            f"UPDATE `{table}` SET `Sequence`=250 WHERE `Action`='LaunchConditions'"
        )
        view.Execute(None)
        view.Close()
    msi.add_data(
        db,
        "LaunchCondition",
        [
            ("VersionNT64", "Proof Quest requires 64-bit Windows."),
            ("NOT ALLUSERS", "Proof Quest installs for the current user only."),
            (
                "Installed OR NOT NEWERPRODUCTS",
                "A newer version of Proof Quest is already installed.",
            ),
        ],
    )
    msi.add_data(
        db,
        "Directory",
        [
            ("TARGETDIR", None, "SourceDir"),
            ("LocalAppDataFolder", "TARGETDIR", "."),
            ("Programs", "LocalAppDataFolder", "Programs"),
            ("INSTALLDIR", "Programs", "ProofQuest"),
            ("ProgramMenuFolder", "TARGETDIR", "."),
            ("MenuDir", "ProgramMenuFolder", "ProofQuest"),
        ],
    )
    msi.Feature(
        db, "Main", "Proof Quest", "App and original demo", 1, directory="INSTALLDIR"
    )
    directory_ids = {"": "INSTALLDIR"}
    for folder in sorted({str(Path(name).parent).replace("\\", "/") for name in names}):
        if folder == ".":
            continue
        current = ""
        for part in folder.split("/"):
            parent = current
            current = current + "/" + part if current else part
            if current not in directory_ids:
                key = identifier("D", current)
                directory_ids[current] = key
                # Stable unique 8.3 aliases, including names containing spaces.
                alias = "D" + hashlib.sha256(current.encode()).hexdigest()[:7]
                msi.add_data(
                    db, "Directory", [(key, directory_ids[parent], alias + "|" + part)]
                )
    cab = msi.CAB("Payload.cab")
    exe_component = None
    exe_file = None
    for name in names:
        path = staging / name
        component, file_id, reg_id = (
            identifier(prefix, name) for prefix in ("C", "F", "R")
        )
        folder = path.relative_to(staging).parent.as_posix()
        directory = directory_ids["" if folder == "." else folder]
        msi.add_data(
            db,
            "Component",
            [
                (
                    component,
                    identity("component:x64:" + name),
                    directory,
                    260,
                    None,
                    reg_id,
                )
            ],
        )
        msi.add_data(db, "FeatureComponents", [("Main", component)])
        msi.add_data(
            db,
            "Registry",
            [
                (
                    reg_id,
                    1,
                    "Software\\ProofQuest\\Components",
                    component,
                    version,
                    component,
                )
            ],
        )
        index, _ = cab.append(str(path), path.name, file_id)
        alias = "F" + hashlib.sha256(name.encode()).hexdigest()[:7]
        msi.add_data(
            db,
            "File",
            [
                (
                    file_id,
                    component,
                    alias + "|" + path.name,
                    path.stat().st_size,
                    None,
                    None,
                    512,
                    index,
                )
            ],
        )
        if name == "ProofQuest.exe":
            exe_component, exe_file = component, file_id
    msi.add_data(
        db,
        "Icon",
        [
            (
                "Fable.ico",
                msi.Binary(str(staging / "_internal/Assets/Fable/application.ico")),
            )
        ],
    )
    msi.add_data(
        db,
        "Shortcut",
        [
            (
                "StartMenu",
                "MenuDir",
                "PROOFQUE|Proof Quest",
                exe_component,
                "[#" + exe_file + "]",
                None,
                "Practice with Proof Quest",
                None,
                "Fable.ico",
                0,
                1,
                "INSTALLDIR",
            )
        ],
    )
    msi.add_data(
        db, "RemoveFile", [("EmptyStartMenu", exe_component, None, "MenuDir", 2)]
    )
    msi.add_data(
        db,
        "Registry",
        [
            (
                "InstallLocation",
                1,
                "Software\\ProofQuest",
                "InstallDirectory",
                "[INSTALLDIR]",
                exe_component,
            )
        ],
    )
    add_ui(msi, db)
    cab.commit(db)
    db.Commit()
    # Release all COM/database handles before replacing a Windows file.
    view = db = None
    gc.collect()
    inspect_msi(
        temporary, {name: (staging / name).stat().st_size for name in names}, version
    )
    os.replace(temporary, destination)
    return destination


def from_archive(
    archive=ROOT / "Dist" / ARCHIVE_NAME, destination=ROOT / "Dist" / MSI_NAME
):
    (ROOT / "Out").mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="msi-", dir=ROOT / "Out") as temporary:
        staging = extract_archive(archive, temporary)
        version = json.loads((staging / "release-manifest.json").read_text())["version"]
        return build_msi(staging, destination, version)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", type=Path, default=ROOT / "Dist" / ARCHIVE_NAME)
    parser.add_argument("--output", type=Path, default=ROOT / "Dist" / MSI_NAME)
    args = parser.parse_args()
    print("Built:", from_archive(args.archive, args.output))
