"""
AI智能检测模块
调用大模型进行深度检测
"""
from typing import List
import json


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


class AIDetector:
    """AI检测器"""

    def __init__(self, api_key: str = ""):
        self.api_key = api_key
        self.client = None
        if api_key:
            try:
                import dashscope
                dashscope.api_key = api_key
                self.client = dashscope
            except:
                pass

    def is_available(self) -> bool:
        return self.client is not None

    def detect(self, text: str) -> List[Issue]:
        """
        使用AI检测文本问题

        Args:
            text: 输入文本

        Returns:
            问题列表
        """
        if not self.is_available():
            return []

        try:
            from dashscope import Generation

            prompt = f"""你是一位专业的中文文字校对编辑。请仔细检查以下文本中的错误。

文本：
{text}

请检查以下类型的错误：
1. 错别字（同音字、形近字错误）
2. 标点符号错误（中英文标点混用、缺失标点）
3. 语法错误（语病、成分残缺、搭配不当）
4. 语义问题（表达不通顺、歧义）
5. 常见易混淆词（的地得、必须必需等）

请以JSON数组格式返回所有发现的错误，格式如下：
[
  {{
    "error": "错误的原文",
    "suggestion": "修改建议",
    "type": "错误类型（错别字/标点/语法/语义）",
    "reason": "错误原因"
  }}
]

注意：
1. 只返回JSON数组，不要其他解释
2. 如果没有错误，返回空数组 []
3. 确保错误原文在文本中能找到完全匹配
4. 每个错误要准确标注类型
"""

            response = Generation.call(
                model='qwen-turbo',
                prompt=prompt,
                max_tokens=3000,
                temperature=0.3,
            )

            if response.status_code != 200:
                print(f"AI检测失败: {response.message}")
                return []

            result_text = response.output.text

            # 提取JSON
            json_start = result_text.find('[')
            json_end = result_text.rfind(']') + 1

            if json_start == -1 or json_end == 0:
                return []

            json_str = result_text[json_start:json_end]
            errors = json.loads(json_str)

            # 转换为Issue对象
            issues = []
            for err in errors:
                error_text = err.get("error", "")
                if not error_text:
                    continue

                # 在原文中查找位置
                pos = text.find(error_text)
                if pos == -1:
                    # 尝试模糊匹配
                    continue

                issue = Issue(
                    position=pos,
                    position_end=pos + len(error_text),
                    error_text=error_text,
                    error_type=err.get("type", "错别字"),
                    suggestion=err.get("suggestion", ""),
                    confidence=0.85
                )
                issues.append(issue)

            return issues

        except Exception as e:
            print(f"AI检测出错: {e}")
            return []

    def detect_batch(self, text: str, max_length: int = 2000) -> List[Issue]:
        """
        分段检测长文本

        Args:
            text: 输入文本
            max_length: 每段最大长度

        Returns:
            问题列表
        """
        if len(text) <= max_length:
            return self.detect(text)

        # 分段检测
        all_issues = []
        paragraphs = text.split('\n')
        current_pos = 0

        for para in paragraphs:
            if not para.strip():
                current_pos += 1
                continue

            issues = self.detect(para)

            # 调整位置偏移
            for issue in issues:
                issue.position += current_pos
                issue.position_end += current_pos

            all_issues.extend(issues)
            current_pos += len(para) + 1

        return all_issues
