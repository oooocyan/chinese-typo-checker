"""
上下文语义检验器
"""
from typing import List


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


class ContextChecker:
    """上下文语义检验器"""

    def __init__(self):
        """初始化检查器"""
        # 口语化表达
        self.colloquialisms = {
            "贼": "非常",
            "老": "很",
            "忒": "太",
        }

    def check(self, text: str) -> List[Issue]:
        """
        检测文本中的语义问题

        Args:
            text: 输入文本

        Returns:
            问题列表
        """
        issues = []

        # 检测口语化表达
        issues.extend(self._check_colloquialism(text))

        return issues

    def _check_colloquialism(self, text: str) -> List[Issue]:
        """检测口语化表达"""
        issues = []

        for colloquial, formal in self.colloquialisms.items():
            start = 0
            while True:
                pos = text.find(colloquial, start)
                if pos == -1:
                    break

                issue = Issue(
                    position=pos,
                    position_end=pos + len(colloquial),
                    error_text=colloquial,
                    error_type="语义",
                    suggestion=f'口语化表达，书面语建议用{formal}',
                    confidence=0.6
                )
                issues.append(issue)

                start = pos + 1

        return issues
