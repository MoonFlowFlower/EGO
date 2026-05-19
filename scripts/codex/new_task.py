#!/usr/bin/env python3
"""
Create a Codex long-run task directory from repo templates.
"""

from __future__ import annotations

import argparse
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
TEMPLATE_DIR = ROOT / "docs" / "codex" / "templates"
TASK_ROOT = ROOT / "docs" / "codex" / "tasks"
TEMPLATE_MAP = {
    "SPEC.template.md": "SPEC.md",
    "PLAN.template.md": "PLAN.md",
    "IMPLEMENT.template.md": "IMPLEMENT.md",
    "EXPLORE.template.md": "EXPLORE.md",
    "STATUS.template.md": "STATUS.md",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create a Codex long-run task directory")
    parser.add_argument("slug", help="Task slug, used as docs/codex/tasks/<slug>/")
    parser.add_argument("--title", help="Human-readable task title")
    parser.add_argument("--dry-run", action="store_true", help="Print actions without writing files")
    return parser.parse_args()


def render_template(text: str, *, slug: str, title: str) -> str:
    today = datetime.now().strftime("%Y-%m-%d")
    return (
        text.replace("{{TASK_SLUG}}", slug)
        .replace("{{TASK_TITLE}}", title)
        .replace("{{DATE}}", today)
    )


def main() -> int:
    args = parse_args()
    slug = args.slug.strip().strip("/").replace("\\", "/")
    title = args.title or slug.replace("-", " ").replace("_", " ").title()
    task_dir = TASK_ROOT / slug

    print(f"Task root: {task_dir.relative_to(ROOT)}")
    print(f"Title: {title}")
    print(f"Mode: {'dry-run' if args.dry_run else 'write'}")

    if not args.dry_run:
        task_dir.mkdir(parents=True, exist_ok=True)

    created = []
    kept = []
    for template_name, output_name in TEMPLATE_MAP.items():
        template_path = TEMPLATE_DIR / template_name
        output_path = task_dir / output_name
        rendered = render_template(template_path.read_text(encoding="utf-8"), slug=slug, title=title)
        if output_path.exists():
            kept.append(output_path.relative_to(ROOT).as_posix())
            continue
        created.append(output_path.relative_to(ROOT).as_posix())
        if not args.dry_run:
            output_path.write_text(rendered, encoding="utf-8")

    for path in created:
        print(f"created: {path}")
    for path in kept:
        print(f"kept existing: {path}")

    print("\nNext steps:")
    print(f"1. Fill {task_dir.relative_to(ROOT).as_posix()}/SPEC.md")
    print(f"2. Fill {task_dir.relative_to(ROOT).as_posix()}/PLAN.md")
    print(f"3. If task is exploratory, fill {task_dir.relative_to(ROOT).as_posix()}/EXPLORE.md")
    print("4. Lock STATUS.md -> Current milestone")
    print(f"5. Run: python3 scripts/codex/verify_repo.py --mode fast")
    print("6. Prompt Codex with:")
    print("   LONGRUN")
    print(f"   Use skill long-run-execution on docs/codex/tasks/{slug}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
