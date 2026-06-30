"""路径安全校验工具。

防止用户输入的相对路径越出允许的内容根目录（如 ../../../etc/passwd），
所有对外部路径做拼接的服务方法均应经此校验。
"""

from pathlib import Path


class PathSecurityError(ValueError):
    """目标路径越出允许目录时抛出。"""


def ensure_child_path(base_dir: Path, target_path: Path) -> Path:
    """校验 target_path 位于 base_dir 内部（含等于 base_dir 本身），通过则返回其绝对路径。

    通过 resolve() 解析真实路径后再比较，可规避符号链接与 `..` 拼接造成的穿越。
    """
    base_dir = base_dir.resolve()
    target_path = target_path.resolve()

    # 等于根目录，或根目录是其父级之一，视为合法
    if target_path == base_dir or base_dir in target_path.parents:
        return target_path

    raise PathSecurityError(f"Path is outside allowed directory: {target_path}")
