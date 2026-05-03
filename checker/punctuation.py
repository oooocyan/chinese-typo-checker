"""
标点符号检查器
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


class PunctuationChecker:
    """标点符号检查器"""

    def __init__(self):
        """初始化检查器"""
        # 中文标点
        self.chinese_puncts = set("。，、；：？！""''（）【】《》—…")
        # 英文标点
        self.english_puncts = set(".,;:?!\"\"''()[]<>")
        # 成对标点
        self.paired_puncts = {
            """: """,
            "「": "」",
            "『": "』",
            "(": ")",
            "（": "）",
            "【": "】",
            "《": "》",
            "\"": "\"",
            "'": "'",
        }
        # 英文标点到中文标点的映射
        self.english_to_chinese = {
            ",": "，",
            ".": "。",
            ";": "；",
            ":": "：",
            "?": "？",
            "!": "！",
            "(": "（",
            ")": "）",
            "[": "【",
            "]": "】",
            "<": "《",
            ">": "》",
        }

    def check(self, text: str) -> List[Issue]:
        """
        检测文本中的标点问题

        Args:
            text: 输入文本

        Returns:
            问题列表
        """
        issues = []

        # 1. 中英文标点混用检测
        issues.extend(self._check_mixed_punct(text))

        # 2. 成对标点配对检测
        issues.extend(self._check_paired_punct(text))

        # 3. 连续重复标点检测
        issues.extend(self._check_repeated_punct(text))

        # 4. 句末标点缺失检测
        issues.extend(self._check_end_punct(text))

        return issues

    def _check_mixed_punct(self, text: str) -> List[Issue]:
        """检测中英文标点混用"""
        issues = []

        # 判断文本主要是中文还是英文
        chinese_count = sum(1 for c in text if '一' <= c <= '鿿')
        total_count = len(text.replace(" ", "").replace("\n", ""))

        # 如果中文占主导（超过50%），检查英文标点
        if total_count > 0 and chinese_count / total_count > 0.5:
            for i, char in enumerate(text):
                if char in self.english_puncts:
                    # 检查是否在数字上下文中（如小数点）
                    if char == '.' and i > 0 and i < len(text) - 1:
                        if text[i-1].isdigit() and text[i+1].isdigit():
                            continue  # 跳过小数点

                    # 建议改为中文标点
                    chinese_equiv = self.english_to_chinese.get(char, char)
                    if chinese_equiv != char:
                        issue = Issue(
                            position=i,
                            position_end=i + 1,
                            error_text=char,
                            error_type="标点",
                            suggestion=chinese_equiv,
                            confidence=0.85
                        )
                        issues.append(issue)

        return issues

    def _check_paired_punct(self, text: str) -> List[Issue]:
        """检测成对标点是否配对"""
        issues = []

        for open_punct, close_punct in self.paired_puncts.items():
            # 统计开闭标点数量
            open_count = text.count(open_punct)
            close_count = text.count(close_punct)

            if open_count != close_count:
                # 找到不配对的位置
                if open_count > close_count:
                    # 开标点多，找到最后出现的开标点
                    last_open = text.rfind(open_punct)
                    issue = Issue(
                        position=last_open,
                        position_end=last_open + 1,
                        error_text=open_punct,
                        error_type="标点",
                        suggestion=f"缺少配对的 {close_punct}",
                        confidence=0.9
                    )
                    issues.append(issue)
                else:
                    # 闭标点多，找到第一个出现的闭标点
                    first_close = text.find(close_punct)
                    issue = Issue(
                        position=first_close,
                        position_end=first_close + 1,
                        error_text=close_punct,
                        error_type="标点",
                        suggestion=f"缺少配对的 {open_punct}",
                        confidence=0.9
                    )
                    issues.append(issue)

        return issues

    def _check_repeated_punct(self, text: str) -> List[Issue]:
        """检测连续重复的标点"""
        issues = []

        # 匹配连续重复的标点（省略号除外）
        pattern = r'([。，、；：？！,;:?!.])\1{2,}'
        matches = re.finditer(pattern, text)

        for match in matches:
            punct = match.group(1)
            # 省略号用三个点是可以的
            if punct == '.' and len(match.group()) == 3:
                continue

            issue = Issue(
                position=match.start(),
                position_end=match.end(),
                error_text=match.group(),
                error_type="标点",
                suggestion=punct if punct in self.chinese_puncts else self.english_to_chinese.get(punct, punct),
                confidence=0.8
            )
            issues.append(issue)

        return issues

    def _check_end_punct(self, text: str) -> List[Issue]:
        """检测句末标点缺失"""
        issues = []

        # 按段落检查
        paragraphs = text.split('\n')

        current_pos = 0
        for para in paragraphs:
            para = para.strip()
            if para:
                # 检查段落末尾是否有标点
                last_char = para[-1] if para else ""
                if last_char and last_char not in self.chinese_puncts and last_char not in self.english_puncts:
                    # 可能缺少句末标点
                    issue = Issue(
                        position=current_pos + len(para) - 1,
                        position_end=current_pos + len(para),
                        error_text="(无)",
                        error_type="标点",
                        suggestion="句末缺少标点符号",
                        confidence=0.6
                    )
                    issues.append(issue)

            current_pos += len(para) + 1  # +1 for newline

        return issues
