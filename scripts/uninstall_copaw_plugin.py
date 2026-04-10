#!/usr/bin/env python3
"""
CoPaw Plugin Uninstaller v3.2.2
Removes injected gatekeeper rules from SOUL.md and AGENTS.md.
"""

import re
import shutil
import sys
from pathlib import Path

__version__ = "3.2.2"

MARKER_START = "<!-- 🟢 COPAW_EVOLUTION_INJECT_START (v3.2.2) -->"
MARKER_END = "<!-- 🔴 COPAW_EVOLUTION_INJECT_END -->"

AGENTS_MD = (
    Path.home() / ".copaw" / "workspaces" / "CoPaw_QA_Agent_0.1beta1" / "AGENTS.md"
)
SOUL_MD = Path.home() / ".copaw" / "workspaces" / "CoPaw_QA_Agent_0.1beta1" / "SOUL.md"


def backup_file(path: Path) -> None:
    """Create .bak backup before modifying file."""
    bak_path = path.with_suffix(path.suffix + ".bak")
    shutil.copy2(path, bak_path)


def clean_inject(path: Path) -> bool:
    """Remove injected marker block from MD file."""
    if not path.exists():
        print(f"[WARN] {path} not found, skipping", file=sys.stderr)
        return False

    content = path.read_text(encoding="utf-8")

    if MARKER_START not in content:
        print(f"[WARN] {path.name} has no marker, skipping uninstall")
        return False

    backup_file(path)

    cleaned = re.sub(
        r"\n?" + re.escape(MARKER_START) + r".*?" + re.escape(MARKER_END) + r"\n?",
        "\n",
        content,
        flags=re.DOTALL,
    )
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned).rstrip("\n") + "\n"
    path.write_text(cleaned, encoding="utf-8")
    print(f"[OK] Removed marker from {path.name}")
    return True


def main():
    print(f"CoPaw Plugin Uninstaller v{__version__}")

    for md_path in (AGENTS_MD, SOUL_MD):
        clean_inject(md_path)

    print("[DONE] Uninstallation complete")


if __name__ == "__main__":
    main()
