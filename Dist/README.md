# Choose a Proof Quest edition

All three editions include the app, Fable artwork, Help, and the original sample dataset. Personal course material is never included.

| File | Use it for | Requirements |
|---|---|---|
| [ProofQuest-win-x64.msi](ProofQuest-win-x64.msi) | Windows installation with a Start-menu shortcut and standard uninstall | Windows 10/11 x64; no Python installation |
| [ProofQuest-win-x64.zip](ProofQuest-win-x64.zip) | A portable Windows copy you can keep in a writable folder | Windows 10/11 x64; no Python installation |
| [ProofQuest-python.zip](ProofQuest-python.zip) | Running from Python on macOS, Linux, or Windows | 64-bit Python 3.9–3.13 and a supported PySide6 platform |

## Windows installer

Double-click the MSI. It installs for your Windows account under `%LOCALAPPDATA%\Programs\ProofQuest` and adds **Proof Quest** to the Start menu. It does not require an administrator installation. Launch the app from the shortcut after setup. The demo opens on first run.

Install a newer MSI to upgrade; older versions are blocked. Use Windows **Installed apps** to uninstall. Updates and uninstall preserve your `proofquest.ini`, `Logs/`, and external datasets. Uninstall removes the program files and shortcut; remove the remaining personal-data folder yourself only if you no longer need your progress. Close Proof Quest before upgrading or uninstalling.

The installer is unsigned, as is the portable executable. An MSI installation is separate from an existing portable copy and does not automatically move its settings/history.

## Windows portable ZIP

Extract the complete `ProofQuest` folder, then run `ProofQuest.exe`. Keep `_internal` beside the executable. Settings and `Logs/` live in that writable folder. For updates, preserve your existing INI and Logs instead of overwriting them with the demo settings. Repository users can run `python Scripts/install_local.py` to update the ignored local test installation safely.

## Python ZIP

Extract it and follow its `README.md` to create a virtual environment, install `requirements.txt`, and run `Src/app.py`. Dependency installation needs internet access. The ZIP contains source and resources; it does not bundle a Python interpreter or platform-specific Qt binaries.

The pinned [PySide6 6.8.3 release](https://pypi.org/project/PySide6/6.8.3/#files) supplies wheels for Windows x64, macOS 12+ Intel/Apple Silicon, Linux x64 (glibc 2.28+), and Linux ARM64 (glibc 2.39+). There is no native wheel for every CPU/OS combination, including 32-bit systems and Windows ARM64. macOS/Linux runtime testing is still outstanding; current executable validation is on Windows.

Use **Select new dataset** for your course material and **Help** for practice and playback instructions. Build and validation details are in the repository's [development guide](../Docs/Development.md).
