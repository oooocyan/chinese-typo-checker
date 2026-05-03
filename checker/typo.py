"""
错别字检测器
"""
import json
from pathlib import Path
from typing import List, Dict, Optional
import re

# 尝试导入 pypinyin，如果失败则提供降级方案
try:
    from pypinyin import pinyin, Style
    HAS_PYPINYIN = True
except ImportError:
    HAS_PYPINYIN = False

# 尝试导入 jieba，如果失败则使用简单分词
try:
    import jieba
    HAS_JIEBA = True
except ImportError:
    HAS_JIEBA = False


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
        # 构建拼音索引（用于同音字检测）
        self.pinyin_index = self._build_pinyin_index()

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

    def _build_pinyin_index(self) -> Dict[str, List[str]]:
        """
        构建拼音到词语的索引
        用于检测同音字错误
        """
        index = {}
        # 从正确词语构建索引
        for wrong_word, info in self.typo_dict.items():
            correct_word = info.get("correct", "")
            if correct_word and HAS_PYPINYIN:
                # 获取正确词语的拼音
                py = self._get_pinyin(correct_word)
                if py not in index:
                    index[py] = []
                if correct_word not in index[py]:
                    index[py].append(correct_word)

        return index

    def _get_pinyin(self, text: str) -> str:
        """获取文本的拼音"""
        if HAS_PYPINYIN:
            result = pinyin(text, style=Style.NORMAL)
            return ''.join([p[0] for p in result])
        return ""

    def check(self, text: str) -> List[Issue]:
        """
        检测文本中的错别字

        Args:
            text: 输入文本

        Returns:
            问题列表
        """
        issues = []

        # 1. 词典精确匹配
        issues.extend(self._dict_match(text))

        # 2. 同音字检测（需要 pypinyin）
        if HAS_PYPINYIN:
            issues.extend(self._pinyin_match(text))

        # 3. "的地得" 检测
        issues.extend(self._check_de_di_de(text))

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

    def _pinyin_match(self, text: str) -> List[Issue]:
        """拼音匹配检测同音字错误"""
        issues = []

        if not HAS_JIEBA:
            return issues

        # 分词
        words = list(jieba.cut(text))

        # 计算每个词的位置
        current_pos = 0
        word_positions = []
        for word in words:
            word_positions.append((word, current_pos))
            current_pos += len(word)

        # 检查每个词
        for word, pos in word_positions:
            if len(word) < 2:  # 单字跳过
                continue

            # 获取词的拼音
            word_pinyin = self._get_pinyin(word)

            # 在拼音索引中查找
            if word_pinyin in self.pinyin_index:
                candidates = self.pinyin_index[word_pinyin]
                if word not in candidates and len(candidates) > 0:
                    # 找到同音的正确词
                    issue = Issue(
                        position=pos,
                        position_end=pos + len(word),
                        error_text=word,
                        error_type="错别字",
                        suggestion="/".join(candidates[:3]),  # 最多显示3个候选
                        confidence=0.6
                    )
                    issues.append(issue)

        return issues

    def _check_de_di_de(self, text: str) -> List[Issue]:
        """
        检测"的地得"误用
        这是一个常见问题，需要特别处理
        """
        issues = []

        # 简单规则检测（后续可以用 AI 增强）
        # 规则：名词前用"的"，动词前用"地"，动词/形容词后用"得"

        # 查找所有的"的"、"地"、"得"
        for i, char in enumerate(text):
            if char in "的地得":
                # 获取上下文
                prev_char = text[i-1] if i > 0 else ""
                next_char = text[i+1] if i < len(text)-1 else ""

                # 简单规则判断
                suggestion = self._suggest_de_di_de(prev_char, char, next_char, text, i)

                if suggestion and suggestion != char:
                    issue = Issue(
                        position=i,
                        position_end=i + 1,
                        error_text=char,
                        error_type="错别字",
                        suggestion=suggestion,
                        confidence=0.7
                    )
                    issues.append(issue)

        return issues

    def _suggest_de_di_de(self, prev: str, current: str, next: str, text: str, pos: int) -> Optional[str]:
        """
        根据"的地得"使用规则给出建议
        这是一个简化版本，实际应用中可以用 AI 增强
        """
        # 常见形容词词尾
        adj_suffixes = "美丽快乐伤心愤怒高兴难过着急认真仔细"
        # 常见动词
        verbs = "跑走说看听想做学用吃喝玩写读"

        # 如果后面是动词，建议用"地"
        if next in verbs and current == "的":
            return "地"

        # 如果后面是名词，建议用"的"
        if next and '一' <= next <= '鿿' and next not in verbs:
            if current == "地":
                return "的"

        return None

    def get_confusion_info(self, word1: str, word2: str) -> Optional[Dict]:
        """获取易混淆词对的解释"""
        key = f"{word1}/{word2}"
        return self.confusion_dict.get(key)
