"""
Context Manager for Cloudkot
Handles context window tracking and compression
"""

import hashlib
import time
from collections import deque
from pathlib import Path

from compat import tomllib
from pydantic import BaseModel


class ContextItem(BaseModel):
    """Represents an item in the context window"""

    content: str
    role: str  # user, assistant, system
    token_count: int
    importance: float = 1.0  # 0-1, higher = more important
    timestamp: float = 0.0


class ContextManager:
    def __init__(self, config_path: str = "config.toml"):
        self.config_path = Path(config_path)
        self.max_tokens: int = 32768
        self.compression_enabled: bool = True
        self.compression_threshold: float = 0.8
        self.current_tokens: int = 0
        self.context_window: deque[ContextItem] = deque()
        self.token_counts: dict[str, int] = {}  # Cache for token counts
        self._tokenizer = self._load_tokenizer()
        self._load_config()

    def _load_tokenizer(self):
        """Load tiktoken encoder, fall back to None"""
        try:
            import tiktoken
            return tiktoken.get_encoding("cl100k_base")
        except (ImportError, Exception):
            return None

    def _load_config(self):
        """Load configuration from config file"""
        if not self.config_path.exists():
            return

        try:
            with open(self.config_path, "rb") as f:
                config = tomllib.load(f)

            if "context" in config:
                self.max_tokens = config["context"].get("max_tokens", 32768)
                self.compression_enabled = config["context"].get("compression_enabled", True)
                self.compression_threshold = config["context"].get("compression_threshold", 0.8)
                self.current_tokens = config["context"].get("current_tokens", 0)
        except Exception as e:
            print(f"Warning: Could not load context config: {e}")

    def _count_tokens(self, text: str) -> int:
        """Count tokens accurately using tiktoken, or approximate with fallback"""
        if self._tokenizer:
            return len(self._tokenizer.encode(text))
        # Fallback: character-based estimation (~4 chars per token)
        # For very short texts, ensure at least 1 token
        char_count = len(text)
        estimated = char_count // 4
        return max(1, estimated) if char_count > 0 else 0

    def add_context(self, content: str, role: str, importance: float = 1.0) -> ContextItem:
        """Add a new item to the context window"""
        token_count = self._count_tokens(content)
        item = ContextItem(
            content=content,
            role=role,
            token_count=token_count,
            importance=importance,
            timestamp=time.time(),
        )

        # Check if we need to compress before adding
        if self.compression_enabled and self._should_compress(token_count):
            self._compress_context()

        self.context_window.append(item)
        self.current_tokens += token_count

        return item

    def _should_compress(self, additional_tokens: int = 0) -> bool:
        """Check if context should be compressed"""
        total_after_add = self.current_tokens + additional_tokens
        return total_after_add > (self.max_tokens * self.compression_threshold)

    def _compress_context(self):
        """Compress the context window by removing less important items"""
        if not self.context_window:
            return

        now = time.time()

        # Score: importance * recency_weight (items within 5 min get a bonus)
        def score(item: ContextItem) -> float:
            age = now - item.timestamp
            recency_bonus = 1.5 if age < 300 else 1.0  # 5 min boost
            return item.importance * recency_bonus

        # Sort by score descending, keeping most valuable
        sorted_context = sorted(self.context_window, key=score, reverse=True)

        # Keep top 50% highest-scored items, at least 1
        keep_count = max(1, len(sorted_context) // 2)

        # Rebuild context window preserving chronological order within kept items
        kept_ids = {id(item) for item in sorted_context[:keep_count]}
        new_window = deque()
        new_token_count = 0

        for item in self.context_window:
            if id(item) in kept_ids:
                new_window.append(item)
                new_token_count += item.token_count

        self.context_window = new_window
        self.current_tokens = new_token_count

    def get_context(self, max_tokens: int | None = None) -> list[dict[str, str]]:
        """Get the current context as a list of messages"""
        if max_tokens is None:
            max_tokens = self.max_tokens

        result = []
        current_count = 0

        # Return context in chronological order
        for item in self.context_window:
            if current_count + item.token_count > max_tokens:
                break
            result.append(
                {
                    "role": item.role,
                    "content": item.content,
                }
            )
            current_count += item.token_count

        return result

    def get_token_count(self) -> int:
        """Get the current token count"""
        return self.current_tokens

    def get_utilization(self) -> float:
        """Get the current context window utilization (0-1)"""
        return self.current_tokens / self.max_tokens if self.max_tokens > 0 else 0

    def clear_context(self):
        """Clear the context window"""
        self.context_window.clear()
        self.current_tokens = 0

    def summarize_context(self) -> str:
        """Create a summary of the current context"""
        if not self.context_window:
            return ""

        # Simple summary: concatenate user messages
        user_messages = [item.content for item in self.context_window if item.role == "user"]
        return " \n".join(user_messages[-3:])  # Last 3 user messages

    def get_context_hash(self) -> str:
        """Get a hash of the current context for caching"""
        context_str = "|".join([f"{item.role}:{item.content}" for item in self.context_window])
        return hashlib.md5(context_str.encode()).hexdigest()


# Singleton instance
context_manager = ContextManager()
