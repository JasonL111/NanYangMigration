"""Build a reproducible, game-only ZIP and verify it against the source tree."""

from hashlib import sha256
import json
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo

PROJECT = Path(__file__).resolve().parents[1]
MOD = PROJECT / "overseas_chinese_mobilization"
ARCHIVE = PROJECT / f"{MOD.name}.zip"
MANIFEST = "docs/SHA256SUMS.json"
INCLUDE = {".metadata", "common", "events", "gfx", "localization", "docs", "README.md"}


def build():
    files = {}
    for path in sorted(MOD.rglob("*")):
        relative = path.relative_to(MOD)
        if relative.parts[0] not in INCLUDE or "__pycache__" in relative.parts:
            continue
        if path.is_symlink():
            raise ValueError(f"Refusing to package linked file {relative}")
        if path.is_file() and path.suffix != ".pyc" and relative.as_posix() != MANIFEST:
            files[relative.as_posix()] = path.read_bytes()
    if ".metadata/metadata.json" not in files or "README.md" not in files:
        raise ValueError("The archive needs Launcher metadata and a README")

    digests = {name: sha256(data).hexdigest() for name, data in files.items()}
    files[MANIFEST] = (json.dumps(digests, indent=2, sort_keys=True) + "\n").encode()
    (MOD / MANIFEST).write_bytes(files[MANIFEST])

    with ZipFile(ARCHIVE, "w", compression=ZIP_DEFLATED, compresslevel=9) as bundle:
        for name, data in sorted(files.items()):
            entry = ZipInfo(f"{MOD.name}/{name}", (1980, 1, 1, 0, 0, 0))
            entry.external_attr = 0o100644 << 16
            bundle.writestr(entry, data, compress_type=ZIP_DEFLATED, compresslevel=9)

    with ZipFile(ARCHIVE) as bundle:
        expected = [f"{MOD.name}/{name}" for name in sorted(files)]
        if bundle.namelist() != expected or bundle.testzip() is not None:
            raise ValueError("ZIP entries or CRC validation failed")
        for name, data in files.items():
            archived = bundle.read(f"{MOD.name}/{name}")
            if archived != data or archived != (MOD / name).read_bytes():
                raise ValueError(f"Mismatch with source for {name}")

    digest = sha256(ARCHIVE.read_bytes()).hexdigest()
    ARCHIVE.with_suffix(".zip.sha256").write_text(f"{digest}  {ARCHIVE.name}\n")
    print(f"{len(files)} files verified, including the DDS texture and metadata.")
    print(f"{digest}  {ARCHIVE.name}")


if __name__ == "__main__":
    build()
