"""
剧本场景规则
"""
from typing import List, Dict
import re


class ScriptChecker:
    """剧本场景检查器"""

    def __init__(self):
        """初始化"""
        # 人物名称模式
        self.character_pattern = r'[^\n：:\s]{2,4}[：:]'

        # 舞台说明标记
        self.stage_directions = ["（", "）", "【", "】", "〔", "〕"]

    def check(self, text: str) -> List[Dict]:
        """
        检查剧本格式问题

        Args:
            text: 输入文本

        Returns:
            问题列表
        """
        issues = []

        # 1. 检查人物名称一致性
        issues.extend(self._check_character_consistency(text))

        # 2. 检查舞台说明格式
        issues.extend(self._check_stage_directions(text))

        return issues

    def _check_character_consistency(self, text: str) -> List[Dict]:
        """检查人物名称一致性"""
        issues = []

        # 提取所有人物名称
        characters = re.findall(self.character_pattern, text)
        characters = [c.replace('：', '').replace(':', '') for c in characters]

        # 统计人物名称出现次数
        from collections import Counter
        char_counts = Counter(characters)

        # 检查是否有相似的人物名称（可能是笔误）
        char_list = list(char_counts.keys())
        for i, char1 in enumerate(char_list):
            for char2 in char_list[i+1:]:
                # 如果两个名字只有一个字不同
                if self._is_similar(char1, char2):
                    issues.append({
                        "type": "人物名称",
                        "message": f"人物名称可能不一致：'{char1}' 和 '{char2}'",
                        "confidence": 0.7
                    })

        return issues

    def _is_similar(self, str1: str, str2: str) -> bool:
        """判断两个字符串是否相似（只有一个字符不同）"""
        if len(str1) != len(str2):
            return False

        diff_count = sum(1 for a, b in zip(str1, str2) if a != b)
        return diff_count == 1

    def _check_stage_directions(self, text: str) -> List[Dict]:
        """检查舞台说明格式"""
        issues = []

        # 检查舞台说明标记是否配对
        pairs = [("（", "）"), ("【", "】"), ("〔", "〕")]

        for open_mark, close_mark in pairs:
            open_count = text.count(open_mark)
            close_count = text.count(close_mark)

            if open_count != close_count:
                issues.append({
                    "type": "舞台说明格式",
                    "message": f"舞台说明标记不配对：'{open_mark}' {open_count} 个，'{close_mark}' {close_count} 个",
                    "confidence": 0.9
                })

        return issues
