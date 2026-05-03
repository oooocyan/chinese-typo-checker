"""
口语/书面语规则
"""
from typing import Dict, List


class StyleRules:
    """表达风格规则"""

    def __init__(self):
        """初始化"""
        # 口语化词汇到书面语的映射
        self.oral_to_written = {
            "啥": "什么",
            "咋": "怎么",
            "弄": "做",
            "整": "做",
            "挺": "很",
            "老": "很",
            "贼": "非常",
            "倍儿": "非常",
            "忒": "太",
            "唠": "聊",
            "侃": "聊",
            "忽悠": "欺骗",
            "琢磨": "思考",
            "鼓捣": "摆弄",
            "折腾": "操劳",
        }

        # 常见口语化句式
        self.oral_patterns = [
            ("...呢", "疑问句式"),
            ("...啊", "感叹句式"),
            ("...嘛", "强调句式"),
            ("...呗", "理所当然"),
            ("...啦", "轻松语气"),
        ]

    def get_written_equivalent(self, oral_word: str) -> str:
        """获取口语词的书面语对应"""
        return self.oral_to_written.get(oral_word, oral_word)

    def check_written_style(self, text: str) -> List[Dict]:
        """
        检查文本是否符合书面语规范

        Args:
            text: 输入文本

        Returns:
            问题列表
        """
        issues = []

        for oral_word, written_word in self.oral_to_written.items():
            if oral_word in text:
                # 找到所有出现的位置
                start = 0
                while True:
                    pos = text.find(oral_word, start)
                    if pos == -1:
                        break

                    issues.append({
                        "position": pos,
                        "position_end": pos + len(oral_word),
                        "error_text": oral_word,
                        "type": "表达风格",
                        "suggestion": f"书面语建议用'{written_word}'",
                        "confidence": 0.7
                    })

                    start = pos + 1

        return issues

    def check_oral_style(self, text: str) -> List[Dict]:
        """
        检查文本是否符合口语化风格
        （口语化风格检查较宽松，主要是确保表达自然）

        Args:
            text: 输入文本

        Returns:
            问题列表
        """
        issues = []

        # 口语化风格不需要特别检查
        # 但可以检查是否有过于书面化的表达导致不自然

        return issues

    def get_style_description(self, style_type: str) -> str:
        """获取风格描述"""
        descriptions = {
            "口语化": "使用日常口语词汇和表达，语气轻松自然",
            "书面化": "使用规范的书面语词汇和表达，语气正式",
            "混合": "口语和书面语混合使用",
        }
        return descriptions.get(style_type, "")

    def get_style_rules(self, style_type: str) -> Dict:
        """获取风格对应的检测规则"""
        if style_type == "口语化":
            return {
                "allow_colloquialism": True,
                "strict_grammar": False,
                "check_written_style": False,
            }
        elif style_type == "书面化":
            return {
                "allow_colloquialism": False,
                "strict_grammar": True,
                "check_written_style": True,
            }
        else:  # 混合
            return {
                "allow_colloquialism": True,
                "strict_grammar": False,
                "check_written_style": False,
            }
