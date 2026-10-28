#!/usr/bin/env python3
"""Export an allowlisted marketplace snapshot and verify its ZIP round trip."""
import argparse
import hashlib
import json
import re
import shutil
import subprocess
import tempfile
import zipfile
from pathlib import Path
from package_common import ROOT, PLUGIN
from validate_plugin import validate, require

PUBLIC_FILES = ['README.md','README.en.md','LICENSE','NOTICE','.gitignore',
                '.agents/plugins/marketplace.json','docs/building.md',
                'scripts/package_common.py','scripts/refresh_provenance.py',
                'scripts/validate_plugin.py','scripts/package_plugin.py','scripts/ci_release.py',
                'scripts/verify_release.py','scripts/extract_release_notes.py','tests/test_packaging.py','tests/test_release_notes.py']


def export(root, output, distribution=False):
    plugin=root/'plugins/kai-icloud-calendar'
    state=validate(plugin)
    manifest=json.loads((plugin/'plugin.json').read_text())
    version=manifest['version']
    require(re.fullmatch(r'\d{4}\.\d{1,2}\.\d+',version) is not None,'Use a YYYY.M.N plugin version')
    if distribution:
        require(state['signature']=='cms-signed' and state['hardened_runtime'] and state['secure_timestamp'],
                'Distribution requires Developer ID, hardened runtime and secure timestamp')
        app=plugin/'server/native/Kai Apple Calendar Helper.app'
        details=subprocess.run(['codesign','-dv','--verbose=2',str(app)],capture_output=True,text=True,check=True).stderr
        require('Authority=Developer ID Application:' in details and 'Timestamp=' in details,'Developer ID authority and timestamp must be verifiable')
        subprocess.run(['xcrun','stapler','validate',str(app)],check=True,capture_output=True)
        subprocess.run(['spctl','--assess','--type','execute',str(app)],check=True,capture_output=True)
    suffix='' if distribution else '-local'
    output.mkdir(parents=True,exist_ok=True)
    snapshot=output/f'kai-chatgpt-plugins-{version}{suffix}'
    require(not snapshot.exists(),'Output already exists; use a new output directory')
    snapshot.mkdir()
    for rel in PUBLIC_FILES:
        target=snapshot/rel;target.parent.mkdir(parents=True,exist_ok=True)
        shutil.copy2(root/rel,target)
    shutil.copytree(plugin,snapshot/'plugins/kai-icloud-calendar',ignore=shutil.ignore_patterns('.build','__pycache__','.DS_Store'))
    if (root/'.github').is_dir():
        shutil.copytree(root/'.github',snapshot/'.github')
    for p in snapshot.rglob('*'):
        require(not p.is_symlink(),f'Symlink in exported snapshot: {p.name}')
        require(p.name not in {'.local','.git','Developer-Credentials'},'Private directory in snapshot')
        require(p.suffix not in {'.p8','.p12','.key'},'Credential file in snapshot')
        if p.is_file() and p.suffix in {'.md','.json','.py','.yaml','.yml','.sh','.js','.swift'}:
            text=p.read_text()
            require(('/' + 'Users/') not in text,f'Personal absolute path: {p.name}')
            require(not re.search(r'-----BEGIN (?:RSA |EC )?PRIVATE KEY-----|gh[pousr]_[A-Za-z0-9]{25,}',text),f'Credential marker: {p.name}')
    archive=output/(snapshot.name+'.zip')
    with zipfile.ZipFile(archive,'w',compression=zipfile.ZIP_DEFLATED) as z:
        for p in sorted(snapshot.rglob('*')):
            if p.is_file(): z.write(p,p.relative_to(snapshot))
    with tempfile.TemporaryDirectory(prefix='kai archive roundtrip ') as temp:
        with zipfile.ZipFile(archive) as z:
            for item in z.infolist():
                rel=Path(item.filename)
                require(not rel.is_absolute() and '..' not in rel.parts,'Unsafe archive entry')
                target=Path(temp)/rel;target.parent.mkdir(parents=True,exist_ok=True)
                target.write_bytes(z.read(item));target.chmod((item.external_attr>>16)&0o777)
        validate(Path(temp)/'plugins/kai-icloud-calendar')
    digest=hashlib.sha256(archive.read_bytes()).hexdigest()
    (output/'SHA256SUMS.txt').write_text(f'{digest}  {archive.name}\n')
    print('Exported and round-trip verified:',archive.name)
    return snapshot,archive


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output',type=Path,default=ROOT/'dist')
    p.add_argument('--distribution',action='store_true',help='Require notarization and Gatekeeper acceptance')
    args=p.parse_args()
    export(ROOT,args.output.resolve(),args.distribution)
