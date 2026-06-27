# 博客目录自动更新 — 文件系统实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 实现文章发布/删除/修改时自动同步更新 `index.md` 目录文件

**Architecture:** 纯函数式引擎（输入 index.md 文本 + 操作指令 → 输出修改后文本），在 `services/index_updater.py` 中实现，集成到 `routers/files.py` 的现有路由

**Tech Stack:** Python 3.10+, FastAPI, Pydantic, dataclasses, re (正则)

**Spec 文件:** `docs/superpowers/specs/2026-06-08-auto-index-design-local.md`

**关键参考文件：**
- 现有路由：`backend/app/routers/files.py`
- 数据模型：`backend/app/schemas.py`
- 配置：`backend/app/config.py`（`BLOG_ROOT`, `POSTS_DIR`, `PREFIX_TO_DIR`）
- FM 服务：`backend/app/services/frontmatter.py`
- index.md 实际文件：`blog/source/_posts/index.md`

---

## 文件结构

| 文件 | 职责 | 操作 |
|------|------|------|
| `backend/app/services/index_updater.py` | 核心引擎：解析、序列化、增删改查 | 新建 |
| `backend/app/routers/files.py` | 集成调用点 | 修改 |
| `backend/tests/__init__.py` | 测试包 | 新建 |
| `backend/tests/conftest.py` | 测试 fixtures（样本 index.md） | 新建 |
| `backend/tests/test_index_parser.py` | 解析器 + 序列化测试 | 新建 |
| `backend/tests/test_index_helpers.py` | 辅助函数测试 | 新建 |
| `backend/tests/test_index_operations.py` | 增删改操作测试 | 新建 |

---

## 依赖关系

```
Task 1 (数据结构 + 解析/序列化)
  ↓
Task 2 (辅助函数)
  ↓ ↓
Task 3 (add)  Task 4 (remove)    ← 可并行
  ↓ ↓          ↓ ↓
Task 5 (update + status_change)
  ↓
Task 6 (集成到 files.py)
  ↓
Task 7 (端到端验证)
```

---

### Task 1: 数据结构 + 解析器 + 序列化器

**Files:**
- Create: `backend/app/services/index_updater.py`
- Create: `backend/tests/__init__.py`
- Create: `backend/tests/conftest.py`
- Create: `backend/tests/test_index_parser.py`

**参考 Spec 章节:** 3.2（目录结构解析）、3.5（序列化规则）

- [ ] **Step 1: 定义数据结构**

使用 dataclasses 定义：

```python
from dataclasses import dataclass, field

@dataclass
class Article:
    line: str  # 原始链接行，如 "- [标题](/URL/)"

@dataclass
class Subcategory:
    number: str          # "1.1"
    title: str           # "AI 探索"
    heading: str         # 原始标题行 "### 1.1 AI 探索"
    articles: list[Article] = field(default_factory=list)

@dataclass
class PrimaryCategory:
    number: str          # "一"
    title: str           # "技术研习"
    heading: str         # 原始标题行 "## 一、技术研习"
    subcategories: list[Subcategory] = field(default_factory=list)
    placeholder: str | None = None  # "*暂无文章，敬请期待*" 或 None

@dataclass
class IndexStructure:
    front_matter: str     # front matter 原始文本（含 --- 分隔符）
    categories: list[PrimaryCategory] = field(default_factory=list)
    footer: str = ""      # 末尾 "*持续更新，记录成长*" 等内容
    unknown_lines: list[str] = field(default_factory=list)  # 无法识别的行，原样保留
```

- [ ] **Step 2: 实现 `parse_index(index_text: str) -> IndexStructure`**

核心解析逻辑：
1. 分离 front matter（`---` 之间的内容原样保留）和 body
2. 逐行解析 body，用正则匹配：
   - `## {中文序号}、{名称}` → PrimaryCategory
   - `### {数字}.{数字} {名称}` → Subcategory
   - `- [{标题}](/{URL}/)` → Article
   - `*暂无文章，敬请期待*` → 设置 placeholder
   - `####` 开头的行及后续内容 → 归入 unknown_lines（系列文章组，原样保留）
   - `---` 分隔符 → 原样保留
   - 其他行 → 归入 unknown_lines
3. 容错：无法识别的行不报错，归入 unknown_lines

- [ ] **Step 3: 实现 `serialize(structure: IndexStructure) -> str`**

将 IndexStructure 序列化回 markdown：
1. 输出 front_matter 原文
2. 遍历 categories，每个 PrimaryCategory：
   - 输出 heading
   - 如果有 subcategories → 遍历输出
   - 如果只有 placeholder → 输出占位文字
   - 如果有 unknown_lines → 在合适位置原样插入
3. PrimaryCategory 之间用 `---` 分隔
4. 输出 footer

- [ ] **Step 4: 写测试 `test_index_parser.py`**

在 `conftest.py` 中创建 fixture `sample_index_md`（一个包含 3 个一级分类、每个有 2-3 个二级分类的完整样本 index.md）

测试用例：
- `test_parse_basic_structure` — 解析后结构正确（分类数量、标题、文章数）
- `test_parse_placeholder` — 空分类正确解析为 placeholder
- `test_parse_preserves_unknown_lines` — 无法识别的行被保留
- `test_roundtrip` — parse → serialize → parse，两次解析结果一致
- `test_preserves_front_matter` — front matter 原样保留

- [ ] **Step 5: 运行测试确认通过**

```bash
cd e:/A-Code/blog/admin-dev/backend
D:/Program-Files/A-Programming-software/Anaconda/envs/python310/python.exe -m pytest tests/test_index_parser.py -v
```

- [ ] **Step 6: 提交**

```bash
git add backend/app/services/index_updater.py backend/tests/
git commit -m "feat: 新增 index.md 解析器和序列化器"
```

---

### Task 2: 辅助函数

**Files:**
- Modify: `backend/app/services/index_updater.py`
- Create: `backend/tests/test_index_helpers.py`

**参考 Spec 章节:** 3.4（辅助函数）

- [ ] **Step 1: 实现辅助函数**

```python
import re
from typing import Optional

# --- 中文序号映射 ---
_CHINESE_NUMBERS = ["一","二","三","四","五","六","七","八","九","十",
                    "十一","十二","十三","十四","十五"]

def number_to_chinese(n: int) -> str:
    """数字 → 中文序号（1→一, 2→二, ...），超过映射表动态生成"""
    if 1 <= n <= len(_CHINESE_NUMBERS):
        return _CHINESE_NUMBERS[n - 1]
    return str(n)  # 超出范围用数字

def chinese_to_number(chinese: str) -> int:
    """中文序号 → 数字（一→1, 二→2, ...）"""
    if chinese in _CHINESE_NUMBERS:
        return _CHINESE_NUMBERS.index(chinese) + 1
    return 0

# --- 链接生成 ---
def generate_link_line(date: str, category_slug: str, filename: str, title: str) -> str:
    """
    生成目录链接行
    date = "2026-06-08 15:30:00" → "- [标题](/2026/06/08/slug/filename/)"
    """
    pass  # 实现细节见 spec 3.4

# --- 链接匹配 ---
def match_link_by_filename(text: str, filename: str) -> Optional[re.Match]:
    """用文件名匹配目录中的链接，正则: - \[.*?\]\(/.*?/{filename}/\)"""
    pass

def count_links_by_filename(text: str, filename: str) -> int:
    """统计文件名匹配到的链接数（用于检测重复）"""
    pass

# --- 分类名匹配 ---
def find_primary_category(structure: IndexStructure, category_name: str) -> Optional[PrimaryCategory]:
    """用中文分类名匹配一级分类（contains 匹配）"""
    pass

def find_subcategory(primary: PrimaryCategory, sub_name: str) -> Optional[Subcategory]:
    """匹配二级分类"""
    pass

# --- 编号工具 ---
def get_next_chinese_number(structure: IndexStructure) -> str:
    """获取下一个一级分类中文序号"""
    pass

def get_next_sub_number(primary: PrimaryCategory) -> str:
    """获取下一个二级分类编号（如当前最大 1.3 → 返回 1.4）"""
    pass

def renumber_subcategories(primary: PrimaryCategory) -> None:
    """重新编号二级分类（消除间隙，如 1.1, 1.3 → 1.1, 1.2）"""
    pass
```

- [ ] **Step 2: 写测试 `test_index_helpers.py`**

- `test_number_to_chinese` — 1→一, 5→五, 15→十五
- `test_chinese_to_number` — 反向测试
- `test_generate_link_line` — 正常日期、带时间日期
- `test_match_link_by_filename_found` — 匹配成功
- `test_match_link_by_filename_not_found` — 匹配失败
- `test_count_links_duplicate` — 检测重复链接
- `test_find_primary_category` — 中文分类名匹配
- `test_renumber_subcategories` — 消除间隙

- [ ] **Step 3: 运行测试确认通过**

```bash
D:/Program-Files/A-Programming-software/Anaconda/envs/python310/python.exe -m pytest tests/test_index_helpers.py -v
```

- [ ] **Step 4: 提交**

```bash
git add backend/app/services/index_updater.py backend/tests/test_index_helpers.py
git commit -m "feat: 新增目录更新辅助函数"
```

---

### Task 3: add_to_index（插入文章链接）

**Files:**
- Modify: `backend/app/services/index_updater.py`
- Modify: `backend/tests/test_index_operations.py`（追加测试）

**参考 Spec 章节:** 3.3①、5.3（匹配错误）、5.4（幂等性）

- [ ] **Step 1: 实现 `add_to_index`**

```python
def add_to_index(
    index_text: str,
    title: str,
    date: str,
    categories: list[str],
    filename: str,
    category_slug: str,
) -> tuple[str, str]:
    """
    插入文章链接到目录。
    Returns: (new_index_text, message)
    """
    # 1. 解析 index → IndexStructure
    # 2. 检查幂等性：文件名已存在 → 静默跳过
    # 3. 匹配一级分类（categories[0]）
    #    - 找到 → 继续
    #    - 没找到 → 自动追加新一级分类（spec 5.3）
    # 4. 匹配二级分类（categories[1]）
    #    - 找到 → 尾插到 articles 末尾
    #    - 没找到 → 新建二级分类（spec 规则 7）
    #    - categories 只有 1 级 → 用一级分类名作为二级（spec 5.3）
    # 5. 清除 placeholder
    # 6. 序列化返回
```

- [ ] **Step 2: 写测试**

- `test_add_to_existing_subcategory` — 追加到已有二级分类
- `test_add_creates_new_subcategory` — 自动创建新二级分类
- `test_add_creates_new_primary_category` — 自动创建新一级分类
- `test_add_idempotent` — 重复添加静默跳过
- `test_add_removes_placeholder` — 添加时清除占位符
- `test_add_missing_categories` — 缺少 categories 字段时报错
- `test_add_missing_date` — 日期格式异常时报错

- [ ] **Step 3: 运行测试确认通过**

```bash
D:/Program-Files/A-Programming-software/Anaconda/envs/python310/python.exe -m pytest tests/test_index_operations.py::test_add -v
```

- [ ] **Step 4: 提交**

```bash
git add backend/app/services/index_updater.py backend/tests/test_index_operations.py
git commit -m "feat: 实现文章目录插入功能"
```

---

### Task 4: remove_from_index（移除文章链接）

**Files:**
- Modify: `backend/app/services/index_updater.py`
- Modify: `backend/tests/test_index_operations.py`（追加测试）

**参考 Spec 章节:** 3.3②、规则 9（二级分类清空时移除并重编号）、规则 10（一级分类清空时恢复占位符）

- [ ] **Step 1: 实现 `remove_from_index`**

```python
def remove_from_index(
    index_text: str,
    filename: str,
) -> tuple[str, str]:
    """
    从目录移除文章链接。
    Returns: (new_index_text, message)
    """
    # 1. 解析 index → IndexStructure
    # 2. 遍历找到文件名匹配的链接并移除
    # 3. 匹配到多条 → 终止报错（spec 5.3）
    # 4. 匹配零条 → 静默跳过
    # 5. 二级分类 articles 为空 → 移除该二级分类
    # 6. 对该一级分类下剩余二级分类重新编号
    # 7. 一级分类下所有二级为空 → 恢复占位符
    # 8. 序列化返回
```

- [ ] **Step 2: 写测试**

- `test_remove_existing_article` — 正常移除
- `test_remove_empty_subcategory_removed` — 二级分类清空时自动移除
- `test_remove_renumbers_subcategories` — 移除后重新编号（1.1,1.3 → 1.1,1.2）
- `test_remove_restores_placeholder` — 一级分类清空时恢复占位符
- `test_remove_not_found_silent` — 不存在的文章静默跳过
- `test_remove_duplicate_filename_error` — 重复文件名时报错

- [ ] **Step 3: 运行测试确认通过**

```bash
D:/Program-Files/A-Programming-software/Anaconda/envs/python310/python.exe -m pytest tests/test_index_operations.py::test_remove -v
```

- [ ] **Step 4: 提交**

```bash
git add backend/app/services/index_updater.py backend/tests/test_index_operations.py
git commit -m "feat: 实现文章目录移除功能"
```

---

### Task 5: update_in_index + handle_status_change

**Files:**
- Modify: `backend/app/services/index_updater.py`
- Modify: `backend/tests/test_index_operations.py`（追加测试）

**参考 Spec 章节:** 3.3③④、6.2（分类变更）

- [ ] **Step 1: 实现 `update_in_index`**

```python
def update_in_index(
    index_text: str,
    old_filename: str,
    new_title: str,
    new_date: str,
    new_categories: list[str],
    new_filename: str,
    new_category_slug: str,
) -> tuple[str, str]:
    """
    更新目录中的文章链接。
    Returns: (new_index_text, message)
    """
    # 1. 解析 index
    # 2. 对比新旧数据：
    #    - 只变标题 → 更新链接文本
    #    - 变日期 → 更新 URL 日期部分
    #    - 变分类 → remove(旧) + add(新)（spec 3.3③）
    #    - 完全相同 → 跳过（spec 5.4）
    # 3. 序列化返回
```

- [ ] **Step 2: 实现 `handle_status_change`**

```python
def handle_status_change(
    index_text: str,
    title: str,
    date: str,
    categories: list[str],
    filename: str,
    category_slug: str,
    old_status: str,
    new_status: str,
) -> tuple[str, str]:
    """
    根据状态变更决定插入或移除。
    Returns: (new_index_text, message)
    """
    # published → 非published: remove_from_index
    # 非published → published: add_to_index
    # 其他（draft→wip 等）: 不处理，返回原文
```

- [ ] **Step 3: 写测试**

`update_in_index`:
- `test_update_title_only` — 只改标题
- `test_update_date` — 改日期更新 URL
- `test_update_category_move` — 分类变更（remove + add）
- `test_update_no_change` — 无变化时跳过

`handle_status_change`:
- `test_status_draft_to_published` — 插入
- `test_status_published_to_draft` — 移除
- `test_status_published_to_wip` — 移除
- `test_status_draft_to_wip` — 不处理

- [ ] **Step 4: 运行全部测试确认通过**

```bash
D:/Program-Files/A-Programming-software/Anaconda/envs/python310/python.exe -m pytest tests/ -v
```

- [ ] **Step 5: 提交**

```bash
git add backend/app/services/index_updater.py backend/tests/test_index_operations.py
git commit -m "feat: 实现文章目录更新和状态变更处理"
```

---

### Task 6: 集成到 files.py 路由

**Files:**
- Modify: `backend/app/routers/files.py`

**参考 Spec 章节:** 四（集成点）

**前置条件:** Task 1-5 全部完成

- [ ] **Step 1: 在 files.py 顶部导入**

```python
from ..services.index_updater import (
    add_to_index,
    remove_from_index,
    update_in_index,
    handle_status_change,
)
```

- [ ] **Step 2: 添加 INDEX_MD 路径常量**

```python
INDEX_MD = POSTS_DIR / "index.md"
```

- [ ] **Step 3: 添加 `_read_index()` / `_write_index()` 内部工具函数**

```python
def _read_index() -> str | None:
    """读取 index.md 内容，失败返回 None"""
    if not INDEX_MD.exists():
        return None
    return INDEX_MD.read_text(encoding="utf-8")

def _write_index(content: str) -> None:
    """写入 index.md（写前备份，写后验证）"""
    # 实现写前备份 .bak、写入、验证、删除备份的流程
```

- [ ] **Step 4: 修改 `update_post` 路由**

在现有 `full_path.write_text(...)` 之后，添加目录同步逻辑：

```python
# 检测关键字段变化，触发目录更新
old_status = existing_fm.get("status", "draft")
new_status = existing_fm.get("status", "draft")
old_title = existing_fm.get("title", "")
new_title = existing_fm.get("title", "")
# ... 其他字段对比

# 调用 handle_status_change 或 update_in_index
index_text = _read_index()
if index_text is not None:
    # 根据 diff 决定调用哪个函数
    new_index, msg = ...
    _write_index(new_index)
```

**重要**：目录更新失败不应阻断文章保存（try-except 包裹，记录日志）

- [ ] **Step 5: 修改 `delete_post` 路由**

在 `full_path.unlink()` 之后，添加：

```python
# 从目录移除
index_text = _read_index()
if index_text is not None:
    filename = Path(path).stem
    new_index, msg = remove_from_index(index_text, filename)
    _write_index(new_index)
```

- [ ] **Step 6: 手动验证**

启动服务，通过管理后台测试：
1. 发布一篇文章 → 检查 index.md 自动添加
2. 修改标题 → 检查 index.md 同步更新
3. 取消发布 → 检查 index.md 自动移除
4. 删除文章 → 检查 index.md 自动移除

- [ ] **Step 7: 提交**

```bash
git add backend/app/routers/files.py
git commit -m "feat: 集成目录自动更新到文章路由"
```

---

### Task 7: 错误处理 + 端到端验证

**Files:**
- Modify: `backend/app/services/index_updater.py`
- Create: `backend/tests/test_index_errors.py`

**参考 Spec 章节:** 5（错误处理）、6（边界情况）

- [ ] **Step 1: 完善所有错误处理**

对照 spec 第五章，确保以下场景都已处理：

**文件级错误（5.1）：**
- `index.md` 不存在 → 终止
- `index.md` 内容为空 → 终止
- Front Matter 解析失败 → 终止

**解析错误（5.2）：**
- 格式不符合的标题行 → 跳过 + 警告日志
- `####` 系列文章 → 原样保留

**匹配错误（5.3）：**
- 一级分类找不到 → 自动追加
- 二级分类找不到 → 自动创建
- 重复文件名 → 终止报错
- categories 为空 → 终止
- categories 只有一级 → 用一级名作为二级

**幂等性（5.4）：**
- add 时已存在 → 静默跳过
- remove 时不存在 → 静默跳过
- update 无变化 → 跳过

**编号边界（5.5）：**
- 一级分类超过映射表 → 动态生成
- 二级编号 ≥ 10 → 正常处理
- 重编号消除间隙

- [ ] **Step 2: 写边界测试 `test_index_errors.py`**

- `test_index_file_not_exists` — index.md 不存在
- `test_index_empty_body` — body 为空
- `test_no_primary_categories` — 无一级分类
- `test_special_chars_in_title` — 标题含方括号/括号
- `test_many_primary_categories` — 超过 10 个一级分类
- `test_series_articles_preserved` — `####` 系列文章原样保留

- [ ] **Step 3: 运行全部测试**

```bash
D:/Program-Files/A-Programming-software/Anaconda/envs/python310/python.exe -m pytest tests/ -v
```

- [ ] **Step 4: 端到端手动验证**

用真实 index.md 测试完整流程

- [ ] **Step 5: 提交**

```bash
git add backend/app/services/index_updater.py backend/tests/test_index_errors.py
git commit -m "feat: 完善目录更新错误处理和边界情况"
```

