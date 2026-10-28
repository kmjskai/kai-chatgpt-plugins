#!/usr/bin/env python3
"""Verify the downloaded release archive without rebuilding or calendar access."""
import argparse,hashlib,json,tempfile,zipfile
from pathlib import Path
from validate_plugin import validate,require
import subprocess


def verify(directory,version):
    archive=directory/f'kai-chatgpt-plugins-{version}.zip'
    sums=(directory/'SHA256SUMS.txt').read_text().splitlines()
    matching=[line.split() for line in sums if line.split()[-1]==archive.name]
    require(len(matching)==1,'Missing or duplicate archive checksum')
    digest=hashlib.sha256(archive.read_bytes()).hexdigest()
    require(digest==matching[0][0],'Release checksum mismatch')
    receipt=json.loads((directory/'release.json').read_text())
    require(receipt['version']==version and receipt['sha256']==digest,'Release receipt mismatch')
    with tempfile.TemporaryDirectory(prefix='kai downloaded release ') as temp:
        root=Path(temp)
        with zipfile.ZipFile(archive) as z:
            for item in z.infolist():
                rel=Path(item.filename)
                require(not rel.is_absolute() and '..' not in rel.parts,'Unsafe release path')
                require(not item.is_dir(),'Unexpected directory entry')
                target=root/rel;target.parent.mkdir(parents=True,exist_ok=True)
                target.write_bytes(z.read(item));target.chmod((item.external_attr>>16)&0o777)
        plugin=root/'plugins/kai-icloud-calendar'
        require(json.loads((plugin/'plugin.json').read_text())['version']==version,'Manifest version mismatch')
        validate(plugin)
        app=plugin/'server/native/Kai Apple Calendar Helper.app'
        subprocess.run(['xcrun','stapler','validate',str(app)],check=True)
        subprocess.run(['spctl','--assess','--type','execute',str(app)],check=True)
    print('PASS: downloaded archive, receipt, checksum, signature, notarization and Gatekeeper')


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('directory',type=Path);p.add_argument('--version',required=True)
    a=p.parse_args();verify(a.directory,a.version)
