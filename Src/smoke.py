"""Explicit developer-only executable smoke test, isolated with --home."""

import json, traceback
from pathlib import Path
from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QMessageBox


def run_smoke(window, path, application, audible=False):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        window.grab().save(str(path.parent / "practice.png"))
        for i, q in enumerate(window.exam["questions"]):
            window.show_question(i)
            pick = next(j for j, o in enumerate(q["options"]) if o["correct"])
            window.options[pick].click()
        window.finish_exam()
        assert window.result["correct"] == window.result["total"]
        window.grab().save(str(path.parent / "graded.png"))
        window.tabs.setCurrentIndex(1)
        window.listen.grab().save(str(path.parent / "player.png"))
        window.autosave()
        result = {
            "passed": True,
            "dataset": window.dataset.id,
            "questions": window.result["total"],
            "score": window.result["correct"],
            "settings_file": str(window.settings.path),
            "has_audio": window.listen.data is not None,
        }
        if window.listen.data:
            listener = window.listen
            listener.refresh_outputs()
            listener.audio.setMuted(not audible)
            listener.seek(10000)
            listener.player.play()
            before = listener.player.position()

            def finish_audio():
                try:
                    assert listener.player.position() > before + 100
                    result["media_clock_advanced"] = True
                    result["audio_muted"] = listener.audio.isMuted()
                    result["audio_device"] = listener.audio.device().description()
                    result["audio_volume"] = listener.audio.volume()
                    path.write_text(json.dumps(result, indent=2), encoding="utf-8")
                    window.close()
                    application.quit()
                except Exception:
                    path.write_text(
                        json.dumps({"passed": False, "error": traceback.format_exc()}),
                        encoding="utf-8",
                    )
                    window.close()
                    application.exit(1)

            QTimer.singleShot(1200, finish_audio)
        else:
            path.write_text(json.dumps(result, indent=2), encoding="utf-8")
            window.close()
            application.quit()
    except Exception:
        path.write_text(
            json.dumps({"passed": False, "error": traceback.format_exc()}),
            encoding="utf-8",
        )
        window.close()
        application.exit(1)
