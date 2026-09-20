#!/usr/bin/env python3
"""Build three clean source-based app editions, never an SD-card/user-data image."""
import argparse
import hashlib
import io
import json
from pathlib import Path
import subprocess
import tarfile

ROOT = Path(__file__).resolve().parents[1]


def build(version, output):
    if not version or any(c not in '0123456789abcdefghijklmnopqrstuvwxyz.-' for c in version):
        raise ValueError('Use a simple lowercase release version.')
    if subprocess.check_output(['git', 'status', '--porcelain'], cwd=ROOT).strip():
        raise ValueError('Commit all changes before building a release so source_commit is accurate.')
    output.mkdir(parents=True, exist_ok=True)
    files = subprocess.check_output(['git', 'ls-files', '-z'], cwd=ROOT).decode().split('\0')
    editions = json.loads((ROOT / 'profiles/editions.json').read_text())
    checksums = []
    for name, profile in editions.items():
        package = f'kali-touch-ui-{version}-{name}'
        target = output / (package + '.tar.gz')
        with tarfile.open(target, 'w:gz') as archive:
            for filename in files:
                if (not filename or filename.startswith(('.git', 'tests/'))
                        or (filename.startswith('tools/') and filename != 'tools/optimize_boot.py')):
                    continue
                path = ROOT / filename
                if not path.is_file() or path.is_symlink():
                    continue
                data = path.read_bytes()
                if filename == 'web/assets/edition.js':
                    data = ("(() => { const p = new URLSearchParams(location.search).get('edition'); "
                            "document.documentElement.dataset.edition = ['7inch','4inch','35inch'].includes(p) ? p : "
                            + json.dumps(name) + "; })();\n").encode()
                entry = tarfile.TarInfo(package + '/' + filename)
                entry.size = len(data); entry.mode = 0o755 if filename.endswith('.sh') or filename.endswith('kali-touch-session') else 0o644
                archive.addfile(entry, io.BytesIO(data))
            manifest = dict(profile, edition=name, version=version, source_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(), artifact_type='application bundle; not a flashable OS image')
            data = (json.dumps(manifest, indent=2)+'\n').encode()
            entry = tarfile.TarInfo(package+'/EDITION.json');entry.size=len(data);entry.mode=0o644
            archive.addfile(entry, io.BytesIO(data))
        checksums.append(hashlib.sha256(target.read_bytes()).hexdigest()+'  '+target.name)
        print(target)
    (output/'SHA256SUMS').write_text('\n'.join(checksums)+'\n')


if __name__ == '__main__':
    p=argparse.ArgumentParser();p.add_argument('version');p.add_argument('--output',type=Path,default=ROOT/'dist')
    args=p.parse_args();build(args.version,args.output)
