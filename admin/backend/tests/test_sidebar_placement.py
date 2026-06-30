"""Sidebar 写入落点回归测试。

验证 ``SidebarService.ensure_doc_id`` 在不同分类深度下都能把 doc_id 写到
``sidebars.ts`` 的正确分类层级，且不破坏括号结构。覆盖历史上出过问题的三类场景：

- 已有叶子分类下追加（append 快乐路径）
- 已有 2 级分类下新建 3 级子分类（原 BUG1：深层新建子分类落点错误）
- 已有 1 级分类下新建 2 级子分类（原 BUG2/3：双重缩进 + 闭合括号缩进丢失）
- 全新顶级分类（追加新侧边栏分组）

独立可运行（无需 pytest）：

    cd admin/backend
    python -m tests.test_sidebar_placement
"""

from __future__ import annotations

import re
import sys
import tempfile
from pathlib import Path

# 以脚本方式运行时，把 admin/backend 注入 sys.path，使 `from scr...` 可解析
BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from scr.core.config import settings  # noqa: E402
from scr.services.content.sidebar_service import SidebarService  # noqa: E402


# 与真实 site/sidebars.ts 同构的最小样本（含 3 层嵌套与一个普通 docs 项）
BASE_SIDEBARS = """\
import type {SidebarsConfig} from '@docusaurus/plugin-content-docs';

const sidebars: SidebarsConfig = {
  overviewSidebar: [
    'intro',
  ],

  techStudySidebar: [
    {
      type: 'category',
      label: '技术研习',
      collapsed: false,
      items: [
        {
          type: 'category',
          label: 'Java 面试题',
          collapsed: false,
          items: [
            {
              type: 'category',
              label: 'Java 基础',
              collapsed: false,
              items: [
                'tech-study/java-interview/java-basic/java-vs-cpp',
              ],
            },
          ],
        },
      ],
    },
  ],

  resourceSharingSidebar: [
    {
      type: 'category',
      label: '资源分享',
      collapsed: false,
      items: [
        'resource-sharing/toolbox',
      ],
    },
  ],
};

export default sidebars;
"""


def _enclosing_labels(content: str, doc_id: str) -> list[str]:
    """返回 doc_id 在结构上所属的分类 label 链（由内到外）。

    依据缩进推断嵌套层级：从 doc_id 所在行向上扫描，每遇到一个缩进更浅的
    ``label:`` 行即视作更外一层的祖先分类。要求样本使用规范的 2 空格缩进。
    """
    lines = content.splitlines()
    target = next((i for i, line in enumerate(lines) if f"'{doc_id}'" in line), -1)
    if target == -1:
        return []

    threshold = len(lines[target]) - len(lines[target].lstrip())
    chain: list[str] = []
    for line in lines[:target][::-1]:
        indent = len(line) - len(line.lstrip())
        match = re.match(r"\s*label:\s*'([^']*)'", line)
        if match and indent < threshold:
            chain.append(match.group(1))
            threshold = indent
    return chain


def _brackets_balanced(content: str) -> bool:
    """粗略校验括号是否平衡（先剔除字符串字面量，避免其中括号干扰计数）。"""
    stripped = re.sub(r"'(?:\\.|[^'\\])*'", "''", content)
    stripped = re.sub(r'"(?:\\.|[^"\\])*"', '""', stripped)
    return stripped.count("[") == stripped.count("]") and stripped.count("{") == stripped.count("}")


def _run_scenario(name: str, doc_id: str, labels: list[str], expected_chain: list[str]) -> None:
    original_sidebars_path = settings.sidebars_path
    try:
        with tempfile.TemporaryDirectory() as tmp:
            sidebar_file = Path(tmp) / "sidebars.ts"
            sidebar_file.write_text(BASE_SIDEBARS, encoding="utf-8")
            object.__setattr__(settings, "sidebars_path", sidebar_file)

            svc = SidebarService()
            category_path = doc_id.split("/")[:-1]
            svc.ensure_doc_id(doc_id, category_path, labels)

            content = sidebar_file.read_text(encoding="utf-8")
            chain = _enclosing_labels(content, doc_id)

            assert chain == expected_chain, (
                f"[{name}] 落点分类链不符\n  期望(内→外): {expected_chain}\n  实际(内→外): {chain}"
            )
            assert _brackets_balanced(content), f"[{name}] 写入后括号不平衡"
            assert content.count(f"'{doc_id}'") == 1, f"[{name}] doc_id 出现次数不为 1"
            assert doc_id in svc.list_registered_doc_ids(), f"[{name}] doc_id 未登记"
            print(f"[PASS] {name}: {' → '.join(chain)}")
    finally:
        object.__setattr__(settings, "sidebars_path", original_sidebars_path)


def main() -> None:
    _run_scenario(
        "已有叶子分类下追加（append 快乐路径）",
        "tech-study/java-interview/java-basic/new-doc",
        ["技术研习", "Java 面试题", "Java 基础"],
        ["Java 基础", "Java 面试题", "技术研习"],
    )
    _run_scenario(
        "已有 2 级分类下新建 3 级子分类（BUG1）",
        "tech-study/java-interview/new-cat/new-doc",
        ["技术研习", "Java 面试题", "New Cat"],
        ["New Cat", "Java 面试题", "技术研习"],
    )
    _run_scenario(
        "已有 1 级分类下新建 2 级子分类（BUG2/3）",
        "tech-study/new-cat/new-doc",
        ["技术研习", "New Cat"],
        ["New Cat", "技术研习"],
    )
    _run_scenario(
        "全新顶级分类（追加新侧边栏分组）",
        "new-top/new-doc",
        ["New Top"],
        ["New Top"],
    )
    print("\n全部通过 ✅")


if __name__ == "__main__":
    main()
