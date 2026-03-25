from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional


PROMPT_FILENAMES = ["AGENT.md", "SOUL.md", "TOOLS.md"]


@dataclass
class PromptFilesBundle:
    root: str
    loaded: Dict[str, str]

    @property
    def loaded_names(self) -> List[str]:
        return list(self.loaded.keys())

    def render(self) -> str:
        sections: List[str] = []
        for name in PROMPT_FILENAMES:
            content = self.loaded.get(name)
            if not content:
                continue
            sections.append(f"## {name}\n{content.strip()}")
        return "\n\n".join(sections).strip()


class RuntimeV2PromptFiles:
    def __init__(self, root: str | Path | None = None) -> None:
        self.root = Path(root or Path(__file__).resolve().parents[2] / "prompts")
        self._cached_bundle: PromptFilesBundle | None = None

    def load(self, force_reload: bool = False) -> PromptFilesBundle:
        if self._cached_bundle is not None and not force_reload:
            return self._cached_bundle
        loaded: Dict[str, str] = {}
        for name in PROMPT_FILENAMES:
            path = self.root / name
            if path.exists():
                loaded[name] = path.read_text(encoding="utf-8")
        self._cached_bundle = PromptFilesBundle(root=str(self.root), loaded=loaded)
        return self._cached_bundle

    def read_file(self, name: str) -> Optional[str]:
        normalized = name.strip()
        if normalized not in PROMPT_FILENAMES:
            return None
        path = self.root / normalized
        if not path.exists():
            return None
        return path.read_text(encoding="utf-8")

    def reload(self) -> PromptFilesBundle:
        return self.load(force_reload=True)
