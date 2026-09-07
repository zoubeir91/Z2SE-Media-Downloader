from pathlib import Path
import hashlib
import json
import sys


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda: f.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


version = sys.argv[1].strip()
if version != '32.44':
    raise SystemExit(f'This release patch is for 32.44, got {version}')

payload = Path('payload')
app_path = payload / 'app.py'
updater_path = payload / 'z2se_updater.pyw'
candidate = Path('candidate_v32_44.py')

if not candidate.is_file():
    raise SystemExit('Missing tested candidate_v32_44.py')

text = candidate.read_text(encoding='utf-8')
if 'APP_VERSION = "32.44"' not in text:
    raise SystemExit('Candidate version marker is not 32.44')
if 'def _validate_completed_download' not in text:
    raise SystemExit('Candidate Facebook/media validation is missing')
if '"nl": "Nederlands"' not in text:
    raise SystemExit('Candidate Dutch language support is missing')

app_path.write_text(text, encoding='utf-8')

files = []
for rel in ('app.py', 'z2se_updater.pyw'):
    p = payload / rel
    if not p.is_file():
        raise SystemExit(f'Missing payload file: {rel}')
    files.append({
        'path': rel,
        'sha256': sha256(p),
        'size': p.stat().st_size,
    })

manifest = {
    'product': 'Z2SE Media Downloader',
    'version': version,
    'created_by': 'GitHub Actions / tested v32.44 candidate',
    'files': files,
}
(payload / 'update_manifest.json').write_text(
    json.dumps(manifest, indent=2, ensure_ascii=False),
    encoding='utf-8',
)

print('Prepared Z2SE v32.44 from tested candidate')
