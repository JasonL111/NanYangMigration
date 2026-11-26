"""Build or verify the standalone Self-Strengthening Reform release."""

import argparse
import hashlib
import io
from pathlib import Path
import zipfile


REPO = Path(__file__).resolve().parents[3]
MOD_ID = "self_strengthening_reform"
MOD = REPO / MOD_ID
ARCHIVE = REPO / f"{MOD_ID}.zip"
CHECKSUM = ARCHIVE.with_suffix(".zip.sha256")

SOURCE_TYPES = {
    "common": ".txt",
    "docs": ".md",
    "events": ".txt",
    "gfx": ".dds",
    "localization": ".yml",
}


def release_sources():
    sources = {
        f"{MOD_ID}/.metadata/metadata.json": (MOD / ".metadata/metadata.json").read_bytes(),
        f"{MOD_ID}/README.md": (MOD / "README.md").read_bytes(),
    }
    for directory, extension in SOURCE_TYPES.items():
        root = MOD / directory
        files = sorted(root.rglob(f"*{extension}"))
        if not files:
            raise ValueError(f"Missing source files under {root}")
        for path in files:
            if not path.is_file() or path.is_symlink():
                raise ValueError(f"Expected a regular release file: {path}")
            if any(part.startswith(".") for part in path.relative_to(root).parts):
                continue
            sources[path.relative_to(MOD.parent).as_posix()] = path.read_bytes()
    return sources


def build_bytes(sources):
    output = io.BytesIO()
    with zipfile.ZipFile(output, "w") as archive:
        for name, content in sorted(sources.items()):
            entry = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
            entry.create_system = 3
            entry.external_attr = 0o100644 << 16
            archive.writestr(entry, content, compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)
    return output.getvalue()


def verify_archive(archive_bytes, sources):
    with zipfile.ZipFile(io.BytesIO(archive_bytes)) as archive:
        if archive.testzip() is not None or sorted(archive.namelist()) != sorted(sources):
            raise ValueError("ZIP structure or CRC check failed")
        for name, content in sources.items():
            if archive.read(name) != content:
                raise ValueError(f"Archive and source differ: {name}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Verify the existing ZIP and SHA-256")
    args = parser.parse_args()
    sources = release_sources()
    archive_bytes = ARCHIVE.read_bytes() if args.check else build_bytes(sources)
    verify_archive(archive_bytes, sources)
    digest = hashlib.sha256(archive_bytes).hexdigest()
    checksum = f"{digest}  {ARCHIVE.name}\n"
    if args.check:
        if CHECKSUM.read_text(encoding="ascii") != checksum:
            raise ValueError("SHA-256 check failed")
    else:
        ARCHIVE.write_bytes(archive_bytes)
        CHECKSUM.write_text(checksum, encoding="ascii", newline="\n")
    print(f"{len(sources)} files verified")
    print(checksum, end="")


if __name__ == "__main__":
    main()
