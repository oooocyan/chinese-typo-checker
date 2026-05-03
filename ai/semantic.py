"""
语义分析模块
调用大模型进行深度语义分析
"""
from typing import List, Dict, Tuple, Optional
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from config import get_api_key


class SemanticAnalyzer:
    """语义分析器"""

    def __init__(self):
        """初始化"""
        self.api_key = get_api_key()
        self.client = None

        if self.api_key:
            try:
                import dashscope
                dashscope.api_key = self.api_key
                self.client = dashscope
            except ImportError:
                pass

    def is_available(self) -> bool:
        """检查功能是否可用"""
        return self.client is not None

    def analyze_context(self, text: str, context: str = "") -> Dict:
        """
        分析文本的上下文语义

        Args:
            text: 目标文本
            context: 上下文

        Returns:
            分析结果字典
        """
        if not self.is_available():
            return {"available": False}

        try:
            prompt = f"""请分析以下中文文本的语义特征：

文本：
{text}

请返回以下信息（JSON格式）：
{{
  "main_topic": "主要话题",
  "tone": "语气（正式/随意/严肃/轻松等）",
  "style": "风格（口语化/书面化）",
  "key_entities": ["关键实体/人物"],
  "potential_issues": ["可能存在的语义问题"]
}}
"""
            from dashscope import Generation

            response = Generation.call(
                model='qwen-turbo',
                prompt=prompt,
                max_tokens=1000,
                temperature=0.5,
            )

            if response.status_code == 200:
                import json
                result_text = response.output.text
                # 提取 JSON
                json_start = result_text.find('{')
                json_end = result_text.rfind('}') + 1
                if json_start != -1:
                    return json.loads(result_text[json_start:json_end])

        except Exception as e:
            print(f"语义分析出错: {e}")

        return {"available": False}

    def check_coherence(self, text: str) -> List[Dict]:
        """
        检查文本的连贯性

        Returns:
            连贯性问题列表
        """
        if not self.is_available():
            return []

        try:
            prompt = f"""请检查以下中文文本的连贯性和逻辑性：

文本：
{text}

请指出存在的连贯性问题，以 JSON 数组格式返回：
[
  {{
    "position": "问题位置的关键词",
    "issue": "问题描述",
    "suggestion": "修改建议"
  }}
]

如果没有问题，返回空数组 []。
"""

            from dashscope import Generation

            response = Generation.call(
                model='qwen-turbo',
                prompt=prompt,
                max_tokens=1000,
                temperature=0.5,
            )

            if response.status_code == 200:
                import json
                result_text = response.output.text
                json_start = result_text.find('[')
                json_end = result_text.rfind(']') + 1
                if json_start != -1:
                    return json.loads(result_text[json_start:json_end])

        except Exception as e:
            print(f"连贯性检查出错: {e}")

        return []

    def verify_usage(self, text: str, phrase: str, usage_type: str = "的地得") -> Tuple[bool, str]:
        """
        验证特定用法是否正确

        Args:
            text: 完整文本
            phrase: 要验证的短语
            usage_type: 用法类型

        Returns:
            (是否正确, 建议)
        """
        if not self.is_available():
            return (True, "")

        try:
            prompt = f"""请判断以下文本中"{phrase}"的用法是否正确：

完整文本：
{text}

请返回 JSON 格式：
{{
  "correct": true/false,
  "reason": "判断理由",
  "suggestion": "如果不正确，给出修改建议"
}}
"""

            from dashscope import Generation

            response = Generation.call(
                model='qwen-turbo',
                prompt=prompt,
                max_tokens=500,
                temperature=0.3,
            )

            if response.status_code == 200:
                import json
                result_text = response.output.text
                json_start = result_text.find('{')
                json_end = result_text.rfind('}') + 1
                if json_start != -1:
                    result = json.loads(result_text[json_start:json_end])
                    return (result.get("correct", True), result.get("suggestion", ""))

        except Exception as e:
            print(f"用法验证出错: {e}")

        return (True, "")
