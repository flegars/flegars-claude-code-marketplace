import json
from pathlib import Path

CONFIG_RELATIVE_PATH = Path(".claude") / "pr-reviewer.json"

DEFAULTS = {
    "platform": None,
    "host": None,
    "base": None,
    "regression_window_days": 14,
    "max_inline_comments": 15,
}


class ConfigError(Exception):
    pass


def load_config(repo_root: Path) -> dict:
    config = dict(DEFAULTS)
    path = repo_root / CONFIG_RELATIVE_PATH
    if not path.is_file():
        return config
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        raise ConfigError(f"{CONFIG_RELATIVE_PATH} n'est pas un JSON valide : {error}") from error
    if not isinstance(raw, dict):
        raise ConfigError(f"{CONFIG_RELATIVE_PATH} doit contenir un objet JSON.")
    unknown = sorted(set(raw) - set(DEFAULTS))
    if unknown:
        raise ConfigError(f"Clés inconnues dans {CONFIG_RELATIVE_PATH} : {', '.join(unknown)}")
    for key in ("regression_window_days", "max_inline_comments"):
        if key in raw and (not isinstance(raw[key], int) or raw[key] < 0):
            raise ConfigError(f"{key} doit être un entier positif ou nul.")
    config.update(raw)
    return config
