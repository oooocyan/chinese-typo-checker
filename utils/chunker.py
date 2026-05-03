"""
长文本分段处理
"""
from typing import List, Generator


class TextChunker:
    """文本分段处理器"""

    def __init__(self, max_chunk_size: int = 2000, overlap: int = 100):
        """
        初始化

        Args:
            max_chunk_size: 每段最大字符数
            overlap: 段落之间的重叠字符数，用于保持上下文
        """
        self.max_chunk_size = max_chunk_size
        self.overlap = overlap

    def chunk(self, text: str) -> List[str]:
        """
        将文本分段

        Args:
            text: 输入文本

        Returns:
            分段后的文本列表
        """
        if len(text) <= self.max_chunk_size:
            return [text]

        chunks = []
        start = 0

        while start < len(text):
            # 确定当前段的结束位置
            end = start + self.max_chunk_size

            if end >= len(text):
                chunks.append(text[start:])
                break

            # 尝试在句号、问号、感叹号处断开
            best_break = self._find_best_break(text, start, end)

            if best_break > start:
                chunks.append(text[start:best_break])
                start = best_break - self.overlap  # 保留重叠部分
                if start < 0:
                    start = 0
            else:
                chunks.append(text[start:end])
                start = end - self.overlap
                if start < 0:
                    start = 0

        return chunks

    def _find_best_break(self, text: str, start: int, end: int) -> int:
        """
        寻找最佳断点位置
        优先在句子结束处断开
        """
        # 在范围内寻找句号、问号、感叹号
        for i in range(end - 1, start, -1):
            if text[i] in '。！？…':
                return i + 1

        # 如果没有找到句子结束符，寻找其他标点
        for i in range(end - 1, start, -1):
            if text[i] in '，、；：）】》"\'':
                return i + 1

        # 如果都没有，在空格或换行处断开
        for i in range(end - 1, start, -1):
            if text[i] in ' \n\t':
                return i + 1

        # 最后直接在 end 处断开
        return end

    def chunk_with_context(self, text: str) -> Generator[tuple, None, None]:
        """
        分段并返回上下文信息

        Yields:
            (chunk_text, start_pos, end_pos, chunk_index, total_chunks)
        """
        chunks = self.chunk(text)
        current_pos = 0

        for idx, chunk in enumerate(chunks):
            # 计算当前段在原文中的位置
            # 考虑重叠部分，需要找到实际匹配的位置
            if idx == 0:
                start_pos = 0
            else:
                # 从上一段结束位置减去重叠部分开始
                start_pos = max(0, current_pos - self.overlap)

            end_pos = start_pos + len(chunk)

            yield (chunk, start_pos, end_pos, idx, len(chunks))

            current_pos = end_pos
