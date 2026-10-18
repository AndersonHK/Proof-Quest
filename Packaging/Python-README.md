# Proof Quest — Python edition

Extract this entire folder into a writable location. This edition includes the Python source, Fable artwork, Help, schemas and original demonstration dataset. It does not include Python, Qt binaries, or private course material.

Use **64-bit Python 3.9–3.13** and the pinned PySide6 dependency. Python 3.11 or 3.12 is a practical choice for a new environment. The PySide6 6.8.3 wheels support Windows x64, macOS 12+ on Intel/Apple Silicon, Linux x64 with glibc 2.28+, and Linux ARM64 with glibc 2.39+. A desktop graphical session and audio output are needed for those features. Other architectures, 32-bit systems, musl Linux and Windows ARM64 do not have a native wheel in this pinned release. See the [official release files](https://pypi.org/project/PySide6/6.8.3/#files).

## macOS or Linux

Open a terminal in this extracted folder:

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python Src/app.py
```

On Linux, your distribution may require its Python venv package and Qt/X11/Wayland system libraries. Dependency installation needs internet access. macOS and Linux runtime behavior has not yet been tested by this project.

## Windows

```powershell
py -3.12 -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
.venv\Scripts\python.exe Src\app.py
```

Use the Python version you installed if it differs from 3.12. These commands install dependencies only into this folder's environment.

## Using and updating the app

The original demo opens first. Use **Select new dataset** to choose another dataset's `dataset.json`; **Help** explains the app. Audio is optional and supplied by each dataset. Settings are saved in `proofquest.ini` in this folder, with practice history under `Logs/`.

To update, close the app, extract the new edition into a new folder, and copy your existing `proofquest.ini` and `Logs/` there. Keep external datasets in a stable location; reselect a dataset if its relative path no longer resolves. Do not overwrite your existing settings with the demo INI.

Project source and development/build instructions: [Proof Quest on GitHub](https://github.com/AndersonHK/Proof-Quest). Proof Quest is MIT licensed; see `LICENSE` and `THIRD-PARTY-NOTICES.md`. Dependencies retain their own licenses.
