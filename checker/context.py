"""
上下文语义检验器
"""
from typing import List, Optional
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


class ContextChecker:
    """上下文语义检验器"""

    def __init__(self):
        """初始化检查器"""
        # 人称代词
        self.pronouns = {
            "第一人称": ["我", "我们", "咱们", "自己"],
            "第二人称": ["你", "您", "你们"],
            "第三人称": ["他", "她", "它", "他们", "她们", "它们"],
        }

        # 时间词
        self.time_words = ["今天", "昨天", "明天", "现在", "以前", "以后", "刚才", "后来"]

    def check(self, text: str) -> List[Issue]:
        """
        检测文本中的语义问题

        Args:
            text: 输入文本

        Returns:
            问题列表
        """
        issues = []

        # 1. 检测人称不一致
        issues.extend(self._check_pronoun_consistency(text))

        # 2. 检测时态不一致
        issues.extend(self._check_tense_consistency(text))

        # 3. 检测口语化表达
        issues.extend(self._check_colloquialism(text))

        return issues

    def _check_pronoun_consistency(self, text: str) -> List[Issue]:
        """检测人称不一致"""
        issues = []

        # 统计各人称的使用次数
        pronoun_counts = {k: 0 for k in self.pronouns}

        for category, pronouns in self.pronouns.items():
            for pronoun in pronouns:
                pronoun_counts[category] += text.count(pronoun)

        # 如果同时大量使用第一人称和第三人称，可能存在问题
        # 这是一个简化的检查，实际应用中需要更复杂的分析
        total = sum(pronoun_counts.values())
        if total > 10:  # 只有当代词数量足够多时才检查
            first_ratio = pronoun_counts["第一人称"] / total
            third_ratio = pronoun_counts["第三人称"] / total

            # 如果两种人称占比都比较高（超过30%），可能存在问题
            if first_ratio > 0.3 and third_ratio > 0.3:
                # 找到第一个第三人称的位置作为标记
                for pronoun in self.pronouns["第三人称"]:
                    pos = text.find(pronoun)
                    if pos != -1:
                        issue = Issue(
                            position=pos,
                            position_end=pos + len(pronoun),
                            error_text=pronoun,
                            error_type="语义",
                            suggestion="人称可能不一致，请检查叙述视角",
                            confidence=0.5
                        )
                        issues.append(issue)
                        break

        return issues

    def _check_tense_consistency(self, text: str) -> List[Issue]:
        """检测时态不一致"""
        issues = []

        # 简化版本：检测时间词混用
        # 实际应用中可以用 AI 进行更准确的判断
        past_markers = ["昨天", "以前", "刚才", "曾经", "已经"]
        future_markers = ["明天", "以后", "将要", "准备"]

        has_past = any(marker in text for marker in past_markers)
        has_future = any(marker in text for marker in future_markers)

        # 如果同时有过去和未来的标记，可能存在时态混乱
        if has_past and has_future:
            # 找到相关位置
            for marker in past_markers + future_markers:
                pos = text.find(marker)
                if pos != -1:
                    issue = Issue(
                        position=pos,
                        position_end=pos + len(marker),
                        error_text=marker,
                        error_type="语义",
                        suggestion="可能存在时态不一致，请检查时间线",
                        confidence=0.4
                    )
                    issues.append(issue)
                    break

        return issues

    def _check_colloquialism(self, text: str) -> List[Issue]:
        """检测口语化表达"""
        issues = []

        # 常见的口语化表达
        colloquialisms = {
            "贼": "非常",  # 如"贼好" → "非常好"
            "老": "很",    # 如"老好了" → "很好了"
            "倍儿": "非常", # 如"倍儿棒" → "非常棒"
            "忒": "太",    # 如"忒好了" → "太好了"
        }

        for colloquial, formal in colloquialisms.items():
            # 查找口语词
            start = 0
            while True:
                pos = text.find(colloquial, start)
                if pos == -1:
                    break

                # 检查上下文，确认是口语化用法
                next_char = text[pos + len(colloquial)] if pos + len(colloquial) < len(text) else ""

                # 如果后面是形容词，可能是口语化用法
                if next_char and ('一' <= next_char <= '鿿'):
                    issue = Issue(
                        position=pos,
                        position_end=pos + len(colloquial),
                        error_text=colloquial,
                        error_type="语义",
                        suggestion=f"口语化表达，书面语建议用'{formal}'",
                        confidence=0.6
                    )
                    issues.append(issue)

                start = pos + 1

        return issues
