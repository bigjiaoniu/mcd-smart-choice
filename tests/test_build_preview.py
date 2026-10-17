from pathlib import Path
import sys
import tempfile
import unittest
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
from build_preview import build

class PreviewTests(unittest.TestCase):
    def test_preview_embeds_companion_and_needs_no_external_scripts(self):
        with tempfile.TemporaryDirectory() as directory:
            output=build(Path(directory)/"preview.html")
            html=output.read_text(encoding="utf-8")
            self.assertIn('window.__OFFLINE_DEMOS=',html)
            self.assertIn('id="buddy"',html)
            self.assertIn('root.BuddyRules=',html)
            self.assertNotIn('<script src=',html)
            self.assertNotIn('href="/style.css"',html)
            self.assertNotIn('Authorization',html)
