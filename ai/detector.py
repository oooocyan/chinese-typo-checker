"""
AI智能检测模块
支持 NVIDIA NIM API (OpenAI兼容)
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
    """AI检测器 - 支持NVIDIA NIM API"""

    def __init__(self, api_key: str = "", base_url: str = ""):
        self.api_key = api_key
        self.base_url = base_url or "https://integrate.api.nvidia.com/v1"
        self.client = None

        if api_key:
            try:
                from openai import OpenAI
                self.client = OpenAI(
                    base_url=self.base_url,
                    api_key=api_key
                )
            except Exception as e:
                print(f"OpenAI初始化失败: {e}")

    def is_available(self) -> bool:
        return self.client is not None

    def detect(self, text: str) -> List[Issue]:
        """使用AI检测文本问题"""
        if not self.is_available():
            return []

        try:
            prompt = f"""你是一位专业的中文文字校对编辑。请仔细检查以下文本中的错误。

文本：
{text}

请检查以下类型的错误：
1. 错别字（同音字、形近字错误，如"在做"应为"再做"、"以经"应为"已经"）
2. 标点符号错误（中英文标点混用、缺失标点、多余标点）
3. 语法错误（语病、成分残缺、搭配不当、语序不当）
4. 语义问题（表达不通顺、歧义、逻辑错误）
5. 易混淆词（的地得、必须必需、反映反应等）

请以JSON数组格式返回所有发现的错误：
[
  {{
    "error": "错误的原文（必须完全匹配文本中的内容）",
    "suggestion": "修改建议",
    "type": "错别字/标点/语法/语义",
    "reason": "简要说明错误原因"
  }}
]

重要：
1. 只返回JSON数组，不要任何解释文字
2. error字段必须完全匹配原文，包括标点符号
3. 如果没有错误，返回空数组 []
4. 每个错误都要准确判断类型
"""

            response = self.client.chat.completions.create(
                model="meta/llama-3.1-405b-instruct",
                messages=[
                    {"role": "system", "content": "你是一位专业的中文文字校对编辑，擅长发现各类文字错误。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=3000,
            )

            result_text = response.choices[0].message.content

            # 提取JSON
            json_start = result_text.find('[')
            json_end = result_text.rfind(']') + 1

            if json_start == -1 or json_end == 0:
                print(f"未找到JSON: {result_text[:200]}")
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
                    # 尝试去掉首尾空格
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

            return issues

        except json.JSONDecodeError as e:
            print(f"JSON解析错误: {e}")
            return []
        except Exception as e:
            print(f"AI检测出错: {e}")
            return []

    def detect_batch(self, text: str, max_length: int = 1500) -> List[Issue]:
        """分段检测长文本"""
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
