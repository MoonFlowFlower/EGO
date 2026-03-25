"""
OpenEmotion Agent Runtime - Profile Memory

User profile memory for preferences, default rules, and stable background.
"""

from typing import Optional, Dict, Any
import json

from app.memory.types import MemoryEntry, MemoryType
from app.memory.memory_manager import get_memory_manager


class ProfileMemory:
    """
    Profile memory for user preferences.
    
    Stores:
    - User preferences
    - Default rules
    - Communication style
    - Timezone
    - Language preferences
    """
    
    KEY_PREFERENCES = "user_preferences"
    KEY_RULES = "default_rules"
    KEY_STYLE = "communication_style"
    
    def __init__(self, user_id: str):
        """
        Initialize profile memory.
        
        Args:
            user_id: User identifier
        """
        self.user_id = user_id
        self.manager = get_memory_manager()
    
    def _make_key(self, key: str) -> str:
        """Create user-specific key."""
        return f"profile:{self.user_id}:{key}"
    
    def set_preference(self, key: str, value: Any) -> str:
        """Set a user preference."""
        prefs = self.get_all_preferences()
        prefs[key] = value
        
        entry = MemoryEntry(
            id=f"profile_{self.user_id}_prefs",
            type=MemoryType.PROFILE,
            key=self._make_key(self.KEY_PREFERENCES),
            content=json.dumps(prefs, ensure_ascii=False),
            metadata={"user_id": self.user_id}
        )
        return self.manager.write(entry)
    
    def get_preference(self, key: str, default: Any = None) -> Any:
        """Get a user preference."""
        prefs = self.get_all_preferences()
        return prefs.get(key, default)
    
    def get_all_preferences(self) -> Dict[str, Any]:
        """Get all preferences."""
        entry = self.manager.get_by_key(self._make_key(self.KEY_PREFERENCES))
        if entry:
            try:
                return json.loads(entry.content)
            except:
                return {}
        return {}
    
    def add_rule(self, rule: str) -> str:
        """Add a default rule."""
        rules = self.get_rules()
        if rule not in rules:
            rules.append(rule)
        
        entry = MemoryEntry(
            id=f"profile_{self.user_id}_rules",
            type=MemoryType.PROFILE,
            key=self._make_key(self.KEY_RULES),
            content=json.dumps(rules, ensure_ascii=False),
            metadata={"user_id": self.user_id}
        )
        return self.manager.write(entry)
    
    def get_rules(self) -> list[str]:
        """Get default rules."""
        entry = self.manager.get_by_key(self._make_key(self.KEY_RULES))
        if entry:
            try:
                return json.loads(entry.content)
            except:
                return []
        return []
    
    def set_communication_style(self, style: str) -> str:
        """Set preferred communication style."""
        entry = MemoryEntry(
            id=f"profile_{self.user_id}_style",
            type=MemoryType.PROFILE,
            key=self._make_key(self.KEY_STYLE),
            content=style,
            metadata={"user_id": self.user_id}
        )
        return self.manager.write(entry)
    
    def get_communication_style(self) -> Optional[str]:
        """Get preferred communication style."""
        entry = self.manager.get_by_key(self._make_key(self.KEY_STYLE))
        return entry.content if entry else None
    
    def get_summary(self) -> str:
        """Get profile summary for context injection."""
        lines = [f"User ID: {self.user_id}"]
        
        prefs = self.get_all_preferences()
        if prefs:
            lines.append(f"Preferences: {json.dumps(prefs, ensure_ascii=False)[:200]}")
        
        rules = self.get_rules()
        if rules:
            lines.append(f"Rules: {', '.join(rules[:5])}")
        
        style = self.get_communication_style()
        if style:
            lines.append(f"Style: {style}")
        
        return '\n'.join(lines)
