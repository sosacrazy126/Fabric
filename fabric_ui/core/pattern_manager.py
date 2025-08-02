from pathlib import Path
from dataclasses import dataclass
from typing import List, Dict, Optional
import time

from fabric_ui.utils.file_utils import SafeFileHandler

@dataclass
class PatternInfo:
    name: str
    display_name: str
    description: str
    category: str
    tags: List[str]
    has_user: bool
    est_tokens: int

class PatternManager:
    def __init__(self, fabric_client=None):
        self.pattern_dir = Path.home() / ".config" / "fabric" / "patterns"
        self._category_map = {
            'analyze_': 'Analysis',
            'create_': 'Creation',
            'extract_': 'Extraction',
            'improve_': 'Enhancement',
            'generate_': 'Generation',
            'summarize_': 'Summarization',
            'explain_': 'Explanation',
            'write_': 'Writing',
            'check_': 'Validation',
            'compare_': 'Comparison',
            'convert_': 'Conversion',
            'ask_': 'Q&A',
            'capture_': 'Documentation',
            'clean_': 'Processing'
        }
        self._cache = {}
        self._cache_time = 0
        self._cache_ttl = 300 # seconds
        self.file_handler = SafeFileHandler()

    def discover(self, force_refresh: bool = False) -> List[PatternInfo]:
        now = time.time()
        if not force_refresh and self._cache and (now - self._cache_time < self._cache_ttl):
            return list(self._cache.values())
        patterns = []
        if not self.pattern_dir.exists():
            self._cache = {}
            self._cache_time = now
            return []
        for pattern_dir in self.pattern_dir.iterdir():
            if not pattern_dir.is_dir():
                continue
            pi = self._extract_pattern_info(pattern_dir)
            if pi:
                patterns.append(pi)
        self._cache = {p.name: p for p in patterns}
        self._cache_time = now
        return patterns

    def search(self, query: str) -> List[PatternInfo]:
        query = query.lower()
        patterns = self.discover()
        results = []
        for p in patterns:
            score = 0
            if query in p.name.lower():
                score += 10
            if query in p.display_name.lower():
                score += 8
            if query in p.description.lower():
                score += 5
            if any(query in t.lower() for t in p.tags):
                score += 3
            if query in p.category.lower():
                score += 2
            if score > 0:
                results.append((p, score))
        results.sort(key=lambda x: (-x[1], x[0].name))
        return [p for p, _ in results]

    def content(self, pattern_name: str) -> Dict[str, str]:
        pd = self.pattern_dir / pattern_name
        out = {}
        s = pd / "system.md"
        u = pd / "user.md"
        if s.exists():
            out["system"] = self.file_handler.read_text_file(s)
        if u.exists():
            out["user"] = self.file_handler.read_text_file(u)
        return out

    def _extract_pattern_info(self, pattern_dir: Path) -> Optional[PatternInfo]:
        system_file = pattern_dir / "system.md"
        user_file = pattern_dir / "user.md"
        if not system_file.exists():
            return None
        system_content = self.file_handler.read_text_file(system_file)
        description = self._extract_description(system_content)
        category = self._determine_category(pattern_dir.name)
        tags = self._extract_tags(pattern_dir.name, system_content)
        has_user = user_file.exists()
        est_tokens = len(system_content) // 4 if system_content else 0
        return PatternInfo(
            name=pattern_dir.name,
            display_name=pattern_dir.name.replace('_', ' ').title(),
            description=description,
            category=category,
            tags=tags,
            has_user=has_user,
            est_tokens=est_tokens
        )

    def _extract_description(self, content: Optional[str]) -> str:
        if not content:
            return "No description available"
        lines = content.split('\n')
        for line in lines:
            line = line.strip()
            if line and not line.startswith('#') and not line.lower().startswith('you are') and len(line) > 20:
                return line[:200] + "..." if len(line) > 200 else line
        return "No description available"

    def _determine_category(self, pattern_name: str) -> str:
        for prefix, cat in self._category_map.items():
            if pattern_name.startswith(prefix):
                return cat
        return 'General'

    def _extract_tags(self, pattern_name: str, content: Optional[str]) -> List[str]:
        tags = set(pattern_name.replace('_', ' ').split())
        if content:
            content_lower = content.lower()
            if "security" in content_lower:
                tags.add("security")
            if "code" in content_lower or "function" in content_lower:
                tags.add("code")
            if "analyze" in content_lower:
                tags.add("analysis")
            if "write" in content_lower or "essay" in content_lower:
                tags.add("writing")
        return sorted(list(tags))