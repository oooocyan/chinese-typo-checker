"""
配置文件
"""
import os

# API Key 配置
# 优先从环境变量读取，如果没有则使用 Streamlit secrets
def get_api_key():
    """获取 API Key"""
    # 尝试从环境变量获取
    api_key = os.environ.get("DASHSCOPE_API_KEY", "")

    # 如果环境变量没有，尝试从 Streamlit secrets 获取
    if not api_key:
        try:
            import streamlit as st
            api_key = st.secrets.get("DASHSCOPE_API_KEY", "")
        except:
            pass

    return api_key

# 检测配置
MAX_TEXT_LENGTH = 10000  # 最大文本长度（字）
CONFIDENCE_THRESHOLD = 0.5  # 置信度阈值

# 问题类型颜色配置（用于界面显示）
ISSUE_COLORS = {
    "错别字": "#FF4B4B",      # 红色
    "标点": "#FFA500",        # 橙色
    "语法": "#4B8BFF",        # 蓝色
    "语义": "#9B59B6",        # 紫色
    "AI建议": "#2ECC71",      # 绿色
}

# 场景类型
SCENE_TYPES = {
    "script": "剧本",
    "novel": "小说",
    "oral": "口语",
    "written": "书面",
}

# 表达风格
STYLE_TYPES = {
    "oral": "口语化",
    "written": "书面化",
}
