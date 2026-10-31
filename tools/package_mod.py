"""Run the checks and package all runtime files, including hidden metadata."""
from pathlib import Path
import hashlib
import json
import subprocess
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[1]
MOD = ROOT / 'nanyang_migration'

def main():
    result = subprocess.run([sys.executable, '-m', 'unittest', 'discover', '-s', 'tests', '-v'],
                            cwd=ROOT, capture_output=True, text=True)
    report = MOD / 'docs/test-results.txt'
    report.write_text('Synthetic script-harness / static checks; NOT a Victoria 3 engine run.\n'
                      + result.stdout + result.stderr, encoding='utf-8')
    print(result.stdout + result.stderr)
    if result.returncode:
        raise SystemExit(result.returncode)
    manifest = MOD / 'docs/SHA256SUMS.json'
    manifest.write_text(json.dumps({str(p.relative_to(MOD)): hashlib.sha256(p.read_bytes()).hexdigest()
                                  for p in sorted(MOD.rglob('*')) if p.is_file() and p != manifest}, indent=2)+'\n')
    archive = ROOT / 'nanyang_migration.zip'
    with zipfile.ZipFile(archive, 'w', zipfile.ZIP_DEFLATED) as z:
        for f in sorted(MOD.rglob('*')):
            if f.is_file(): z.write(f, f.relative_to(ROOT))
    with zipfile.ZipFile(archive) as z:
        assert z.testzip() is None
        assert 'nanyang_migration/.metadata/metadata.json' in z.namelist()
        assert len(z.namelist()) == len([p for p in MOD.rglob('*') if p.is_file()])
        for path, digest in json.loads(manifest.read_text()).items():
            assert hashlib.sha256(z.read('nanyang_migration/'+path)).hexdigest() == digest
    digest = hashlib.sha256(archive.read_bytes()).hexdigest()
    (ROOT/'nanyang_migration.zip.sha256').write_text(digest+'  nanyang_migration.zip\n')
    print(f'ZIP validated: {archive}, {archive.stat().st_size} bytes, SHA256 {digest}')

if __name__ == '__main__':
    main()
