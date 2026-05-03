"""
自动场景识别模块
"""
from typing import Tuple, Dict
import re


class SceneDetector:
    """场景检测器"""

    def __init__(self):
        """初始化"""
        # 场景特征关键词
        self.scene_keywords = {
            "剧本": {
                "markers": ["（", "）", "：", "【", "】", "幕", "场", "旁白", "独白"],
                "dialogue_pattern": r'[^\n]+[：:][^\n]+',  # 对话模式
            },
            "小说": {
                "markers": ["他", "她", "它", "他们", "她们", "说", "道", "想"],
                "narrative_pattern": r'[^"「『]+[。！？]',  # 叙述模式
            },
        }

        # 口语化特征
        self.oral_markers = [
            "呢", "啊", "吧", "嘛", "呀", "哦", "哈", "哎", "喂",
            "啥", "咋", "弄", "整", "挺", "老", "贼", "倍儿",
            "呗", "咯", "喽", "咧", "哇", "喏",
        ]

        # 书面化特征
        self.written_markers = [
            "之", "其", "者", "所", "以", "于", "而", "且", "但",
            "若", "则", "虽", "因", "故", "即", "乃", "亦",
        ]

    def detect(self, text: str) -> Tuple[str, str]:
        """
        检测文本的场景类型和表达风格

        Args:
            text: 输入文本

        Returns:
            (场景类型, 表达风格)
        """
        scene_type = self._detect_scene_type(text)
        style_type = self._detect_style(text)

        return (scene_type, style_type)

    def _detect_scene_type(self, text: str) -> str:
        """
        检测场景类型

        Returns:
            "剧本" / "小说" / "散文" / "其他"
        """
        scores = {"剧本": 0, "小说": 0}

        # 计算剧本特征得分
        script_patterns = self.scene_keywords["剧本"]
        for marker in script_patterns["markers"]:
            scores["剧本"] += text.count(marker)

        # 检测对话模式
        dialogue_matches = re.findall(script_patterns["dialogue_pattern"], text)
        scores["剧本"] += len(dialogue_matches) * 2

        # 计算小说特征得分
        novel_patterns = self.scene_keywords["小说"]
        for marker in novel_patterns["markers"]:
            scores["小说"] += text.count(marker)

        # 检测叙述模式
        narrative_matches = re.findall(novel_patterns["narrative_pattern"], text)
        scores["小说"] += len(narrative_matches)

        # 判断结果
        if scores["剧本"] > scores["小说"] * 1.5:
            return "剧本"
        elif scores["小说"] > scores["剧本"]:
            return "小说"
        else:
            # 检查是否有对话
            if '"' in text or '"' in text or "「" in text:
                return "小说"
            return "散文"

    def _detect_style(self, text: str) -> str:
        """
        检测表达风格

        Returns:
            "口语化" / "书面化" / "混合"
        """
        oral_count = 0
        written_count = 0

        # 统计口语化标记
        for marker in self.oral_markers:
            oral_count += text.count(marker)

        # 统计书面化标记
        for marker in self.written_markers:
            written_count += text.count(marker)

        # 计算比例
        total = oral_count + written_count
        if total == 0:
            return "书面化"  # 默认

        oral_ratio = oral_count / total

        if oral_ratio > 0.6:
            return "口语化"
        elif oral_ratio < 0.3:
            return "书面化"
        else:
            return "混合"

    def get_scene_info(self, scene_type: str, style_type: str) -> Dict:
        """
        获取场景检测的详细信息
        """
        return {
            "scene_type": scene_type,
            "style_type": style_type,
            "description": self._get_description(scene_type, style_type),
            "rules": self._get_rules(scene_type, style_type),
        }

    def _get_description(self, scene_type: str, style_type: str) -> str:
        """获取场景描述"""
        descriptions = {
            ("剧本", "口语化"): "剧本格式，对话为主，口语化表达",
            ("剧本", "书面化"): "剧本格式，对话为主，书面化表达",
            ("小说", "口语化"): "小说格式，叙述为主，口语化表达",
            ("小说", "书面化"): "小说格式，叙述为主，书面化表达",
            ("散文", "口语化"): "散文格式，口语化表达",
            ("散文", "书面化"): "散文格式，书面化表达",
        }
        return descriptions.get((scene_type, style_type), "标准文本")

    def _get_rules(self, scene_type: str, style_type: str) -> Dict:
        """获取场景对应的检测规则"""
        rules = {
            "allow_colloquialism": style_type == "口语化",
            "strict_grammar": style_type == "书面化",
            "check_dialogue_format": scene_type == "剧本",
            "check_narrative_flow": scene_type in ["小说", "散文"],
        }
        return rules
