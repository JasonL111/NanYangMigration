"""Build or verify the independent Chinese Industrial Enterprises archive."""

import argparse
import hashlib
from pathlib import Path
import zipfile


ROOT = Path(__file__).resolve().parents[3]
MOD = ROOT / "chinese_industrial_enterprises"
ARCHIVE = MOD.with_suffix(".zip")
CHECKSUM = ARCHIVE.with_suffix(".zip.sha256")


def source_files():
    paths = [MOD / ".metadata/metadata.json", MOD / "README.md"]
    for directory, pattern in (
        ("common", "*.txt"), ("gfx", "*.dds"), ("localization", "*.yml"), ("docs", "*.md"),
    ):
        files = list((MOD / directory).rglob(pattern))
        if not files:
            raise ValueError(f"No release files in {directory}")
        paths.extend(files)
    return {path.relative_to(ROOT).as_posix(): path.read_bytes() for path in sorted(paths)}


def write_archive(files, archive_path):
    with zipfile.ZipFile(archive_path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for name, data in sorted(files.items()):
            entry = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
            entry.create_system = 3
            entry.external_attr = 0o100644 << 16
            archive.writestr(entry, data, compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)


def verify_archive(files, archive_path):
    with zipfile.ZipFile(archive_path) as archive:
        if archive.testzip() is not None or sorted(archive.namelist()) != sorted(files):
            raise ValueError("ZIP CRC or entry names differ")
        for name, data in files.items():
            if archive.read(name) != data:
                raise ValueError(f"Source differs from ZIP entry: {name}")
    return f"{hashlib.sha256(archive_path.read_bytes()).hexdigest()}  {ARCHIVE.name}\n"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Verify the existing ZIP and SHA-256")
    args = parser.parse_args()
    files = source_files()
    if not args.check:
        write_archive(files, ARCHIVE)
    checksum = verify_archive(files, ARCHIVE)
    if args.check:
        if CHECKSUM.read_text(encoding="ascii") != checksum:
            raise ValueError("SHA-256 check failed")
    else:
        CHECKSUM.write_text(checksum, encoding="ascii", newline="\n")
    print(f"{len(files)} files verified")
    print(checksum, end="")


if __name__ == "__main__":
    main()
