"""Shared package inventory and binary metadata; no calendar access."""
import hashlib
import json
import plistlib
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PLUGIN = ROOT / 'plugins/kai-icloud-calendar'

def sha256(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

def inventory(plugin):
    result = {}
    for directory in ['server', 'skills']:
        for p in sorted((plugin / directory).rglob('*')):
            if any(x in {'.build', '__pycache__'} for x in p.relative_to(plugin).parts):
                continue
            if p.is_symlink():
                raise ValueError(f'Symlink in payload: {p.name}')
            if p.is_file():
                result[str(p.relative_to(plugin))] = sha256(p)
    return result

def helper_metadata(plugin):
    app = plugin / 'server/native/Kai Apple Calendar Helper.app'
    exe = app / 'Contents/MacOS/calendar-helper'
    binary = subprocess.check_output(['vtool', '-show-build', str(exe)], text=True)
    versions = re.findall(r'\bminos\s+(\S+)', binary)
    arch = subprocess.check_output(['lipo', '-archs', str(exe)], text=True).strip()
    sig = subprocess.run(['codesign', '-dv', '--verbose=2', str(app)], capture_output=True, text=True, check=True).stderr
    info = plistlib.loads((app / 'Contents/Info.plist').read_bytes())
    return {'architecture': arch, 'minimum_macos': versions,
            'bundle_id': info['CFBundleIdentifier'],
            'plist_minimum_macos': info.get('LSMinimumSystemVersion'),
            'signature': 'ad-hoc' if 'Signature=adhoc' in sig else 'cms-signed',
            'hardened_runtime': 'runtime' in sig,
            'secure_timestamp': bytes.fromhex('060b2a864886f70d010910020e') in exe.read_bytes()}

def refresh(plugin, origin='source-rebuild'):
    file = plugin / 'provenance.json'
    data = json.loads(file.read_text())
    data['format_version'] = 2
    data['sha256'] = inventory(plugin)
    data['helper'] = helper_metadata(plugin)
    data['binary_origin'] = origin
    file.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n')
    return data
