from pathlib import Path

import pytest

from guitar_practice_logger.config import ConfigError, load_config


def test_relative_paths_are_resolved_from_config_dir(tmp_path):
    path = tmp_path / "config.toml"
    path.write_text(
        'songs_root = "/mnt/c/songs"\n'
        'archive_dir = "archive"\n'
        'songs_file = "songs.toml"\n'
        'db_path = "~/takes.db"\n'
    )

    config = load_config(path)

    assert config.songs_root == Path("/mnt/c/songs")
    assert config.archive_dir == tmp_path / "archive"
    assert config.songs_file == tmp_path / "songs.toml"
    assert config.db_path == Path("~/takes.db").expanduser()


def test_missing_key_is_reported(tmp_path):
    path = tmp_path / "config.toml"
    path.write_text('songs_root = "/x"\n')

    with pytest.raises(ConfigError, match="archive_dir"):
        load_config(path)
