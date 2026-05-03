"""
智能文字校对工具 - Streamlit 主入口
参考爱校对风格设计，优化交互体验
"""
import streamlit as st
from dataclasses import dataclass
from typing import List, Optional
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from checker.typo import TypoChecker
from checker.punctuation import PunctuationChecker
from checker.grammar import GrammarChecker
from checker.context import ContextChecker
from scene.detector import SceneDetector

# 配置页面
st.set_page_config(
    page_title="智能文字校对",
    page_icon="📝",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# 自定义CSS
st.markdown("""
<style>
    /* 隐藏Streamlit默认元素 */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}

    /* 主容器 */
    .main .block-container {
        padding-top: 1rem;
        max-width: 100%;
    }

    /* 标题样式 */
    .main-title {
        font-size: 1.8rem;
        font-weight: 600;
        color: #1a73e8;
        text-align: center;
        padding: 0.5rem 0;
        border-bottom: 2px solid #e8f0fe;
        margin-bottom: 1rem;
    }

    /* 输入区域 */
    .input-area {
        background-color: #fafafa;
        border: 2px dashed #ddd;
        border-radius: 8px;
        padding: 1rem;
        min-height: 400px;
    }

    /* 结果卡片 */
    .error-card {
        background: white;
        border: 1px solid #e0e0e0;
        border-radius: 8px;
        padding: 12px 16px;
        margin-bottom: 8px;
        transition: all 0.2s;
        cursor: pointer;
    }
    .error-card:hover {
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        border-color: #1a73e8;
    }
    .error-card.selected {
        border-color: #1a73e8;
        background: #f0f7ff;
    }

    /* 错误类型标签 */
    .error-tag {
        display: inline-block;
        padding: 2px 10px;
        border-radius: 12px;
        font-size: 0.8rem;
        font-weight: 500;
        margin-right: 8px;
    }

    /* 按钮 */
    .stButton button {
        border-radius: 6px;
        font-weight: 500;
    }
    .stButton button[kind="primary"] {
        background: #1a73e8;
    }

    /* 统计栏 */
    .stats-bar {
        display: flex;
        gap: 20px;
        padding: 10px 0;
        border-bottom: 1px solid #eee;
        margin-bottom: 10px;
    }
    .stat-item {
        text-align: center;
    }
    .stat-number {
        font-size: 1.5rem;
        font-weight: 600;
        color: #1a73e8;
    }
    .stat-label {
        font-size: 0.8rem;
        color: #666;
    }

    /* 高亮文本 */
    .highlight-error {
        background: #ffebee;
        color: #c62828;
        padding: 1px 4px;
        border-radius: 3px;
        border-bottom: 2px solid #c62828;
        cursor: pointer;
    }
    .highlight-selected {
        background: #c62828;
        color: white;
        padding: 1px 4px;
        border-radius: 3px;
    }

    /* AI结果区 */
    .ai-result-box {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border-radius: 8px;
        padding: 1.5rem;
        line-height: 1.8;
    }
</style>
""", unsafe_allow_html=True)


@dataclass
class Issue:
    """问题数据类"""
    position: int
    position_end: int
    error_text: str
    error_type: str
    suggestion: str
    confidence: float
    applied: bool = False
    ignored: bool = False


def get_issue_color(error_type: str) -> str:
    """获取问题类型对应的颜色"""
    colors = {
        "错别字": "#e74c3c",
        "标点": "#f39c12",
        "语法": "#3498db",
        "语义": "#9b59b6",
        "敏感词": "#c0392b",
    }
    return colors.get(error_type, "#7f8c8d")


def get_issue_bgcolor(error_type: str) -> str:
    """获取问题类型背景色"""
    colors = {
        "错别字": "#ffebee",
        "标点": "#fff3e0",
        "语法": "#e3f2fd",
        "语义": "#f3e5f5",
        "敏感词": "#ffebee",
    }
    return colors.get(error_type, "#f5f5f5")


def highlight_text(text: str, issues: List[Issue], selected_idx: Optional[int] = None) -> str:
    """高亮显示文本中的错误"""
    if not issues:
        return text

    sorted_issues = sorted([i for i in issues if not i.ignored], key=lambda x: x.position)
    result = []
    last_end = 0

    for idx, issue in enumerate(sorted_issues):
        if issue.position > last_end:
            result.append(text[last_end:issue.position])

        error_part = text[issue.position:issue.position_end]
        is_selected = (selected_idx is not None and idx == selected_idx)

        if is_selected:
            result.append(f'<span class="highlight-selected">{error_part}</span>')
        else:
            result.append(f'<span class="highlight-error">{error_part}</span>')

        last_end = issue.position_end

    if last_end < len(text):
        result.append(text[last_end:])

    return "".join(result)


def count_chinese_chars(text: str) -> int:
    """统计中文字符数"""
    return sum(1 for char in text if '一' <= char <= '鿿')


def run_check(text: str) -> tuple:
    """运行检测"""
    issues = []

    detector = SceneDetector()
    scene_type, style_type = detector.detect(text)

    # 错别字
    for issue in TypoChecker().check(text):
        issues.append(Issue(issue.position, issue.position_end, issue.error_text, "错别字", issue.suggestion, issue.confidence))

    # 标点
    for issue in PunctuationChecker().check(text):
        issues.append(Issue(issue.position, issue.position_end, issue.error_text, "标点", issue.suggestion, issue.confidence))

    # 语法
    for issue in GrammarChecker().check(text):
        issues.append(Issue(issue.position, issue.position_end, issue.error_text, "语法", issue.suggestion, issue.confidence))

    # 语义
    for issue in ContextChecker().check(text):
        issues.append(Issue(issue.position, issue.position_end, issue.error_text, "语义", issue.suggestion, issue.confidence))

    issues.sort(key=lambda x: x.position)
    return issues, scene_type, style_type


def run_ai_optimize(text: str) -> str:
    """AI优化"""
    try:
        import dashscope
        from dashscope import Generation

        api_key = st.secrets.get("DASHSCOPE_API_KEY", "")
        if not api_key:
            return "⚠️ 请在Settings中配置DASHSCOPE_API_KEY"

        dashscope.api_key = api_key

        prompt = f"""请对以下文本进行润色优化，提升表达质量。直接输出优化后的文本，不要解释：

{text[:2000]}"""

        response = Generation.call(model='qwen-turbo', prompt=prompt, max_tokens=3000)
        return response.output.text if response.status_code == 200 else f"优化失败: {response.message}"

    except Exception as e:
        return f"优化出错: {str(e)}"


def main():
    # 标题
    st.markdown('<div class="main-title">📝 智能文字校对</div>', unsafe_allow_html=True)

    # 初始化状态
    if "text" not in st.session_state:
        st.session_state.text = ""
    if "issues" not in st.session_state:
        st.session_state.issues = []
    if "scene_type" not in st.session_state:
        st.session_state.scene_type = "未识别"
    if "style_type" not in st.session_state:
        st.session_state.style_type = "未识别"
    if "selected_idx" not in st.session_state:
        st.session_state.selected_idx = None
    if "checking" not in st.session_state:
        st.session_state.checking = False
    if "ai_result" not in st.session_state:
        st.session_state.ai_result = ""
    if "tab" not in st.session_state:
        st.session_state.tab = "校对"

    # 功能标签
    tab1, tab2, tab3 = st.tabs(["🔍 文字校对", "✨ AI润色", "📊 使用说明"])

    # ========== 文字校对 ==========
    with tab1:
        # 工具栏
        col1, col2, col3, col4 = st.columns([1, 1, 1, 2])

        with col1:
            char_count = count_chinese_chars(st.session_state.text)
            st.metric("字数", f"{char_count}/10000")

        with col2:
            if st.button("🔍 开始校对", type="primary", use_container_width=True):
                if st.session_state.text.strip() and char_count <= 10000:
                    st.session_state.checking = True
                    st.session_state.issues = []
                    st.session_state.selected_idx = None
                    st.rerun()
                elif not st.session_state.text.strip():
                    st.warning("请输入文本")
                else:
                    st.error("超过10000字")

        with col3:
            if st.button("🗑️ 清空", use_container_width=True):
                st.session_state.text = ""
                st.session_state.issues = []
                st.session_state.ai_result = ""
                st.rerun()

        with col4:
            if st.session_state.issues and not st.session_state.checking:
                active = len([i for i in st.session_state.issues if not i.ignored])
                applied = sum(1 for i in st.session_state.issues if i.applied)
                st.info(f"✓ 检测完成：发现 {len(st.session_state.issues)} 个问题，已修正 {applied} 个")

        # 执行检测
        if st.session_state.checking:
            with st.spinner("正在校对..."):
                issues, scene_type, style_type = run_check(st.session_state.text)
                st.session_state.issues = issues
                st.session_state.scene_type = scene_type
                st.session_state.style_type = style_type
                st.session_state.checking = False
            st.rerun()

        # 主内容区
        col_left, col_right = st.columns([3, 2])

        with col_left:
            st.markdown("**📄 输入文本**")

            # 文本输入
            text_input = st.text_area(
                "输入文本",
                value=st.session_state.text,
                height=350,
                label_visibility="collapsed",
                placeholder="在此粘贴或输入需要校对的文本..."
            )

            if text_input != st.session_state.text:
                st.session_state.text = text_input
                st.session_state.issues = []
                st.session_state.ai_result = ""

            # 高亮显示
            if st.session_state.issues:
                st.markdown("**预览（点击错误可定位）：**")
                highlighted = highlight_text(st.session_state.text, st.session_state.issues, st.session_state.selected_idx)
                st.markdown(f'<div style="background:#fafafa; padding:12px; border-radius:8px; line-height:2; max-height:200px; overflow:auto;">{highlighted}</div>', unsafe_allow_html=True)

                # 一键修正
                col_a, col_b = st.columns(2)
                with col_a:
                    if st.button("✓ 一键修正全部", use_container_width=True):
                        new_text = st.session_state.text
                        for issue in sorted(st.session_state.issues, key=lambda x: -x.position):
                            if not issue.ignored:
                                new_text = new_text[:issue.position] + issue.suggestion + new_text[issue.position_end:]
                                issue.applied = True
                        st.session_state.text = new_text
                        st.rerun()
                with col_b:
                    if st.button("📥 导出报告", use_container_width=True):
                        report = f"# 校对报告\n\n## 概况\n- 类型：{st.session_state.scene_type}\n- 问题：{len(st.session_state.issues)}个\n\n## 问题列表\n"
                        for i, issue in enumerate(st.session_state.issues, 1):
                            if not issue.ignored:
                                report += f"{i}. [{issue.error_type}] {issue.error_text} → {issue.suggestion}\n"
                        report += f"\n## 原文\n\n{st.session_state.text}"
                        st.download_button("下载", report, "校对报告.md", "text/markdown")

        with col_right:
            st.markdown("**📋 检测结果**")

            if st.session_state.issues:
                # 统计
                type_counts = {}
                for issue in st.session_state.issues:
                    if not issue.ignored:
                        type_counts[issue.error_type] = type_counts.get(issue.error_type, 0) + 1

                stats_html = " ".join([f'<span class="error-tag" style="background:{get_issue_bgcolor(t)};color:{get_issue_color(t)}">{t}:{c}</span>' for t, c in type_counts.items()])
                st.markdown(f'<div style="margin-bottom:12px;">{stats_html}</div>', unsafe_allow_html=True)

                # 问题列表
                for idx, issue in enumerate(st.session_state.issues):
                    if issue.ignored:
                        continue

                    color = get_issue_color(issue.error_type)
                    is_selected = st.session_state.selected_idx == idx

                    # 问题卡片
                    card_class = "error-card selected" if is_selected else "error-card"
                    st.markdown(f"""
                    <div class="{card_class}">
                        <div style="display:flex; align-items:center; margin-bottom:6px;">
                            <span class="error-tag" style="background:{get_issue_bgcolor(issue.error_type)};color:{color}">{issue.error_type}</span>
                            <span style="color:#666; font-size:0.85rem;">第{issue.position}字</span>
                        </div>
                        <div style="font-size:1rem;">
                            <span style="color:{color}; text-decoration:line-through;">{issue.error_text}</span>
                            <span style="margin:0 8px; color:#999;">→</span>
                            <span style="color:#27ae60; font-weight:600;">{issue.suggestion}</span>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

                    col_a, col_b, col_c = st.columns([1, 1, 1])
                    with col_a:
                        if st.button("✓ 应用", key=f"apply_{idx}", use_container_width=True):
                            new_text = st.session_state.text[:issue.position] + issue.suggestion + st.session_state.text[issue.position_end:]
                            st.session_state.text = new_text
                            issue.applied = True
                            st.rerun()
                    with col_b:
                        if st.button("✕ 忽略", key=f"ignore_{idx}", use_container_width=True):
                            issue.ignored = True
                            st.rerun()
                    with col_c:
                        if st.button("📍 定位", key=f"loc_{idx}", use_container_width=True):
                            st.session_state.selected_idx = None if is_selected else idx
                            st.rerun()

            else:
                st.info("👈 输入文本后点击「开始校对」")

    # ========== AI润色 ==========
    with tab2:
        st.markdown("""
        <div style="background:linear-gradient(135deg, #667eea 0%, #764ba2 100%); color:white; padding:20px; border-radius:10px; margin-bottom:20px;">
            <h3 style="margin:0 0 10px 0;">✨ AI智能润色</h3>
            <p style="margin:0; opacity:0.9;">基于大语言模型，智能优化文字表达，提升文采和可读性</p>
        </div>
        """, unsafe_allow_html=True)

        if st.session_state.text:
            st.markdown("**原文：**")
            st.text_area("", st.session_state.text[:800] + ("..." if len(st.session_state.text) > 800 else ""), height=150, disabled=True, key="orig")

            if st.button("🚀 开始AI润色", type="primary"):
                with st.spinner("AI正在优化中..."):
                    result = run_ai_optimize(st.session_state.text)
                    st.session_state.ai_result = result

            if st.session_state.ai_result:
                st.markdown("**✨ 润色结果：**")
                st.markdown(f'<div class="ai-result-box">{st.session_state.ai_result}</div>', unsafe_allow_html=True)

                if st.button("📋 使用润色结果替换原文"):
                    st.session_state.text = st.session_state.ai_result
                    st.session_state.ai_result = ""
                    st.session_state.issues = []
                    st.success("已替换！")
        else:
            st.info("请先在「文字校对」中输入文本")

    # ========== 使用说明 ==========
    with tab3:
        st.markdown("""
        ### 📖 使用说明

        **1. 文字校对功能**
        - 粘贴或输入需要校对的文本
        - 点击「开始校对」按钮
        - 查看检测结果，点击「应用」修正错误
        - 支持一键修正全部错误

        **2. AI润色功能**
        - 输入文本后切换到「AI润色」标签
        - 点击「开始AI润色」
        - 查看优化结果，可选择替换原文

        **3. 支持的检测类型**
        - 🔴 错别字检测
        - 🟠 标点符号检查
        - 🔵 语法问题检测
        - 🟣 语义问题检测

        ---

        ### ⚙️ 配置AI功能

        如需使用AI润色功能，请在Streamlit Cloud的 Settings → Secrets 中添加：

        ```
        DASHSCOPE_API_KEY = "你的通义千问API密钥"
        ```

        获取API密钥：[dashscope.console.aliyun.com](https://dashscope.console.aliyun.com/)
        """)


if __name__ == "__main__":
    main()
