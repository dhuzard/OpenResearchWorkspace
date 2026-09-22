"""Filesystem checks shared by the mutation boundaries, without provider APIs.

These guards assume exclusive workspace access during a mutation. They are not
an OS sandbox against another process changing paths between checks and writes.
"""
from __future__ import annotations

import hashlib
import os
from pathlib import Path, PurePosixPath
import re
import stat


class UnsafePathError(ValueError):
    """A mutation would follow a link or cross its declared filesystem boundary."""


def absolute_path(value: Path | str) -> Path:
    """Canonicalize ancestors, but preserve the named root for link inspection.

User-selected workspace/output roots can live below filesystem aliases such as
macOS /var -> /private/var. Resolve their ancestors before comparing boundaries.
Do not resolve the final component: a symlink/junction at the selected root is
still refused. Resource paths below a workspace never use this normalization;
assert_no_links checks every component against the already canonical root.
"""
    path = Path(os.path.abspath(Path(value).expanduser()))
    return path.parent.resolve(strict=False) / path.name


def assert_no_links(path: Path) -> None:
    for candidate in [*reversed(path.parents), path]:
        try:
            info = candidate.lstat()
        except FileNotFoundError:
            continue
        if stat.S_ISLNK(info.st_mode) or (
            getattr(info, "st_file_attributes", 0)
            & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400)
        ):
            raise UnsafePathError(f"Symlink/junction paths are not allowed: {candidate}")


def relative_path(raw: str) -> Path:
    if not isinstance(raw, str) or not raw or raw != raw.strip():
        raise UnsafePathError("Local paths must be non-empty and have no surrounding whitespace.")
    value = raw.replace("\\", "/")
    path = PurePosixPath(value)
    if (value.startswith("/") or re.match(r"^[A-Za-z]:", value)
            or ":" in value or "\x00" in value or ".." in path.parts
            or path == PurePosixPath(".")):
        raise UnsafePathError(f"Not a safe workspace-relative path: {raw!r}")
    return Path(*path.parts)


def overlaps(left: Path, right: Path) -> bool:
    return left == right or left in right.parents or right in left.parents


def inventory(root: Path, *, exclude: frozenset[str] = frozenset()) -> dict:
    """Hash all regular files and inventory directories; refuse links/special files."""
    root = absolute_path(root)
    assert_no_links(root)
    files: dict[str, str] = {}
    directories: list[str] = []
    for directory, names, filenames in os.walk(root, followlinks=False):
        names.sort()
        filenames.sort()
        for name in [*names, *filenames]:
            path = Path(directory) / name
            assert_no_links(path)
            rel = path.relative_to(root).as_posix()
            mode = path.stat().st_mode
            if stat.S_ISDIR(mode):
                directories.append(rel)
            elif stat.S_ISREG(mode):
                if rel not in exclude:
                    digest = hashlib.sha256()
                    with path.open("rb") as stream:
                        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                            digest.update(chunk)
                    files[rel] = digest.hexdigest()
            else:
                raise UnsafePathError(f"Special files cannot be packaged: {path}")
    return {"files": files, "directories": sorted(directories)}
