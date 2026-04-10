#!/usr/bin/env python3
"""
CoPaw Plugin Installer v3.2.2
Marks injection into SOUL.md and AGENTS.md, appending Gatekeeper rules.
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

GATEKEEPER_RULES = """
{MARKER_START}
## 🛡️ Gatekeeper Rules (Auto-Injected by CoPaw)

**安装后添加，请勿手动修改此区域。**

### 核心约束
- 涉及 Agent 注入规则的内容，禁止直接编辑 AGENTS.md / SOUL.md
- 使用 install/uninstall 脚本管理注入规则
- 每次操作前自动创建 .bak 备份

### 版本追踪
- 标记版本: v3.2.2
- 更新时同步修改版本号
{MARKER_END}
""".strip()


def backup_file(path: Path) -> None:
    """Create .bak backup before modifying file."""
    bak_path = path.with_suffix(path.suffix + ".bak")
    shutil.copy2(path, bak_path)


def inject_marker(path: Path) -> bool:
    """Inject gatekeeper rules into MD file if not already present."""
    if not path.exists():
        print(f"[WARN] {path} not found, skipping", file=sys.stderr)
        return False

    content = path.read_text(encoding="utf-8")

    if MARKER_START in content:
        print(f"[INFO] {path.name} already contains marker, skipping install")
        return True

    backup_file(path)

    new_content = (
        content.rstrip("\n")
        + "\n\n"
        + GATEKEEPER_RULES.format(MARKER_START=MARKER_START, MARKER_END=MARKER_END)
        + "\n"
    )
    path.write_text(new_content, encoding="utf-8")
    print(f"[OK] Injected gatekeeper rules into {path.name}")
    return True


def main():
    print(f"CoPaw Plugin Installer v{__version__}")

    for md_path in (AGENTS_MD, SOUL_MD):
        inject_marker(md_path)

    print("[DONE] Installation complete")


if __name__ == "__main__":
    main()
