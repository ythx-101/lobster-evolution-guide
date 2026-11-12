#!/usr/bin/env python3
"""检查 docs/*.md 里所有 ```python 代码块能否通过 compile()（只检查语法，不执行）。"""
import re
import sys
from pathlib import Path

FENCE = re.compile(r"^```python[ \t]*\n(.*?)^```[ \t]*$", re.S | re.M)


def main() -> int:
    docs = Path(__file__).resolve().parent.parent / "docs"
    failed = 0
    for md in sorted(docs.glob("*.md")):
        text = md.read_text(encoding="utf-8")
        for i, m in enumerate(FENCE.finditer(text), 1):
            line = text.count("\n", 0, m.start()) + 1
            label = f"{md.name} 第 {i} 段（第 {line} 行）"
            try:
                compile(m.group(1), label, "exec")
                print(f"ok    {label}")
            except SyntaxError as e:
                failed += 1
                print(f"FAIL  {label}: {e}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
