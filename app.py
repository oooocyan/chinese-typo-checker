"""
智能文字校对工具 - 优化交互体验
支持：悬浮修改建议、双向联动定位、一键溯源
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

st.set_page_config(
    page_title="智能文字校对",
    page_icon="📝",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# 自定义CSS和JavaScript
st.markdown("""
<style>
    #MainMenu, footer, header {visibility: hidden;}
    .main .block-container {padding-top: 1rem; max-width: 100%;}

    .main-title {
        font-size: 1.8rem;
        font-weight: 600;
        color: #1a73e8;
        text-align: center;
        padding: 0.5rem 0;
        border-bottom: 2px solid #e8f0fe;
        margin-bottom: 1rem;
    }

    /* 原文显示区 */
    .text-display {
        background: #fafafa;
        border: 1px solid #e0e0e0;
        border-radius: 8px;
        padding: 16px;
        line-height: 2;
        font-size: 1rem;
        min-height: 300px;
        max-height: 500px;
        overflow-y: auto;
    }

    /* 错误高亮 */
    .error-span {
        background: #ffebee;
        color: #c62828;
        padding: 2px 4px;
        border-radius: 3px;
        border-bottom: 2px solid #c62828;
        cursor: pointer;
        position: relative;
        transition: all 0.2s;
    }
    .error-span:hover {
        background: #ffcdd2;
    }
    .error-span.selected {
        background: #c62828;
        color: white;
        box-shadow: 0 2px 8px rgba(198, 40, 40, 0.4);
    }

    /* 悬浮提示框 */
    .tooltip {
        position: absolute;
        bottom: 100%;
        left: 50%;
        transform: translateX(-50%);
        background: white;
        border: 1px solid #ddd;
        border-radius: 8px;
        padding: 10px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        z-index: 1000;
        min-width: 180px;
        display: none;
    }
    .error-span:hover .tooltip {
        display: block;
    }

    /* 结果卡片 */
    .result-card {
        background: white;
        border: 1px solid #e0e0e0;
        border-radius: 8px;
        padding: 12px;
        margin-bottom: 8px;
        transition: all 0.2s;
        border-left: 4px solid transparent;
    }
    .result-card:hover {
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    }
    .result-card.active {
        border-left-color: #1a73e8;
        background: #f0f7ff;
        box-shadow: 0 2px 8px rgba(26, 115, 232, 0.2);
    }

    /* 错误类型标签 */
    .type-tag {
        display: inline-block;
        padding: 2px 8px;
        border-radius: 12px;
        font-size: 0.75rem;
        font-weight: 500;
        margin-right: 6px;
    }

    /* 按钮 */
    .action-btn {
        padding: 4px 12px;
        border-radius: 4px;
        border: none;
        cursor: pointer;
        font-size: 0.85rem;
        margin-right: 4px;
        transition: all 0.2s;
    }
    .apply-btn {
        background: #27ae60;
        color: white;
    }
    .apply-btn:hover {
        background: #219a52;
    }
    .ignore-btn {
        background: #95a5a6;
        color: white;
    }
    .ignore-btn:hover {
        background: #7f8c8d;
    }

    /* AI结果 */
    .ai-box {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border-radius: 8px;
        padding: 20px;
        line-height: 1.8;
    }

    /* 统计栏 */
    .stats-row {
        display: flex;
        gap: 16px;
        padding: 8px 0;
        margin-bottom: 12px;
    }
    .stat-item {
        background: #f5f5f5;
        padding: 6px 12px;
        border-radius: 6px;
        font-size: 0.9rem;
    }
    .stat-num {
        font-weight: 600;
        color: #1a73e8;
    }
</style>

<script>
// 滚动到指定错误位置
function scrollToError(errorId) {
    const element = document.getElementById('error-' + errorId);
    if (element) {
        element.scrollIntoView({ behavior: 'smooth', block: 'center' });
        element.classList.add('selected');
        setTimeout(() => element.classList.remove('selected'), 2000);
    }
}

// 滚动到结果卡片
function scrollToResult(errorId) {
    const element = document.getElementById('result-' + errorId);
    if (element) {
        element.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }
}
</script>
""", unsafe_allow_html=True)


@dataclass
class Issue:
    position: int
    position_end: int
    error_text: str
    error_type: str
    suggestion: str
    confidence: float
    id: int = 0
    applied: bool = False
    ignored: bool = False


def get_issue_color(error_type: str) -> str:
    colors = {"错别字": "#e74c3c", "标点": "#f39c12", "语法": "#3498db", "语义": "#9b59b6"}
    return colors.get(error_type, "#7f8c8d")


def get_issue_bgcolor(error_type: str) -> str:
    colors = {"错别字": "#ffebee", "标点": "#fff3e0", "语法": "#e3f2fd", "语义": "#f3e5f5"}
    return colors.get(error_type, "#f5f5f5")


def render_text_with_tooltips(text: str, issues: List[Issue], selected_id: Optional[int] = None) -> str:
    """渲染带悬浮提示的文本"""
    if not issues:
        return text.replace('\n', '<br>')

    sorted_issues = sorted([i for i in issues if not i.ignored], key=lambda x: x.position)
    result = []
    last_end = 0

    for issue in sorted_issues:
        if issue.position > last_end:
            result.append(text[last_end:issue.position].replace('\n', '<br>'))

        error_part = text[issue.position:issue.position_end].replace('\n', '<br>')
        color = get_issue_color(issue.error_type)
        is_selected = selected_id == issue.id

        selected_class = " selected" if is_selected else ""

        # 悬浮提示HTML
        tooltip_html = f'''
        <div class="tooltip">
            <div style="font-weight:600; margin-bottom:6px; color:{color};">
                {issue.error_type}
            </div>
            <div style="margin-bottom:8px;">
                <span style="text-decoration:line-through; color:#999;">{issue.error_text}</span>
                →
                <span style="color:#27ae60; font-weight:600;">{issue.suggestion}</span>
            </div>
            <div style="font-size:0.8rem; color:#666;">
                置信度: {issue.confidence:.0%}
            </div>
        </div>
        '''

        result.append(f'''
        <span id="error-{issue.id}" class="error-span{selected_class}" style="border-bottom-color:{color};" onclick="scrollToResult({issue.id})">
            {error_part}
            {tooltip_html}
        </span>
        ''')

        last_end = issue.position_end

    if last_end < len(text):
        result.append(text[last_end:].replace('\n', '<br>'))

    return "".join(result)


def count_chinese_chars(text: str) -> int:
    return sum(1 for c in text if '一' <= c <= '鿿')


def run_check(text: str) -> tuple:
    issues = []
    detector = SceneDetector()
    scene_type, style_type = detector.detect(text)

    for issue in TypoChecker().check(text):
        issues.append(Issue(issue.position, issue.position_end, issue.error_text, "错别字", issue.suggestion, issue.confidence))
    for issue in PunctuationChecker().check(text):
        issues.append(Issue(issue.position, issue.position_end, issue.error_text, "标点", issue.suggestion, issue.confidence))
    for issue in GrammarChecker().check(text):
        issues.append(Issue(issue.position, issue.position_end, issue.error_text, "语法", issue.suggestion, issue.confidence))
    for issue in ContextChecker().check(text):
        issues.append(Issue(issue.position, issue.position_end, issue.error_text, "语义", issue.suggestion, issue.confidence))

    issues.sort(key=lambda x: x.position)
    for i, issue in enumerate(issues):
        issue.id = i

    return issues, scene_type, style_type


def run_ai_optimize(text: str) -> str:
    try:
        import dashscope
        from dashscope import Generation
        api_key = st.secrets.get("DASHSCOPE_API_KEY", "")
        if not api_key:
            return "⚠️ 请配置 DASHSCOPE_API_KEY"
        dashscope.api_key = api_key
        response = Generation.call(model='qwen-turbo', prompt=f"润色优化以下文本，直接输出结果：\n{text[:2000]}", max_tokens=3000)
        return response.output.text if response.status_code == 200 else f"失败: {response.message}"
    except Exception as e:
        return f"出错: {e}"


def main():
    st.markdown('<div class="main-title">📝 智能文字校对</div>', unsafe_allow_html=True)

    # 初始化状态
    for key in ["text", "issues", "scene_type", "style_type", "selected_id", "checking", "ai_result"]:
        if key not in st.session_state:
            st.session_state[key] = "" if key in ["text", "ai_result", "scene_type", "style_type"] else ([] if key == "issues" else None if key == "selected_id" else False)

    # 标签页
    tab1, tab2, tab3 = st.tabs(["🔍 文字校对", "✨ AI润色", "📖 使用说明"])

    # ===== 文字校对 =====
    with tab1:
        # 工具栏
        col1, col2, col3, col4, col5 = st.columns([1, 1, 1, 1, 1])

        with col1:
            st.metric("字数", f"{count_chinese_chars(st.session_state.text)}/10000")

        with col2:
            if st.button("🔍 开始校对", type="primary", use_container_width=True):
                if st.session_state.text.strip() and count_chinese_chars(st.session_state.text) <= 10000:
                    st.session_state.checking = True
                    st.session_state.issues = []
                    st.session_state.selected_id = None
                    st.rerun()

        with col3:
            if st.button("✓ 一键修正全部", use_container_width=True):
                if st.session_state.issues:
                    new_text = st.session_state.text
                    for issue in sorted(st.session_state.issues, key=lambda x: -x.position):
                        if not issue.ignored:
                            new_text = new_text[:issue.position] + issue.suggestion + new_text[issue.position_end:]
                            issue.applied = True
                    st.session_state.text = new_text
                    st.session_state.issues = []
                    st.rerun()

        with col4:
            if st.button("🗑️ 清空", use_container_width=True):
                st.session_state.text = ""
                st.session_state.issues = []
                st.session_state.ai_result = ""
                st.rerun()

        with col5:
            if st.session_state.issues:
                remaining = len([i for i in st.session_state.issues if not i.ignored])
                st.metric("剩余问题", remaining)

        # 执行检测
        if st.session_state.checking:
            with st.spinner("校对中..."):
                issues, scene_type, style_type = run_check(st.session_state.text)
                st.session_state.issues = issues
                st.session_state.scene_type = scene_type
                st.session_state.style_type = style_type
                st.session_state.checking = False
            st.rerun()

        # 主内容区
        col_left, col_right = st.columns([3, 2])

        with col_left:
            st.markdown("**📄 输入文本**（可编辑）")

            # 文本输入
            text_input = st.text_area(
                "输入文本",
                value=st.session_state.text,
                height=200,
                label_visibility="collapsed",
                placeholder="粘贴或输入文本...",
                key="text_input_area"
            )

            if text_input != st.session_state.text:
                st.session_state.text = text_input
                st.session_state.issues = []
                st.session_state.selected_id = None

            # 高亮预览区（悬浮提示）
            if st.session_state.issues:
                st.markdown("---")
                st.markdown("**📌 错误预览**（鼠标悬停查看建议，点击定位）")

                highlighted = render_text_with_tooltips(
                    st.session_state.text,
                    st.session_state.issues,
                    st.session_state.selected_id
                )
                st.markdown(f'<div class="text-display">{highlighted}</div>', unsafe_allow_html=True)

                # 导出按钮
                if st.button("📥 导出报告"):
                    report = f"# 校对报告\n\n类型: {st.session_state.scene_type}\n问题: {len(st.session_state.issues)}个\n\n"
                    for i, issue in enumerate(st.session_state.issues, 1):
                        if not issue.ignored:
                            report += f"{i}. [{issue.error_type}] {issue.error_text} → {issue.suggestion}\n"
                    report += f"\n## 原文\n\n{st.session_state.text}"
                    st.download_button("下载报告", report, "校对报告.md", "text/markdown")

        with col_right:
            st.markdown("**📋 检测结果**（点击定位）")

            if st.session_state.issues:
                # 统计
                type_counts = {}
                for issue in st.session_state.issues:
                    if not issue.ignored:
                        type_counts[issue.error_type] = type_counts.get(issue.error_type, 0) + 1

                stats = " ".join([f'<span class="stat-item"><span class="stat-num">{c}</span> {t}</span>' for t, c in type_counts.items()])
                st.markdown(f'<div class="stats-row">{stats}</div>', unsafe_allow_html=True)

                # 结果列表
                for issue in st.session_state.issues:
                    if issue.ignored:
                        continue

                    color = get_issue_color(issue.error_type)
                    is_active = st.session_state.selected_id == issue.id
                    card_class = "result-card active" if is_active else "result-card"

                    st.markdown(f"""
                    <div id="result-{issue.id}" class="{card_class}" style="border-left-color:{color};">
                        <div style="display:flex; align-items:center; margin-bottom:6px;">
                            <span class="type-tag" style="background:{get_issue_bgcolor(issue.error_type)};color:{color};">{issue.error_type}</span>
                            <span style="color:#999; font-size:0.8rem;">第{issue.position}字</span>
                            <span style="margin-left:auto; font-size:0.75rem; color:#999;">置信度 {issue.confidence:.0%}</span>
                        </div>
                        <div style="font-size:1rem; margin-bottom:8px;">
                            <span style="color:{color}; text-decoration:line-through;">{issue.error_text}</span>
                            <span style="margin:0 6px; color:#ccc;">→</span>
                            <span style="color:#27ae60; font-weight:600;">{issue.suggestion}</span>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

                    col_a, col_b, col_c = st.columns([1, 1, 1])
                    with col_a:
                        if st.button("✓ 应用", key=f"apply_{issue.id}", use_container_width=True):
                            new_text = st.session_state.text[:issue.position] + issue.suggestion + st.session_state.text[issue.position_end:]
                            st.session_state.text = new_text
                            issue.applied = True
                            st.session_state.issues = [i for i in st.session_state.issues if i.id != issue.id]
                            st.rerun()
                    with col_b:
                        if st.button("✕ 忽略", key=f"ignore_{issue.id}", use_container_width=True):
                            issue.ignored = True
                            st.rerun()
                    with col_c:
                        if st.button("📍 定位", key=f"loc_{issue.id}", use_container_width=True):
                            st.session_state.selected_id = None if is_active else issue.id
                            st.rerun()

            else:
                st.info("👈 输入文本后点击「开始校对」")

    # ===== AI润色 =====
    with tab2:
        st.markdown('<div style="background:linear-gradient(135deg,#667eea,#764ba2);color:white;padding:16px;border-radius:8px;margin-bottom:16px;"><h3 style="margin:0">✨ AI智能润色</h3><p style="margin:6px 0 0;opacity:0.9">一键优化文字表达，提升文采</p></div>', unsafe_allow_html=True)

        if st.session_state.text:
            st.markdown("**原文：**")
            st.text_area("", st.session_state.text[:600] + ("..." if len(st.session_state.text) > 600 else ""), height=120, disabled=True)

            if st.button("🚀 开始AI润色", type="primary"):
                with st.spinner("AI优化中..."):
                    st.session_state.ai_result = run_ai_optimize(st.session_state.text)

            if st.session_state.ai_result:
                st.markdown("**✨ 润色结果：**")
                st.markdown(f'<div class="ai-box">{st.session_state.ai_result}</div>', unsafe_allow_html=True)

                col1, col2 = st.columns(2)
                with col1:
                    if st.button("📋 使用此结果"):
                        st.session_state.text = st.session_state.ai_result
                        st.session_state.ai_result = ""
                        st.session_state.issues = []
                        st.success("✓ 已替换原文")
                with col2:
                    if st.button("🔄 重新润色"):
                        st.session_state.ai_result = ""
                        st.rerun()
        else:
            st.info("请先在校对页输入文本")

    # ===== 使用说明 =====
    with tab3:
        st.markdown("""
        ### 📖 使用说明

        #### 🎯 核心功能

        **1. 悬浮修改建议**
        - 鼠标移到红色高亮的错误文本上
        - 自动弹出修改建议
        - 直接查看建议内容

        **2. 双向联动定位**
        - 点击原文中的错误 → 右侧结果卡片高亮
        - 点击右侧「定位」按钮 → 原文自动滚动到对应位置

        **3. 一键修正**
        - 点击「一键修正全部」自动应用所有修改
        - 或逐个点击「应用」选择性修改

        #### 📝 操作步骤

        1. 粘贴或输入文本
        2. 点击「开始校对」
        3. 鼠标悬停查看建议，或点击定位
        4. 应用或忽略修改建议

        #### ⚙️ AI润色配置

        在 Settings → Secrets 添加：
        ```
        DASHSCOPE_API_KEY = "你的密钥"
        ```
        """)


if __name__ == "__main__":
    main()
