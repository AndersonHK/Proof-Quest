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

        def failed():
            path.write_text(
                json.dumps({"passed": False, "error": traceback.format_exc()}),
                encoding="utf-8",
            )
            window.close()
            application.exit(1)

        def finish_mascot():
            # Exercise the actual packaged Qt timers and atlas resources.
            window.tabs.setCurrentIndex(0)

            def review_ready():
                try:
                    assert window.journey.state == "review"
                    window.show_question(
                        (window.current + 1) % len(window.exam["questions"])
                    )

                    def sip_ready():
                        try:
                            if len(window.exam["questions"]) > 1:
                                assert window.mascot.pose_override == "sip"
                            window.grab().save(str(path.parent / "mascot-review.png"))
                            window.new_exam()

                            def home_ready():
                                try:
                                    assert window.journey.state == "home"
                                    assert window.mascot.pose_override is None
                                    result["mascot_round_trip"] = True
                                    path.write_text(
                                        json.dumps(result, indent=2), encoding="utf-8"
                                    )
                                    window.close()
                                    application.quit()
                                except Exception:
                                    failed()

                            QTimer.singleShot(1800, home_ready)
                        except Exception:
                            failed()

                    QTimer.singleShot(400, sip_ready)
                except Exception:
                    failed()

            QTimer.singleShot(3600, review_ready)

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
                    listener.player.pause()
                    finish_mascot()
                except Exception:
                    path.write_text(
                        json.dumps({"passed": False, "error": traceback.format_exc()}),
                        encoding="utf-8",
                    )
                    window.close()
                    application.exit(1)

            QTimer.singleShot(1200, finish_audio)
        else:
            finish_mascot()
    except Exception:
        path.write_text(
            json.dumps({"passed": False, "error": traceback.format_exc()}),
            encoding="utf-8",
        )
        window.close()
        application.exit(1)
