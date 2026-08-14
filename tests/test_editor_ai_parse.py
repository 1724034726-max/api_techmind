# 写作 AI Markdown 解析单测（stdlib unittest，无需 pytest）
import unittest

from app.core.error_codes import ErrorCode
from app.core.exceptions import AppException
from app.services.editor_ai_service import (
    _finalize_plain_md,
    _parse_labeled_sections_md,
    _parse_topic_md,
)


class EditorAiParseTests(unittest.TestCase):
    def test_parse_topic_md_standard(self) -> None:
        raw = """## 洞察

近 30 天竞争中等。

## 切口：对比选型

**标题**：ZGC vs G1
**提示**：决策边界

## 背景

为什么选型总被低估。

## 切口：实战手册

**标题**：五步排查
**提示**：高质量少

1. 进程
2. 火焰图
"""
        vo = _parse_topic_md(raw)
        self.assertIn("竞争", vo.insight)
        self.assertEqual(len(vo.angles), 2)
        self.assertEqual(vo.angles[0].angle, "对比选型")
        self.assertEqual(vo.angles[0].title, "ZGC vs G1")
        self.assertIn("背景", vo.angles[0].outline_md)
        self.assertEqual(vo.angles[1].title, "五步排查")

    def test_parse_topic_md_missing_sections(self) -> None:
        with self.assertRaises(AppException) as ctx:
            _parse_topic_md("只有一段散文，没有约定标题")
        self.assertEqual(ctx.exception.code, ErrorCode.ERR_AI_BAD_RESPONSE.code)

    def test_parse_labeled_sections(self) -> None:
        raw = """## 问题导向

本文说明分布式锁边界。

## 结论先行

WatchDog 不是银弹。

## 场景共鸣

如果你踩过 synchronized 的坑。
"""
        items = _parse_labeled_sections_md(raw)
        self.assertEqual(len(items), 3)
        self.assertEqual(items[0].label, "问题导向")
        self.assertIn("分布式锁", items[0].text)

    def test_parse_labeled_too_few(self) -> None:
        with self.assertRaises(AppException) as ctx:
            _parse_labeled_sections_md("## 只有标题\n")
        self.assertEqual(ctx.exception.code, ErrorCode.ERR_AI_BAD_RESPONSE.code)

    def test_finalize_rejects_json(self) -> None:
        with self.assertRaises(AppException) as ctx:
            _finalize_plain_md('{"appendix_md":"x"}')
        self.assertEqual(ctx.exception.code, ErrorCode.ERR_AI_BAD_RESPONSE.code)

    def test_finalize_ok_markdown(self) -> None:
        self.assertTrue(_finalize_plain_md("## Hello\n\nworld").startswith("## Hello"))


if __name__ == "__main__":
    unittest.main()
