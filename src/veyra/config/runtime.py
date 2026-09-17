"""Runtime filesystem preparation."""

from pathlib import Path

from .settings import Settings


def ensure_directory(path: Path) -> None:
    """Create a directory and its missing parents when necessary."""

    path.mkdir(
        parents=True,
        exist_ok=True,
    )


def prepare_runtime_directories(settings: Settings) -> None:
    """
    Prepare directories required by the application at runtime.

    Configuration loading itself deliberately has no filesystem side effects.
    """

    ensure_directory(settings.database_path.parent)
    ensure_directory(settings.media_root)
    ensure_directory(settings.log_dir)
