import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from package_common import PLUGIN, refresh
from validate_plugin import validate

class PackageFailures(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(prefix='kai payload fault ')
        self.plugin=Path(self.temp.name)/'kai-icloud-calendar'
        shutil.copytree(PLUGIN,self.plugin)
    def tearDown(self): self.temp.cleanup()
    def test_tampered_payload_is_rejected(self):
        (self.plugin/'server/bin/kai-apple-calendar-mcp.js').write_text('// altered\n')
        with self.assertRaisesRegex(ValueError,'hash/inventory'): validate(self.plugin)
    def test_missing_build_source_is_rejected(self):
        (self.plugin/'server/native/main.swift').unlink()
        with self.assertRaisesRegex(ValueError,'Missing file'): validate(self.plugin)
    def test_symlink_is_rejected(self):
        (self.plugin/'server/unexpected-link').symlink_to('/tmp')
        with self.assertRaisesRegex(ValueError,'Symlink'): validate(self.plugin)
    def test_missing_skill_license_is_rejected(self):
        (self.plugin/'skills/kai-apple-calendar/LICENSE').unlink()
        with self.assertRaisesRegex(ValueError,'Missing file'): validate(self.plugin)
    def test_manifest_cannot_use_machine_path(self):
        file=self.plugin/'mcp.json';data=json.loads(file.read_text())
        data['mcpServers']['kai_apple_calendar']['args']=['/private/tmp/a.js']
        file.write_text(json.dumps(data))
        with self.assertRaisesRegex(ValueError,'Non-portable'): validate(self.plugin)
    def test_missing_signed_calendar_entitlement_is_rejected(self):
        app=self.plugin/'server/native/Kai Apple Calendar Helper.app'
        subprocess.run(['codesign','--force','--sign','-',str(app)],check=True,capture_output=True)
        refresh(self.plugin)
        with self.assertRaisesRegex(ValueError,'[Ee]ntitlement'): validate(self.plugin)
    def test_wrong_macos_metadata_is_rejected(self):
        import plistlib
        file=self.plugin/'server/native/Kai Apple Calendar Helper.app/Contents/Info.plist'
        info=plistlib.loads(file.read_bytes());info['LSMinimumSystemVersion']='26.0';file.write_bytes(plistlib.dumps(info))
        refresh(self.plugin)
        with self.assertRaisesRegex(ValueError,'deployment target mismatch'): validate(self.plugin)

if __name__=='__main__': unittest.main()
