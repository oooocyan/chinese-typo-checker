"""
AI智能检测模块
支持 DeepSeek API (OpenAI兼容)
"""
from typing import List, Tuple
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
    """AI检测器 - 支持DeepSeek API"""

    def __init__(self, api_key: str = "", base_url: str = ""):
        self.api_key = api_key
        self.base_url = base_url or "https://api.deepseek.com/v1"
        self.client = None
        self.error_msg = ""

        if api_key:
            try:
                from openai import OpenAI
                self.client = OpenAI(
                    base_url=self.base_url,
                    api_key=api_key
                )
            except ImportError:
                self.error_msg = "未安装openai库，请添加到requirements.txt"
            except Exception as e:
                self.error_msg = f"OpenAI初始化失败: {e}"

    def is_available(self) -> bool:
        return self.client is not None

    def get_error(self) -> str:
        return self.error_msg

    def detect(self, text: str) -> Tuple[List[Issue], str]:
        """使用AI检测文本问题，返回(问题列表, 错误信息)"""
        if not self.is_available():
            return [], self.error_msg or "AI未初始化"

        try:
            prompt = f"""请检查以下中文文本中的错误，包括：错别字、标点错误、语法错误、语义问题。

文本：
{text}

请直接返回JSON数组格式，不要其他内容：
[
  {{
    "error": "错误原文",
    "suggestion": "修改建议",
    "type": "错别字或标点或语法或语义"
  }}
]

如果没有错误返回 []
"""

            response = self.client.chat.completions.create(
                model="deepseek-chat",
                messages=[
                    {"role": "system", "content": "你是中文校对助手，只返回JSON数组。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2,
                max_tokens=2000,
            )

            result_text = response.choices[0].message.content.strip()

            # 提取JSON
            json_start = result_text.find('[')
            json_end = result_text.rfind(']') + 1

            if json_start == -1:
                return [], f"AI返回格式错误: {result_text[:100]}"

            json_str = result_text[json_start:json_end]
            errors = json.loads(json_str)

            # 转换为Issue对象
            issues = []
            for err in errors:
                error_text = err.get("error", "")
                if not error_text:
                    continue

                pos = text.find(error_text)
                if pos == -1:
                    error_text = error_text.strip()
                    pos = text.find(error_text)
                    if pos == -1:
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

            return issues, ""

        except json.JSONDecodeError as e:
            return [], f"JSON解析错误: {e}"
        except Exception as e:
            return [], f"AI检测出错: {str(e)}"

    def detect_batch(self, text: str, max_length: int = 1500) -> Tuple[List[Issue], str]:
        """分段检测长文本"""
        if len(text) <= max_length:
            return self.detect(text)

        all_issues = []
        paragraphs = text.split('\n')
        current_pos = 0

        for para in paragraphs:
            if not para.strip():
                current_pos += 1
                continue

            issues, error = self.detect(para)
            if error:
                return [], error

            for issue in issues:
                issue.position += current_pos
                issue.position_end += current_pos

            all_issues.extend(issues)
            current_pos += len(para) + 1

        return all_issues, ""
