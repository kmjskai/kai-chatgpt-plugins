#!/usr/bin/env python3
"""Validate distributable files and relocated MCP startup without calendar access."""
import argparse
import json
import os
import plistlib
import re
import shutil
import subprocess
import tempfile
from pathlib import Path
from package_common import ROOT, PLUGIN, inventory, helper_metadata, sha256


def require(condition, message):
    if not condition:
        raise ValueError(message)


def validate(plugin):
    manifest = json.loads((plugin / 'plugin.json').read_text())
    require(manifest['name'] == 'kai-icloud-calendar', 'Plugin identity mismatch')
    require(manifest.get('license') == 'Apache-2.0', 'Plugin license missing')
    require(manifest['extensions']['com.openai']['requires_local_executor'], 'Local executor required')
    for rel in ['LICENSE', 'NOTICE', 'README.md', 'README.en.md', 'server/native/main.swift',
                'server/native/Entitlements.plist', 'server/scripts/build.sh', 'server/scripts/install-codex.sh', 'server/test/server.test.js',
                'skills/kai-apple-calendar/LICENSE']:
        require((plugin / rel).is_file(), f'Missing file: {rel}')
    require('Apache License' in (plugin / 'LICENSE').read_text(), 'Invalid license text')
    config = json.loads((plugin / 'mcp.json').read_text())['mcpServers']['kai_apple_calendar']
    require(config['type'] == 'stdio' and config['command'] == 'node', 'Wrong MCP transport')
    require(config['args'] == ['${PLUGIN_ROOT}/server/bin/kai-apple-calendar-mcp.js'], 'Non-portable MCP path')
    require(config['cwd'] == '${PLUGIN_ROOT}', 'Non-portable working directory')
    data = json.loads((plugin / 'provenance.json').read_text())
    require(inventory(plugin) == data['sha256'], 'Payload hash/inventory mismatch')
    require(sha256(plugin / 'skills/kai-apple-calendar/SKILL.md') == data['skill']['source_skill_sha256'], 'Skill content changed')
    observed = helper_metadata(plugin)
    require(observed == data['helper'], 'Binary metadata mismatch')
    require(observed['architecture'] == 'arm64', 'This candidate supports arm64 only')
    require(observed['minimum_macos'] == ['14.0'], 'Binary deployment target must be macOS 14.0')
    require(observed['plist_minimum_macos'] == '14.0', 'Info.plist deployment target mismatch')
    require(observed['bundle_id'] == 'com.yingkaisun.kaiapplecalendar.helper', 'Helper identity changed')
    exe = plugin / 'server/native/Kai Apple Calendar Helper.app/Contents/MacOS/calendar-helper'
    require(os.access(exe, os.X_OK), 'Helper executable permission lost')
    entitlements=subprocess.run(['codesign','-d','--entitlements',':-',str(exe.parent.parent.parent)],capture_output=True,check=True).stdout
    require(bool(entitlements),'Signed entitlement payload missing')
    signed=plistlib.loads(entitlements)
    require(signed.get('com.apple.security.personal-information.calendars') is True,'Signed calendar entitlement missing')
    for p in plugin.rglob('*'):
        if any(x in {'.build', '__pycache__'} for x in p.relative_to(plugin).parts):
            continue
        require(not p.is_symlink(), f'Symlink: {p.name}')
        if p.is_file() and p.suffix in ['.json', '.yaml', '.md', '.js', '.py', '.sh', '.swift']:
            text = p.read_text()
            require(('/' + 'Users/') not in text, f'Personal absolute path: {p.name}')
            require(not re.search(r'-----BEGIN (?:RSA |EC )?PRIVATE KEY-----|gh[pousr]_[A-Za-z0-9]{25,}',text), f'Credential marker: {p.name}')
    with tempfile.TemporaryDirectory(prefix='kai plugin relocated ') as temp:
        moved = Path(temp) / plugin.name
        shutil.copytree(plugin, moved)
        app = moved / 'server/native/Kai Apple Calendar Helper.app'
        subprocess.run(['codesign', '--verify', '--deep', '--strict', str(app)], check=True)
        requests = [
            {'jsonrpc':'2.0','id':1,'method':'initialize','params':{'protocolVersion':'2025-06-18'}},
            {'jsonrpc':'2.0','method':'notifications/initialized'},
            {'jsonrpc':'2.0','id':2,'method':'tools/list','params':{}}]
        command = [config['command'], *[s.replace('${PLUGIN_ROOT}',str(moved)) for s in config['args']]]
        result = subprocess.run(command,cwd=moved,input=''.join(json.dumps(x)+'\n' for x in requests),
                                capture_output=True,text=True,timeout=15,check=True)
        replies = {x['id']:x for x in map(json.loads,result.stdout.splitlines())}
        require(replies[1]['result']['serverInfo']['name']=='kai-apple-calendar','Unexpected MCP')
        tools = replies[2]['result']['tools']
        require([t['name'] for t in tools]==['list_calendars','list_events','create_event'],'Tool surface changed')
        require(all(t['annotations']['readOnlyHint'] for t in tools[:2]),'Read annotations changed')
        require(not tools[2]['annotations']['idempotentHint'],'Creation must not be retried blindly')
    return observed


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--plugin',type=Path,default=PLUGIN)
    args=parser.parse_args()
    observed=validate(args.plugin.resolve())
    print('PASS: licenses, source completeness, payload hashes, binary target, relocation and MCP protocol')
    print('Signing state:', observed['signature'])


if __name__=='__main__':
    main()
