"""Build a source review ZIP from tracked files; this is not an installer."""
import argparse
import subprocess
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FILES = {
    "main.py", "startup.py", "extension.json", "pyproject.toml", "uv.lock",
    "requirements.txt", "LICENSE", "README.md", "PRIVACY.md", "SECURITY.md",
    "mcp-tool-manifest.json",
}
PREFIXES = ("revit_mcp/", "tools/", "MCP.tab/", "images/", "docs/", "scripts/")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    files = subprocess.check_output(["git", "ls-files", "-z"], cwd=ROOT).decode().split("\0")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(args.output, "w", zipfile.ZIP_DEFLATED) as archive:
        for name in sorted(files):
            if name in FILES or name.startswith(PREFIXES):
                archive.write(ROOT / name, "revit-mcp-python.extension/" + name)
    print("Source review package: " + str(args.output))


if __name__ == "__main__":
    main()
