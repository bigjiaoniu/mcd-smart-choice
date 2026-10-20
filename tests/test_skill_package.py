from pathlib import Path
import json
import subprocess
import sys
import tempfile
import unittest
from zipfile import ZipFile

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
from build_skill_package import build

class SkillPackageTests(unittest.TestCase):
    def test_allowlist_and_standalone_historical_calculation(self):
        with tempfile.TemporaryDirectory() as directory:
            dest=Path(directory)
            package=build(dest/"skill.zip")
            with ZipFile(package) as archive:
                self.assertEqual(set(archive.namelist()), {"SKILL.md", "references/quote-workflow.md", "references/calculation.md", "references/historical-quotes.json", "scripts/adapt_quotes.py", "scripts/compare_quotes.py"})
                archive.extractall(dest/"installed")
            run=subprocess.run([sys.executable,"-E","-s","-B",str(dest/"installed/scripts/adapt_quotes.py"),str(dest/"installed/references/historical-quotes.json")],cwd=dest,capture_output=True,text=True,encoding="utf-8")
            self.assertEqual(run.returncode,0,run.stderr)
            result=json.loads(run.stdout)
            self.assertEqual(result["results"][-1]["same_basket_saving_fen"],200)
            self.assertEqual(result["results"][-1]["over_budget_fen"],140)

    def test_metadata_and_references_are_present(self):
        text=(ROOT/"skills/mcd-smart-choice/SKILL.md").read_text(encoding="utf-8")
        self.assertTrue(text.startswith("---\n"))
        for name in ["description:","description_zh:","description_en:","version:","author:"]:
            self.assertIn(name,text)
        self.assertNotIn("python app.py",text)
        self.assertIn("实时对话会使用宿主模型额度",text)
