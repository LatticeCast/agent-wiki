"""CLI entry point for knowledge linting."""
import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "build"))
sys.path.insert(0, str(ROOT))
from lint.wiki import has_findings, lint_wiki  # noqa: E402


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="wiki-lint")
    parser.add_argument("--root", default="wiki")
    parser.add_argument("--warn-only", action="store_true")
    args = parser.parse_args(argv)
    report = lint_wiki(args.root)
    print(json.dumps(report, sort_keys=True, indent=2))
    return 0 if args.warn_only or not has_findings(report) else 1


if __name__ == "__main__":
    sys.exit(main())
