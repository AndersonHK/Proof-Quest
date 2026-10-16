"""Portable settings: always beside the executable, never inside its bundle."""

import configparser
import json
import os
import sys
from pathlib import Path


def app_directory():
    return (
        Path(sys.executable).resolve().parent
        if getattr(sys, "frozen", False)
        else Path(__file__).resolve().parents[1]
    )


def resources_directory():
    return (
        Path(sys._MEIPASS)
        if getattr(sys, "frozen", False)
        else Path(__file__).resolve().parents[1]
    )


class Settings:
    def __init__(self, home=None):
        self.home = Path(home or app_directory())
        self.path = self.home / "proofquest.ini"
        self.config = configparser.ConfigParser(interpolation=None)
        if self.path.exists():
            try:
                self.config.read(self.path, encoding="utf-8")
            except configparser.Error as error:
                raise ValueError(f"Cannot read settings: {error}") from error
        if not self.config.has_section("ProofQuest"):
            self.config.add_section("ProofQuest")

    def get(self, key, default=None):
        raw = self.config.get("ProofQuest", key, fallback=None)
        if raw is None:
            return default
        try:
            value = json.loads(raw)
        except (ValueError, TypeError):
            return default
        if default is not None:
            if isinstance(default, bool) and not isinstance(value, bool):
                return default
            if isinstance(default, (int, float)) and not isinstance(default, bool):
                if not isinstance(value, (int, float)) or isinstance(value, bool):
                    return default
                if isinstance(default, int) and key not in ("playback_rate",):
                    value = int(value)
            elif not isinstance(value, type(default)):
                return default
        return value

    def set(self, key, value):
        self.config.set("ProofQuest", key, json.dumps(value, ensure_ascii=False))

    def save(self):
        self.home.mkdir(parents=True, exist_ok=True)
        temp = self.path.with_suffix(".ini.tmp")
        with temp.open("w", encoding="utf-8") as out:
            self.config.write(out)
        os.replace(temp, self.path)

    def dataset_path(self):
        value = self.get("dataset", "")
        if not value:
            return None
        path = Path(value)
        return path if path.is_absolute() else (self.home / path).resolve()

    def select_dataset(self, path):
        path = Path(path).resolve()
        try:
            value = os.path.relpath(path, self.home)
        except ValueError:
            value = str(path)
        self.set("dataset", value)
        self.save()
