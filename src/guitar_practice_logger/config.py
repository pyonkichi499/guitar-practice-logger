"""設定ファイル（TOML）の読み込み。"""

import os
import tomllib
from dataclasses import dataclass
from pathlib import Path

DEFAULT_CONFIG_PATH = Path("~/.config/guitar-practice-logger/config.toml")
CONFIG_ENV = "GPL_CONFIG"


class ConfigError(Exception):
    pass


@dataclass(frozen=True)
class Config:
    songs_root: Path  # DAW が曲ごとに書き出すフォルダの親
    archive_dir: Path  # 取り込んだ WAV の移動先
    songs_file: Path  # 曲の台帳（TOML）
    db_path: Path  # テイクの記録（SQLite）


def config_path() -> Path:
    return Path(os.environ.get(CONFIG_ENV, DEFAULT_CONFIG_PATH)).expanduser()


def load_config(path: Path | None = None) -> Config:
    path = path or config_path()
    if not path.exists():
        raise ConfigError(
            f"設定ファイルが見つかりません: {path}（config.example.toml を参考に作成してください）"
        )
    with path.open("rb") as f:
        raw = tomllib.load(f)

    try:
        return Config(**{key: Path(raw[key]).expanduser() for key in Config.__dataclass_fields__})
    except KeyError as e:
        raise ConfigError(f"設定ファイルに {e.args[0]} がありません: {path}") from e
