from __future__ import annotations

import json
import logging
import subprocess
from pathlib import Path
from typing import Any, Dict, List


LOGGER_NAME = "transcriber"
LOG_OUTPUT_MAX_CHARS = 4000


def setup_logger(verbose: bool = False) -> logging.Logger:
    """Create a simple console logger."""
    logger = logging.getLogger(LOGGER_NAME)
    if logger.handlers:
        return logger

    level = logging.DEBUG if verbose else logging.INFO
    logger.setLevel(level)

    handler = logging.StreamHandler()
    handler.setLevel(level)
    formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    return logger


def project_root_from_config(config_path: Path) -> Path:
    return config_path.resolve().parent


def load_config(config_path: Path) -> Dict[str, Any]:
    """Load config file. YAML is preferred, JSON fallback is always available."""
    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")

    text = config_path.read_text(encoding="utf-8")
    suffix = config_path.suffix.lower()

    if suffix == ".json":
        return json.loads(text)

    if suffix in {".yaml", ".yml"}:
        try:
            import yaml  # type: ignore
        except ModuleNotFoundError as exc:
            raise ModuleNotFoundError(
                "PyYAML is required to read YAML config. Install with: pip install pyyaml "
                "or use a JSON config file."
            ) from exc

        loaded = yaml.safe_load(text)
        if not isinstance(loaded, dict):
            raise ValueError("Config root must be a mapping/dictionary.")
        return loaded

    raise ValueError(f"Unsupported config extension: {config_path.suffix}")


def resolve_path(root: Path, path_str: str | Path) -> Path:
    path = Path(path_str)
    if path.is_absolute():
        return path
    return (root / path).resolve()


def ensure_directories(paths: List[Path]) -> None:
    for path in paths:
        path.mkdir(parents=True, exist_ok=True)


def decode_output_bytes(data: bytes) -> str:
    """Decode process output safely for logs/UI without raising decode errors."""
    if not data:
        return ""
    return data.decode("utf-8", errors="replace")


def _trim_for_log(text: str, limit: int = LOG_OUTPUT_MAX_CHARS) -> str:
    if len(text) <= limit:
        return text
    return f"{text[:limit]}\n...<truncated {len(text) - limit} chars>"


def run_command(command: List[str], logger: logging.Logger) -> subprocess.CompletedProcess[bytes]:
    logger.debug("Running command: %s", " ".join(command))
    result = subprocess.run(
        command,
        capture_output=True,
        text=False,
        check=False,
    )

    stdout_bytes = result.stdout if result.stdout is not None else b""
    stderr_bytes = result.stderr if result.stderr is not None else b""
    normalized = subprocess.CompletedProcess(
        args=result.args,
        returncode=result.returncode,
        stdout=stdout_bytes,
        stderr=stderr_bytes,
    )

    stdout_text = decode_output_bytes(stdout_bytes)
    stderr_text = decode_output_bytes(stderr_bytes)

    if stdout_text.strip():
        logger.debug("stdout:\n%s", _trim_for_log(stdout_text))
    if stderr_text.strip():
        logger.debug("stderr:\n%s", _trim_for_log(stderr_text))

    if normalized.returncode != 0:
        logger.error("Command failed with return code %s", normalized.returncode)
        raise subprocess.CalledProcessError(
            returncode=normalized.returncode,
            cmd=command,
            output=stdout_bytes,
            stderr=stderr_bytes,
        )

    return normalized
