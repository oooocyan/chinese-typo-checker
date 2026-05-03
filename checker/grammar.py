"""
语法检查器
"""
from typing import List
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


class GrammarChecker:
    """语法检查器"""

    def __init__(self):
        """初始化检查器"""
        # 冗余词模式
        self.redundant_patterns = [
            (r'大约.+左右', '大约和左右语义重复'),
            (r'大约.+上下', '大约和上下语义重复'),
        ]

    def check(self, text: str) -> List[Issue]:
        """
        检测文本中的语法问题

        Args:
            text: 输入文本

        Returns:
            问题列表
        """
        issues = []

        # 检测冗余表达
        issues.extend(self._check_redundancy(text))

        return issues

    def _check_redundancy(self, text: str) -> List[Issue]:
        """检测冗余表达"""
        issues = []

        for pattern, message in self.redundant_patterns:
            matches = re.finditer(pattern, text)
            for match in matches:
                issue = Issue(
                    position=match.start(),
                    position_end=match.end(),
                    error_text=match.group(),
                    error_type="语法",
                    suggestion=message,
                    confidence=0.75
                )
                issues.append(issue)

        return issues
