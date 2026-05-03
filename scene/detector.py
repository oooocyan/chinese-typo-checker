"""
自动场景识别模块
"""
from typing import Tuple


class SceneDetector:
    """场景检测器"""

    def __init__(self):
        """初始化"""
        pass

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
        """检测场景类型"""
        # 简单判断
        if '：' in text or ':' in text:
            return "剧本"
        return "小说"

    def _detect_style(self, text: str) -> str:
        """检测表达风格"""
        oral_markers = ["呢", "啊", "吧", "嘛", "呀", "哦"]
        written_markers = ["之", "其", "者", "所", "以", "于"]

        oral_count = sum(text.count(m) for m in oral_markers)
        written_count = sum(text.count(m) for m in written_markers)

        if oral_count > written_count:
            return "口语化"
        return "书面化"
