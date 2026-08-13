# 敏感词检测（基于 AC 自动机）
from __future__ import annotations

from functools import lru_cache
from pathlib import Path

import ahocorasick

# 词库文件：项目根目录 data/sensitive_words.txt
_WORD_FILE = Path(__file__).resolve().parents[2] / "data" / "sensitive_words.txt"


def _load_words() -> list[str]:
    # 读取词库，忽略空行与注释
    if not _WORD_FILE.is_file():
        return []
    words: list[str] = []
    for line in _WORD_FILE.read_text(encoding="utf-8").splitlines():
        word = line.strip()
        if not word or word.startswith("#"):
            continue
        words.append(word.lower())
    return words


@lru_cache(maxsize=1)
def _automaton() -> ahocorasick.Automaton | None:
    # 构建 AC 自动机（进程内缓存；空词库返回 None）
    words = _load_words()
    if not words:
        return None
    automaton = ahocorasick.Automaton()
    for idx, word in enumerate(words):
        automaton.add_word(word, (idx, word))
    automaton.make_automaton()
    return automaton


def find_sensitive(text: str) -> str | None:
    """若包含敏感词则返回命中的词，否则 None。"""
    if not text or not text.strip():
        return None
    automaton = _automaton()
    if automaton is None:
        return None
    normalized = text.strip().lower()
    for _, (_, word) in automaton.iter(normalized):
        return word
    return None


def first_sensitive_in_tags(tags: list[str]) -> str | None:
    """检查标签列表，返回第一个命中的敏感词。"""
    for tag in tags:
        item = (tag or "").strip()
        if not item:
            continue
        hit = find_sensitive(item)
        if hit is not None:
            return hit
    return None
