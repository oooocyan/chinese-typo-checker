"""
文本处理工具函数
"""
import re
from typing import List


def split_sentences(text: str) -> List[str]:
    """
    将文本分割成句子
    支持中英文标点
    """
    # 匹配句号、问号、感叹号、省略号等
    pattern = r'[^。！？…]+[。！？…]+'
    sentences = re.findall(pattern, text)

    # 处理剩余文本
    remaining = re.sub(pattern, '', text)
    if remaining.strip():
        sentences.append(remaining.strip())

    return [s for s in sentences if s.strip()]


def count_chinese_chars(text: str) -> int:
    """
    统计中文字符数
    """
    count = 0
    for char in text:
        if '一' <= char <= '鿿':
            count += 1
    return count


def is_chinese_char(char: str) -> bool:
    """
    判断是否为中文字符
    """
    return '一' <= char <= '鿿'


def is_punctuation(char: str) -> bool:
    """
    判断是否为标点符号
    """
    chinese_puncts = "。，、；：？！""''（）【】《》—…"
    english_puncts = ".,;:?!\"\"''()[]<>-"
    return char in chinese_puncts or char in english_puncts


def is_chinese_punctuation(char: str) -> bool:
    """
    判断是否为中文标点
    """
    chinese_puncts = "。，、；：？！""''（）【】《》—…"
    return char in chinese_puncts


def is_english_punctuation(char: str) -> bool:
    """
    判断是否为英文标点
    """
    english_puncts = ".,;:?!\"\"''()[]<>"
    return char in english_puncts


def get_char_position(text: str, char_index: int) -> tuple:
    """
    获取字符在文本中的行列位置
    返回 (行号, 列号)，从1开始
    """
    lines = text[:char_index].split('\n')
    line_num = len(lines)
    col_num = len(lines[-1]) + 1
    return (line_num, col_num)
