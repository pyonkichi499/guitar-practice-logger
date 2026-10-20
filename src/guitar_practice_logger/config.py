"""設定ファイル（TOML）の読み込み。"""

import os
import tomllib
from dataclasses import dataclass
from pathlib import Path

# src/guitar_practice_logger/config.py から見たリポジトリ直下
REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONFIG_PATH = REPO_ROOT / "config.toml"
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
    """設定を読む。相対パスは設定ファイルのあるディレクトリを基準に解決する。"""
    path = path or config_path()
    if not path.exists():
        raise ConfigError(
            f"設定ファイルが見つかりません: {path}"
            "（config.example.toml をコピーして作成してください）"
        )
    with path.open("rb") as f:
        raw = tomllib.load(f)

    base = path.parent
    try:
        return Config(
            **{key: base / Path(raw[key]).expanduser() for key in Config.__dataclass_fields__}
        )
    except KeyError as e:
        raise ConfigError(f"設定ファイルに {e.args[0]} がありません: {path}") from e
