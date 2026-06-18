"""Configuration loader for the EEG visualization tool.

Reads config.yaml and resolves the data-file paths to absolute paths so
the rest of the modules never have to worry about the working directory.
"""

import os
import yaml

# Project directory (where this file and config.yaml live).
PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))

DEFAULT_CONFIG_PATH = os.path.join(PROJECT_DIR, "config.yaml")


def _resolve(base, path):
    """Resolve `path` against `base` unless it is already absolute."""
    if os.path.isabs(path):
        return path
    return os.path.normpath(os.path.join(base, path))


def load_config(path=None):
    """Load config.yaml and return it as a dict with absolute data paths.

    Path resolution:
      - paths.data_dir is resolved relative to the project directory.
      - raw_eeg_dir / coherence_file / dai_file are resolved relative
        to data_dir.
    """
    path = path or DEFAULT_CONFIG_PATH

    with open(path, "r") as f:
        config = yaml.safe_load(f)

    paths = config.setdefault("paths", {})

    data_dir = _resolve(PROJECT_DIR, paths.get("data_dir", "."))
    paths["data_dir"] = data_dir

    for key in ("raw_eeg_dir", "coherence_file", "dai_file"):
        if key in paths and paths[key] is not None:
            paths[key] = _resolve(data_dir, paths[key])

    return config
