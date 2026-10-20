"""Build a standalone WorkBuddy upload ZIP from an explicit public allowlist."""
import argparse
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

ROOT = Path(__file__).resolve().parents[1]

def build(output):
    source = ROOT / "skills/mcd-smart-choice"
    entries = {"SKILL.md": source / "SKILL.md"}
    for item in sorted((source / "references").glob("*.md")):
        entries["references/" + item.name] = item
    for name in ("adapt_quotes.py", "compare_quotes.py"):
        entries["scripts/" + name] = ROOT / "scripts" / name
    entries["references/historical-quotes.json"] = ROOT / "examples/coupon-price-only.json"
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    with ZipFile(output, "w", ZIP_DEFLATED) as archive:
        for name, path in entries.items():
            archive.writestr(name, path.read_bytes())
    return output

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="生成 WorkBuddy 独立技能导入包，不含凭证和本地数据")
    parser.add_argument("--output", required=True, type=Path)
    print(build(parser.parse_args().output))
