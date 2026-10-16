# Third-party runtime components

The Windows bundle includes unmodified runtime components from Python, PySide6/Qt, Shiboken, and PyInstaller. Shared libraries reside in `_internal/`; their upstream license terms apply independently of the original application code. No book content or private recordings are included.

| Component | Pinned version | Upstream source and licensing information |
|---|---|---|
| Python | Build interpreter version recorded in the release manifest | [CPython](https://github.com/python/cpython), [Python license](https://docs.python.org/3/license.html) |
| PySide6, Qt, Shiboken | 6.8.3 | [Qt for Python](https://code.qt.io/cgit/pyside/pyside-setup.git/), [Qt licensing](https://doc.qt.io/qt-6/licensing.html) |
| Qt multimedia dependencies | From the PySide6 6.8.3 Windows wheels | [Qt FFmpeg attribution](https://doc.qt.io/qt-6.8/qtmultimedia-attribution-ffmpeg.html) |
| PyInstaller bootloader | 6.16.0 | [PyInstaller](https://github.com/pyinstaller/pyinstaller), GPL with its distribution exception |

The build copies available dependency license files into the bundle's `Licenses/` folder. See upstream sources for corresponding source code and attribution details. Project-owned badge artwork and synthetic demo fixtures are original to Proof Quest. Windows system fonts are loaded from the installed operating system and are not redistributed.
