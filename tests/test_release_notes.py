import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from extract_release_notes import extract

class ReleaseNotes(unittest.TestCase):
    def test_extracts_only_requested_version(self):
        self.assertEqual(extract('# Changelog\n## 2026.10.0\n- New\n## 2026.9.0\n- Old\n','2026.10.0'),'- New\n')
    def test_rejects_missing_or_duplicate_version(self):
        for text in ['## 2026.9.0\n- Old','## 2026.10.0\n- A\n## 2026.10.0\n- B']:
            with self.assertRaises(ValueError):extract(text,'2026.10.0')
    def test_rejects_empty_version(self):
        with self.assertRaises(ValueError):extract('## 2026.10.0\n\n','2026.10.0')

if __name__=='__main__':unittest.main()
