"""Package unchanged Fable artwork into Windows' standard icon resolutions."""

import struct
from pathlib import Path
from PySide6.QtCore import QByteArray, QBuffer, QIODevice, Qt
from PySide6.QtGui import QImage, QPainter


def build_icon(root):
    source = QImage(str(root / "Assets/Fable/neutral.png"))
    if source.isNull():
        raise RuntimeError("Fable icon source is missing.")
    frames = []
    for size in (16, 24, 32, 48, 64, 128, 256):
        # This is native asset packaging/resampling, not a new illustration.
        artwork = source.copy(150, 100, 1000, 1100).scaled(
            size, size, Qt.KeepAspectRatio, Qt.SmoothTransformation
        )
        frame = QImage(size, size, QImage.Format_ARGB32)
        frame.fill(Qt.transparent)
        painter = QPainter(frame)
        painter.drawImage(
            (size - artwork.width()) // 2, (size - artwork.height()) // 2, artwork
        )
        painter.end()
        data = QByteArray()
        buffer = QBuffer(data)
        buffer.open(QIODevice.WriteOnly)
        if not frame.save(buffer, "PNG"):
            raise RuntimeError("Cannot encode Fable icon frame.")
        frames.append((frame.width(), frame.height(), bytes(data)))
    offset = 6 + 16 * len(frames)
    result = bytearray(struct.pack("<HHH", 0, 1, len(frames)))
    for width, height, data in frames:
        result.extend(
            struct.pack(
                "<BBBBHHII", width % 256, height % 256, 0, 0, 1, 32, len(data), offset
            )
        )
        offset += len(data)
    for _, _, data in frames:
        result.extend(data)
    destination = root / "Assets/Fable/application.ico"
    destination.write_bytes(result)
    return destination


if __name__ == "__main__":
    print(build_icon(Path(__file__).resolve().parents[1]))
