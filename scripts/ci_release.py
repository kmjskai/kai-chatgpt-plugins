#!/usr/bin/env python3
"""Build, sign, notarize and package in CI; credentials never enter output files."""
import argparse,base64,json,os,re,secrets,shlex,subprocess,tempfile
from pathlib import Path
from package_common import ROOT,PLUGIN,refresh,sha256
from package_plugin import export


def run(command,*,cwd=None,secret=False):
    result=subprocess.run(command,cwd=cwd,text=True,capture_output=True)
    if result.returncode:
        # Never include credential-bearing command arguments in an exception.
        detail='' if secret else result.stderr[-1500:]
        raise RuntimeError(f'{Path(command[0]).name} failed with status {result.returncode}: {detail}')
    return result.stdout


def main():
    p=argparse.ArgumentParser();p.add_argument('--version',required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args()
    version=json.loads((PLUGIN/'plugin.json').read_text())['version']
    if a.version!=version or not re.fullmatch(r'\d{4}\.\d{1,2}\.\d+',version):
        raise SystemExit('Version does not match plugin manifest')
    keys=['MACOS_CERTIFICATE_P12_BASE64','MACOS_CERTIFICATE_PASSWORD','APPLE_NOTARY_KEY_P8_BASE64','APPLE_NOTARY_KEY_ID','APPLE_NOTARY_ISSUER_ID']
    for key in keys:
        if not os.environ.get(key):raise SystemExit('Missing release secret: '+key)
    run(['npm','run','build'],cwd=PLUGIN/'server')
    run(['npm','test'],cwd=PLUGIN/'server')
    original_keychains=shlex.split(run(['security','list-keychains','-d','user']))
    original_default=shlex.split(run(['security','default-keychain','-d','user']))[0]
    with tempfile.TemporaryDirectory(prefix='kai-ci-signing-') as temp:
        work=Path(temp);keychain=work/'release.keychain-db';password=secrets.token_hex(32)
        p12=work/'certificate.p12';key=work/'AuthKey.p8'
        p12.write_bytes(base64.b64decode(os.environ[keys[0]],validate=True))
        key.write_bytes(base64.b64decode(os.environ[keys[2]],validate=True))
        p12.chmod(0o600);key.chmod(0o600)
        try:
            run(['security','create-keychain','-p',password,str(keychain)],secret=True)
            run(['security','set-keychain-settings','-lut','21600',str(keychain)])
            run(['security','unlock-keychain','-p',password,str(keychain)],secret=True)
            run(['security','list-keychains','-d','user','-s',str(keychain),*original_keychains])
            run(['security','default-keychain','-d','user','-s',str(keychain)])
            run(['security','import',str(p12),'-k',str(keychain),'-P',os.environ[keys[1]],'-T','/usr/bin/codesign'],secret=True)
            run(['security','set-key-partition-list','-S','apple-tool:,apple:','-s','-k',password,str(keychain)],secret=True)
            identities=run(['security','find-identity','-v','-p','codesigning',str(keychain)])
            hashes=re.findall(r'\b([A-F0-9]{40})\s+"Developer ID Application:',identities)
            if len(hashes)!=1:raise RuntimeError('Expected one Developer ID Application identity')
            app=PLUGIN/'server/native/Kai Apple Calendar Helper.app'
            if (app/'Contents/Frameworks').exists() or (app/'Contents/PlugIns').exists():
                raise RuntimeError('Nested code requires an explicit signing order')
            run(['codesign','--force','--sign',hashes[0],'--keychain',str(keychain),'--options','runtime','--timestamp',
                 '--entitlements',str(PLUGIN/'server/native/Entitlements.plist'),str(app)])
            run(['codesign','--verify','--deep','--strict',str(app)])
            archive=work/'helper.zip';run(['ditto','-c','-k','--keepParent',str(app),str(archive)])
            auth=['--key',str(key),'--key-id',os.environ[keys[3]],'--issuer',os.environ[keys[4]]]
            submission=json.loads(run(['xcrun','notarytool','submit',str(archive),*auth,'--wait','--timeout','20m','--output-format','json'],secret=True))
            if submission.get('status')!='Accepted':raise RuntimeError('Apple notarization was not accepted')
            run(['xcrun','stapler','staple',str(app)])
            run(['xcrun','stapler','validate',str(app)])
            run(['spctl','--assess','--type','execute',str(app)])
            refresh(PLUGIN,'github-actions/'+os.environ.get('GITHUB_SHA','local'))
            snapshot,zip_path=export(ROOT,a.output.resolve(),distribution=True)
            receipt={'version':version,'source_commit':os.environ.get('GITHUB_SHA'),
                     'notarization_id':submission['id'],'artifact':zip_path.name,'sha256':sha256(zip_path)}
            (a.output/'release.json').write_text(json.dumps(receipt,indent=2)+'\n')
            print('Signed, notarized and verified '+zip_path.name)
        finally:
            for cmd in [ ['security','default-keychain','-d','user','-s',original_default],
                         ['security','list-keychains','-d','user','-s',*original_keychains],
                         ['security','delete-keychain',str(keychain)] ]:
                subprocess.run(cmd,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)


if __name__=='__main__':main()
