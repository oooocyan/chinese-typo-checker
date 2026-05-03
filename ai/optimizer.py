"""
AI 优化建议模块
调用通义千问 API 提供文本润色建议
"""
from typing import List, Optional
import sys
from pathlib import Path

# 添加父目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import get_api_key


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


class AIOptimizer:
    """AI 优化建议器"""

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
        """检查 AI 功能是否可用"""
        return self.client is not None

    def optimize(self, text: str, scene_type: str = "小说", style_type: str = "书面化") -> List[Issue]:
        """
        使用 AI 提供优化建议

        Args:
            text: 输入文本
            scene_type: 场景类型（剧本/小说/散文等）
            style_type: 表达风格（口语化/书面化）

        Returns:
            优化建议列表
        """
        issues = []

        if not self.is_available():
            return issues

        try:
            # 构建提示词
            prompt = self._build_prompt(text, scene_type, style_type)

            # 调用 API
            response = self._call_api(prompt)

            # 解析结果
            issues = self._parse_response(text, response)

        except Exception as e:
            print(f"AI 优化建议出错: {e}")

        return issues

    def _build_prompt(self, text: str, scene_type: str, style_type: str) -> str:
        """构建提示词"""
        prompt = f"""你是一位专业的文字编辑，擅长中文写作优化。请分析以下{scene_type}文本（{style_type}风格），指出可以改进的地方。

文本内容：
{text[:2000]}  # 限制长度避免超出token限制

请从以下角度给出具体的修改建议：
1. 用词精准度：是否有更好的词汇可以替换
2. 句子流畅度：是否有拗口或冗长的句子
3. 表达简洁性：是否有冗余可以精简
4. 文采提升：是否有更优美或更有表现力的表达方式

请以 JSON 格式返回建议，格式如下：
[
  {{"position": "问题的位置或上下文关键词", "original": "原文内容", "suggestion": "建议修改", "reason": "修改原因", "type": "建议类型"}},
  ...
]

注意：
- 只返回需要修改的内容，不需要返回 JSON 格式说明
- position 可以是原文中的关键词或短语
- 每条建议要具体可操作
- 如果文本很好，返回空数组 []
"""
        return prompt

    def _call_api(self, prompt: str) -> str:
        """调用通义千问 API"""
        from dashscope import Generation

        response = Generation.call(
            model='qwen-turbo',
            prompt=prompt,
            max_tokens=2000,
            temperature=0.7,
        )

        if response.status_code == 200:
            return response.output.text
        else:
            raise Exception(f"API 调用失败: {response.code} - {response.message}")

    def _parse_response(self, text: str, response: str) -> List[Issue]:
        """解析 API 响应"""
        issues = []

        try:
            import json

            # 尝试提取 JSON 部分
            json_start = response.find('[')
            json_end = response.rfind(']') + 1

            if json_start != -1 and json_end > json_start:
                json_str = response[json_start:json_end]
                suggestions = json.loads(json_str)

                for item in suggestions:
                    # 查找原文内容的位置
                    original = item.get("original", "")
                    pos = text.find(original)

                    if pos != -1:
                        issue = Issue(
                            position=pos,
                            position_end=pos + len(original),
                            error_text=original,
                            error_type="AI建议",
                            suggestion=item.get("suggestion", ""),
                            confidence=0.7
                        )
                        issues.append(issue)

        except json.JSONDecodeError:
            pass
        except Exception as e:
            print(f"解析 AI 响应出错: {e}")

        return issues
