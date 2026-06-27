from __future__ import annotations

from pathlib import Path

FORBIDDEN_PATTERNS = (
    "from " + "app.",
    "import " + "app.",
    "legacy" + "_",
    "Api" + "Response",
    "normalize" + "_response_envelope",
)


def test_src_and_tests_do_not_reference_old_app_package() -> None:
    backend_root = Path(__file__).resolve().parents[1]
    checked_roots = [backend_root / "src", backend_root / "tests"]
    offenders: list[str] = []

    for root in checked_roots:
        for path in root.rglob("*.py"):
            if "__pycache__" in path.parts:
                continue
            text = path.read_text(encoding="utf-8")
            for pattern in FORBIDDEN_PATTERNS:
                if pattern in text:
                    offenders.append(f"{path.relative_to(backend_root).as_posix()}: {pattern}")

    assert not offenders, "Old app references remain:\n" + "\n".join(offenders)


