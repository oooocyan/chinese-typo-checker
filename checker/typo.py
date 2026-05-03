"""
错别字检测器
"""
import json
from pathlib import Path
from typing import List, Dict, Optional
import re


class Issue:
    """问题数据类"""
    def __init__(self, position: int, position_end: int, error_text: str,
                 error_type: str, suggestion: str, confidence: float):
        self.position = position
        self.position_end = position_end
        self.error_text = error_text
        self.error_type = error_type
        self.suggestion = suggestion
        self.confidence = confidence


class TypoChecker:
    """错别字检测器"""

    def __init__(self):
        """初始化检测器"""
        # 加载错别字词典
        self.typo_dict = self._load_typo_dict()
        # 加载易混淆词对
        self.confusion_dict = self._load_confusion_dict()

    def _load_typo_dict(self) -> Dict:
        """加载错别字词典"""
        dict_path = Path(__file__).parent.parent / "data" / "typos.json"
        if dict_path.exists():
            with open(dict_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}

    def _load_confusion_dict(self) -> Dict:
        """加载易混淆词对词典"""
        dict_path = Path(__file__).parent.parent / "data" / "confusion.json"
        if dict_path.exists():
            with open(dict_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}

    def check(self, text: str) -> List[Issue]:
        """
        检测文本中的错别字

        Args:
            text: 输入文本

        Returns:
            问题列表
        """
        issues = []

        # 词典精确匹配
        issues.extend(self._dict_match(text))

        return issues

    def _dict_match(self, text: str) -> List[Issue]:
        """词典精确匹配"""
        issues = []

        for wrong_word, info in self.typo_dict.items():
            # 查找错误词在文本中的位置
            start = 0
            while True:
                pos = text.find(wrong_word, start)
                if pos == -1:
                    break

                # 创建问题
                issue = Issue(
                    position=pos,
                    position_end=pos + len(wrong_word),
                    error_text=wrong_word,
                    error_type="错别字",
                    suggestion=info.get("correct", ""),
                    confidence=0.95
                )
                issues.append(issue)

                start = pos + 1

        return issues
