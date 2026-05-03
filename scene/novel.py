"""
小说场景规则
"""
from typing import List, Dict
import re


class NovelChecker:
    """小说场景检查器"""

    def __init__(self):
        """初始化"""
        # 引号模式
        self.quote_pattern = r'["「『]([^"」』]+)["」』]'

    def check(self, text: str) -> List[Dict]:
        """
        检查小说格式问题

        Args:
            text: 输入文本

        Returns:
            问题列表
        """
        issues = []

        # 1. 检查对话与叙述比例
        issues.extend(self._check_dialogue_ratio(text))

        # 2. 检查段落长度
        issues.extend(self._check_paragraph_length(text))

        # 3. 检查叙述视角一致性
        issues.extend(self._check_narrative_perspective(text))

        return issues

    def _check_dialogue_ratio(self, text: str) -> List[Dict]:
        """检查对话与叙述的比例"""
        issues = []

        # 提取对话内容
        dialogues = re.findall(self.quote_pattern, text)
        dialogue_length = sum(len(d) for d in dialogues)

        # 计算对话比例
        total_length = len(text.replace('\n', '').replace(' ', ''))
        if total_length > 0:
            dialogue_ratio = dialogue_length / total_length

            # 如果对话过多或过少，给出建议
            if dialogue_ratio > 0.7:
                issues.append({
                    "type": "结构建议",
                    "message": "对话占比过高（超过70%），建议增加叙述描写",
                    "confidence": 0.6
                })
            elif dialogue_ratio < 0.1:
                issues.append({
                    "type": "结构建议",
                    "message": "对话占比过低（低于10%），建议适当增加对话",
                    "confidence": 0.6
                })

        return issues

    def _check_paragraph_length(self, text: str) -> List[Dict]:
        """检查段落长度"""
        issues = []

        paragraphs = [p for p in text.split('\n') if p.strip()]

        if not paragraphs:
            return issues

        # 计算平均段落长度
        avg_length = sum(len(p) for p in paragraphs) / len(paragraphs)

        # 检查是否有过长或过短的段落
        for i, para in enumerate(paragraphs):
            para_length = len(para)

            if para_length > 500:
                issues.append({
                    "type": "段落长度",
                    "message": f"第{i+1}段落过长（{para_length}字），建议分段",
                    "confidence": 0.5
                })
            elif para_length < 10 and i > 0 and i < len(paragraphs) - 1:
                # 中间的极短段落可能是问题
                issues.append({
                    "type": "段落长度",
                    "message": f"第{i+1}段落过短（{para_length}字），请检查是否遗漏内容",
                    "confidence": 0.4
                })

        return issues

    def _check_narrative_perspective(self, text: str) -> List[Dict]:
        """检查叙述视角一致性"""
        issues = []

        # 检测第一人称
        first_person_markers = ["我", "我们", "我的", "我们的"]
        first_person_count = sum(text.count(m) for m in first_person_markers)

        # 检测第三人称
        third_person_markers = ["他", "她", "它", "他们", "她们", "它们"]
        third_person_count = sum(text.count(m) for m in third_person_markers)

        total = first_person_count + third_person_count

        if total > 20:  # 只有代词足够多时才检查
            first_ratio = first_person_count / total
            third_ratio = third_person_count / total

            # 如果两种人称占比都比较高，可能存在视角混乱
            if first_ratio > 0.3 and third_ratio > 0.3:
                issues.append({
                    "type": "叙述视角",
                    "message": "叙述视角可能不一致，建议统一使用第一人称或第三人称",
                    "confidence": 0.5
                })

        return issues
