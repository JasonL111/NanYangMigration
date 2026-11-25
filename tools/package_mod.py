"""Run checks and create deterministic installation archives and SHA-256 files."""
from pathlib import Path
import hashlib
import json
import re
import subprocess
import sys
import zipfile

from build_mod import ROOT, MOD
from build_probe import PROBE

PACKAGED_DIRS = {'.metadata', 'common', 'events', 'gfx', 'localization', 'docs'}

def file_digest(data):
    return hashlib.sha256(data).hexdigest()

def package(folder, archive):
    files = {
        p.relative_to(folder).as_posix(): p.read_bytes()
        for p in sorted(folder.rglob('*'))
        if p.is_file() and p.relative_to(folder).parts[0] in PACKAGED_DIRS
        and '__pycache__' not in p.parts and p.suffix != '.pyc'
        and p.name != 'SHA256SUMS.json'
    }
    files['README.md'] = (folder / 'README.md').read_bytes()
    manifest = {name: file_digest(data) for name, data in files.items()}
    manifest_name = 'docs/SHA256SUMS.json'
    files[manifest_name] = (json.dumps(manifest, indent=2, sort_keys=True) + '\n').encode()
    (folder / manifest_name).parent.mkdir(exist_ok=True)
    (folder / manifest_name).write_bytes(files[manifest_name])
    with zipfile.ZipFile(archive, 'w', zipfile.ZIP_DEFLATED, compresslevel=9) as bundle:
        for path, data in sorted(files.items()):
            entry = zipfile.ZipInfo(f'{folder.name}/{path}', (1980, 1, 1, 0, 0, 0))
            entry.external_attr = 0o100644 << 16
            bundle.writestr(entry, data, compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)
    with zipfile.ZipFile(archive) as bundle:
        expected = {f'{folder.name}/{path}' for path in files}
        if bundle.testzip() is not None or set(bundle.namelist()) != expected or len(bundle.namelist()) != len(expected):
            raise ValueError(f'Archive entries or CRC mismatch: {archive}')
        for path, data in files.items():
            if bundle.read(f'{folder.name}/{path}') != data:
                raise ValueError(f'Archive byte mismatch: {path}')
        if '.metadata/metadata.json' not in files:
            raise ValueError('Missing required metadata')
    digest = file_digest(archive.read_bytes())
    archive.with_suffix('.zip.sha256').write_text(f'{digest}  {archive.name}\n')
    print(f'{archive.relative_to(ROOT)}: {digest}')

def main():
    result = subprocess.run([sys.executable, '-m', 'unittest', 'discover', '-s', 'tests', '-v'],
                            cwd=ROOT, capture_output=True, text=True)
    output = result.stdout + result.stderr
    print(output)
    if result.returncode:
        raise SystemExit(result.returncode)
    stable_log = re.sub(r'^(Ran \d+ tests) in [\d.]+s$', r'\1', output, flags=re.M)
    (MOD / 'docs/test-results.txt').write_text(
        'Static and synthetic-scenario checks (not a Victoria 3 engine run).\n' + stable_log,
        encoding='utf-8')
    package(MOD, ROOT / 'nanyang_migration.zip')
    package(PROBE, ROOT / 'nanyang_native_probe.zip')

if __name__ == '__main__':
    main()
