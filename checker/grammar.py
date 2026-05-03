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
        # 常见语法错误模式
        self.error_patterns = [
            # 双重否定
            (r'不.*?不.*?(?!是)', "可能存在双重否定，建议检查语义"),
            # 主语重复
            (r'([^，。！？\n]{2,})\1', "可能存在主语重复"),
        ]

        # 冗余词模式
        self.redundant_patterns = [
            (r'大约.+左右', "约'和'左右'语义重复"),
            (r'大约.+上下', "约'和'上下'语义重复"),
            (r'接近.+左右', "近'和'左右'语义重复"),
            (r'更加.+更加', "可能存在重复"),
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

        # 1. 检测冗余表达
        issues.extend(self._check_redundancy(text))

        # 2. 检测重复词语
        issues.extend(self._check_repetition(text))

        # 3. 检测常见的语法错误模式
        issues.extend(self._check_patterns(text))

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

    def _check_repetition(self, text: str) -> List[Issue]:
        """检测重复词语"""
        issues = []

        # 检测连续重复的词（2字以上）
        pattern = r'([^，。！？\s\n]{2,})\1'
        matches = re.finditer(pattern, text)

        for match in matches:
            # 排除一些允许重复的情况（如"天天"、"年年"等叠词）
            word = match.group(1)
            if self._is_valid_reduplication(word):
                continue

            issue = Issue(
                position=match.start(),
                position_end=match.end(),
                error_text=match.group(),
                error_type="语法",
                suggestion=f"词语重复，建议删除重复的'{word}'",
                confidence=0.7
            )
            issues.append(issue)

        return issues

    def _is_valid_reduplication(self, word: str) -> bool:
        """判断是否是合法的叠词"""
        # 常见的合法叠词
        valid_reduplications = {
            "天天", "年年", "月月", "日日", "时时",
            "人人", "处处", "事事", "物物",
            "渐渐", "慢慢", "快快", "好好", "轻轻",
            "高高", "低低", "大大", "小小", "多多",
            "想想", "看看", "听听", "说说", "写写",
            "走走", "跑跑", "跳跳", "笑笑", "哭哭",
        }
        return word in valid_reduplications

    def _check_patterns(self, text: str) -> List[Issue]:
        """检测常见语法错误模式"""
        issues = []

        for pattern, message in self.error_patterns:
            matches = re.finditer(pattern, text)
            for match in matches:
                issue = Issue(
                    position=match.start(),
                    position_end=match.end(),
                    error_text=match.group(),
                    error_type="语法",
                    suggestion=message,
                    confidence=0.6
                )
                issues.append(issue)

        return issues
