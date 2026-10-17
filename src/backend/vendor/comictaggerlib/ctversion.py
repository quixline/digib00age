# Hand-written stand-in for CT's own setuptools_scm-generated ctversion.py
# (comictaggerlib/ctversion.py is generated at CT's build time from git
# tags, never a real source file in the upstream repo — see
# dev/docs/comictagger-vendoring-scope.md "Smallest version"). Values below
# are a literal copy of what the pinned pip-installed commit
# (0cc9e76f8d45d3ef27bcf2feabb676e124412abf) reported, confirmed 2026-10-15,
# so vendoring doesn't change any version string CT embeds (Tag-reader
# version tag, imagefetcher.py's User-Agent).
from __future__ import annotations

__all__ = [
    "__version__",
    "__version_tuple__",
    "version",
    "version_tuple",
    "__commit_id__",
    "commit_id",
]

version: str
__version__: str
__version_tuple__: tuple[int | str, ...]
version_tuple: tuple[int | str, ...]
commit_id: str | None
__commit_id__: str | None

__version__ = version = '1.6.0b11.dev45'
__version_tuple__ = version_tuple = (1, 6, 0, 'b11', 'dev45')

__commit_id__ = commit_id = 'g0cc9e76f8'
